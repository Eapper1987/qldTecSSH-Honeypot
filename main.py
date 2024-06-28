import os
import logging
import paramiko
import threading
import socket
import argparse
import time
from logging.handlers import RotatingFileHandler

# Constants
SSH_BANNER = "SSH-2.0-qldTecServices_1.0"
FAKE_ROOT = "/tmp/fake_qld_tec_services"
USER_HOME = os.path.join(FAKE_ROOT, "home", "admin")
INITIAL_DELAY = 0.5
DELAY_INCREMENT = 0.1
MAX_DELAY = 5.0

# Logging Format
logging_format = logging.Formatter('%(asctime)s %(message)s')

# Funnel Logger
funnel_logger = logging.getLogger('FunnelLogger')
funnel_logger.setLevel(logging.INFO)
funnel_handler = RotatingFileHandler('cmd_audits.log', maxBytes=2000, backupCount=5)
funnel_handler.setFormatter(logging_format)
funnel_logger.addHandler(funnel_handler)

# Credentials Logger
creds_logger = logging.getLogger('CredsLogger')
creds_logger.setLevel(logging.INFO)
creds_handler = RotatingFileHandler('creds_audits.log', maxBytes=2000, backupCount=5)
creds_handler.setFormatter(logging_format)
creds_logger.addHandler(creds_handler)

# Alert Logger
alert_logger = logging.getLogger('AlertLogger')
alert_logger.setLevel(logging.WARNING)
alert_handler = RotatingFileHandler('alerts.log', maxBytes=2000, backupCount=5)
alert_handler.setFormatter(logging_format)
alert_logger.addHandler(alert_handler)

# Generate RSA host key (if not already generated)
host_key_path = 'host_key_rsa'
if not os.path.exists(host_key_path):
    host_key = paramiko.RSAKey.generate(2048)
    host_key.write_private_key_file(host_key_path)
else:
    host_key = paramiko.RSAKey(filename=host_key_path)

# SSH Server Class
class Server(paramiko.ServerInterface):

    def __init__(self, client_ip):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.current_directory = FAKE_ROOT  # Start at the fake root directory initially
        self.delay = INITIAL_DELAY

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
    
    def get_allowed_auths(self, username):
        return "password"

    def check_auth_password(self, username, password):
        funnel_logger.info(f'Client {self.client_ip} attempted connection with username: {username}, password: {password}')
        creds_logger.info(f'{self.client_ip}, {username}, {password}')
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        command = str(command)
        funnel_logger.info(f'Command execution requested: {command} by {self.client_ip}')
        return True

def emulated_shell(channel, client_ip, server_instance):
    prompt = b"admin@qldTecServices:~# "
    channel.send(prompt)
    command = b""
    while True:
        char = channel.recv(1)
        if not char:
            channel.close()
            return

        if char == b'\x08' or char == b'\x7f':  # Handle backspace
            if len(command) > 0:
                command = command[:-1]
                channel.send(b'\b \b')  # Erase character on terminal
            continue
        elif char == b'\r':
            channel.send(b'\r\n')
            command_str = command.strip().decode()
            funnel_logger.info(f'{client_ip} executed command: {command_str}')
            process_command(command_str, channel, client_ip, server_instance)
            command = b""
            channel.send(prompt)
        else:
            command += char
            channel.send(char)

def process_command(command, channel, client_ip, server_instance):
    response = b""
    time.sleep(server_instance.delay)
    server_instance.delay = min(server_instance.delay + DELAY_INCREMENT, MAX_DELAY)

    if command == 'exit':
        response = b"\n Goodbye!\n"
        funnel_logger.info(f'{client_ip} executed command: exit')
        channel.send(response)
        funnel_logger.info(f'{client_ip} exited the shell')
        channel.close()
    elif command == 'pwd':
        response = b"\n" + bytes(server_instance.current_directory[len(FAKE_ROOT):], 'utf-8') + b"\r\n"
    elif command == 'whoami':
        response = b"\nadmin\r\n"
    elif command == 'ls':
        try:
            files = os.listdir(server_instance.current_directory)
            files_str = b" ".join([bytes(f, 'utf-8') for f in files])
            response = b"\n" + files_str + b"\r\n"
        except FileNotFoundError:
            response = b"\nDirectory not found\r\n"
    elif command.startswith('cd '):
        new_dir = command[3:]
        if new_dir == "/":
            server_instance.current_directory = FAKE_ROOT
            response = b"\n"
        elif new_dir == "":
            server_instance.current_directory = USER_HOME
            response = b"\n"
        elif new_dir == "..":
            if server_instance.current_directory != FAKE_ROOT:
                server_instance.current_directory = os.path.dirname(server_instance.current_directory)
            response = b"\n"
        else:
            new_path = os.path.join(server_instance.current_directory, new_dir)
            if os.path.exists(new_path) and os.path.isdir(new_path):
                server_instance.current_directory = new_path
                response = b"\n"
            else:
                response = b"\nDirectory not found\r\n"
    elif command.startswith('cat '):
        file_path = os.path.join(server_instance.current_directory, command[4:])
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
                response = b"\n" + file_content + b"\r\n"
        except FileNotFoundError:
            response = b"\nFile not found\r\n"
        except IsADirectoryError:
            response = b"\nIs a directory\r\n"
    elif command.startswith('mkdir '):
        try:
            dir_name = command[6:]
            new_dir_path = os.path.join(server_instance.current_directory, dir_name)
            os.makedirs(new_dir_path, exist_ok=True)
            response = b"\n"
        except Exception as e:
            response = f"\nFailed to create directory: {e}\r\n".encode('utf-8')
    elif command.startswith('touch '):
        try:
            file_name = command[6:]
            file_path = os.path.join(server_instance.current_directory, file_name)
            open(file_path, 'a').close()
            response = b"\n"
        except Exception as e:
            response = f"\nFailed to create file: {e}\r\n".encode('utf-8')
    elif command.startswith('rm '):
        try:
            file_name = command[3:]
            file_path = os.path.join(server_instance.current_directory, file_name)
            os.remove(file_path)
            response = b"\n"
        except Exception as e:
            response = f"\nFailed to remove file: {e}\r\n".encode('utf-8')
    elif command.startswith('echo '):
        try:
            parts = command.split('>')
            if len(parts) == 2:
                content, file_name = parts[0].strip(), parts[1].strip()
                file_path = os.path.join(server_instance.current_directory, file_name)
                with open(file_path, 'w') as f:
                    f.write(content)
                response = b"\n"
            else:
                response = b"\nInvalid echo command\r\n"
        except Exception as e:
            response = f"\nFailed to write to file: {e}\r\n".encode('utf-8')
    elif command.startswith('cp '):
        try:
            parts = command[3:].split(' ')
            if len(parts) == 2:
                src, dest = parts[0], parts[1]
                src_path = os.path.join(server_instance.current_directory, src)
                dest_path = os.path.join(server_instance.current_directory, dest)
                with open(src_path, 'rb') as f_src:
                    with open(dest_path, 'wb') as f_dest:
                        f_dest.write(f_src.read())
                response = b"\n"
            else:
                response = b"\nInvalid cp command\r\n"
        except Exception as e:
            response = f"\nFailed to copy file: {e}\r\n".encode('utf-8')
    elif command.startswith('mv '):
        try:
            parts = command[3:].split(' ')
            if len(parts) == 2:
                src, dest = parts[0], parts[1]
                src_path = os.path.join(server_instance.current_directory, src)
                dest_path = os.path.join(server_instance.current_directory, dest)
                os.rename(src_path, dest_path)
                response = b"\n"
            else:
                response = b"\nInvalid mv command\r\n"
        except Exception as e:
            response = f"\nFailed to move file: {e}\r\n".encode('utf-8')
    else:
        response = b"\n" + command.encode('utf-8') + b": command not found\r\n"

    funnel_logger.info(f'{client_ip} executed command: {command}, response: {response.strip().decode()}')
    channel.send(response)

def client_handle(client, addr, server_instance):
    client_ip = addr[0]
    print(f"{client_ip} connected to server.")
    try:
        transport = paramiko.Transport(client)
        transport.local_version = SSH_BANNER
        server = Server(client_ip=client_ip)
        transport.add_server_key(host_key)
        transport.start_server(server=server)
        channel = transport.accept(100)

        if channel is None:
            print("No channel was opened.")
            return

        try:
            channel.send("Welcome to qldTecServices 2024!\r\n\r\n")
            emulated_shell(channel, client_ip=client_ip, server_instance=server)

        except Exception as error:
            print(error)
    except Exception as error:
        print(error)
        print("!!! Exception !!!")
    
    finally:
        try:
            transport.close()
        except Exception:
            pass
        
        client.close()
    
def honeypot(address, port):
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.bind((address, port))
    socks.listen(100)
    print(f"Server is listening on port {port}.")

    while True: 
        try:
            client, addr = socks.accept()
            threading.Thread(target=client_handle, args=(client, addr, None)).start()
        except Exception as error:
            print("!!! Exception - Could not open new client connection !!!")
            print(error)

def create_qld_tec_services_fs():
    # Define directories relative to the fake root
    directories = [
        os.path.join(FAKE_ROOT, "bin"),
        os.path.join(FAKE_ROOT, "boot"),
        os.path.join(FAKE_ROOT, "dev"),
        os.path.join(FAKE_ROOT, "etc"),
        os.path.join(FAKE_ROOT, "home", "admin"),
        os.path.join(FAKE_ROOT, "lib"),
        os.path.join(FAKE_ROOT, "lib64"),
        os.path.join(FAKE_ROOT, "media"),
        os.path.join(FAKE_ROOT, "mnt"),
        os.path.join(FAKE_ROOT, "opt"),
        os.path.join(FAKE_ROOT, "proc"),
        os.path.join(FAKE_ROOT, "root"),
        os.path.join(FAKE_ROOT, "run"),
        os.path.join(FAKE_ROOT, "sbin"),
        os.path.join(FAKE_ROOT, "srv"),
        os.path.join(FAKE_ROOT, "sys"),
        os.path.join(FAKE_ROOT, "tmp"),
        os.path.join(FAKE_ROOT, "usr"),
        os.path.join(FAKE_ROOT, "usr", "share"),
        os.path.join(FAKE_ROOT, "usr", "share", "doc"),
        os.path.join(FAKE_ROOT, "var"),
        os.path.join(FAKE_ROOT, "home", "admin", "Documents"),
        os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Projects"),
        os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Projects", "2024"),
        os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Projects", "2024", "hidden"),
        os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Reports"),
        os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Personal"),
        os.path.join(FAKE_ROOT, "home", "admin", "Downloads"),
        os.path.join(FAKE_ROOT, "home", "admin", "Pictures"),
        os.path.join(FAKE_ROOT, "var", "log"),
        os.path.join(FAKE_ROOT, "var", "www", "html"),
        os.path.join(FAKE_ROOT, "usr", "local", "bin"),
        os.path.join(FAKE_ROOT, "usr", "local", "lib"),
        os.path.join(FAKE_ROOT, "usr", "local", "share"),
        os.path.join(FAKE_ROOT, "usr", "bin"),
        os.path.join(FAKE_ROOT, "usr", "sbin"),
        os.path.join(FAKE_ROOT, "home", "admin", "Work", "Finance"),
        os.path.join(FAKE_ROOT, "home", "admin", "Work", "HR"),
        os.path.join(FAKE_ROOT, "home", "admin", "Work", "Engineering"),
        os.path.join(FAKE_ROOT, "home", "admin", "Work", "Marketing"),
        os.path.join(FAKE_ROOT, "home", "admin", "Work", "IT"),
        os.path.join(FAKE_ROOT, "home", "admin", "Work", "Legal"),
        os.path.join(FAKE_ROOT, "home", "admin", "Work", "Operations"),
        os.path.join(FAKE_ROOT, "home", "admin", "Work", "Sales"),
    ]

    # Create directories in the fake root directory
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Create realistic files in writable directories
    with open(os.path.join(FAKE_ROOT, "etc", "config.txt"), "w") as f:
        f.write("network_interface=eth0\nip_address=192.168.1.1\nnetmask=255.255.255.0\ngateway=192.168.1.254\ndns1=8.8.8.8\ndns2=8.8.4.4\n")

    with open(os.path.join(FAKE_ROOT, "etc", "passwd"), "w") as f:
        f.write("root:x:0:0:root:/root:/bin/bash\nadmin:x:1000:1000:admin,,,:/home/admin:/bin/bash\n")

    with open(os.path.join(FAKE_ROOT, "etc", "shadow"), "w") as f:
        f.write("root:$6$saltsalt$hashedpassword:18030:0:99999:7:::\nadmin:$6$saltsalt$hashedpassword:18030:0:99999:7:::\n")

    with open(os.path.join(FAKE_ROOT, "etc", "hosts"), "w") as f:
        f.write("127.0.0.1   localhost\n127.0.1.1   qldTecServices\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "readme.txt"), "w") as f:
        f.write("Welcome to the admin home directory!\nThis directory contains various documents and projects.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Documents", "project.txt"), "w") as f:
        f.write("Project Plan:\n- Task 1: Research\n- Task 2: Development\n- Task 3: Testing\n- Task 4: Deployment\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Documents", "budget.xlsx"), "w") as f:
        f.write("Year,Budget,Spent,Remaining\n2024,100000,50000,50000\n2025,120000,30000,90000\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Documents", "meeting_notes.txt"), "w") as f:
        f.write("Meeting Notes:\n- Discussed project timeline\n- Reviewed budget allocation\n- Assigned tasks to team members\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Documents", "script.sh"), "w") as f:
        f.write("#!/bin/bash\n\necho 'This is a sample script'\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Projects", "2024", "hidden", "secret_key.txt"), "w") as f:
        f.write("This is the secret key.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Reports", "annual_report.pdf"), "wb") as f:
        f.write(b"%PDF-1.4\n%This is a dummy annual report.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Reports", "q1_report.pdf"), "wb") as f:
        f.write(b"%PDF-1.4\n%This is a dummy Q1 report.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Personal", "diary.txt"), "w") as f:
        f.write("This is a personal diary entry.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Documents", "Personal", "todo.txt"), "w") as f:
        f.write("TODO:\n- Buy groceries\n- Finish project\n- Call mom\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Downloads", "setup.exe"), "wb") as f:
        f.write(b"This is a dummy executable file.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Downloads", "report.pdf"), "wb") as f:
        f.write(b"%PDF-1.4\n%This is a dummy PDF report file.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Downloads", "data.csv"), "w") as f:
        f.write("id,name,value\n1,Alice,10\n2,Bob,20\n3,Charlie,30\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Pictures", "image.jpg"), "wb") as f:
        f.write(b"This is a dummy image file.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Pictures", "diagram.png"), "wb") as f:
        f.write(b"This is a dummy diagram file.\n")

    with open(os.path.join(FAKE_ROOT, "tmp", "session.log"), "w") as f:
        f.write("Session started at 2024-06-01 12:00:00\nSession ended at 2024-06-01 14:00:00\n")

    with open(os.path.join(FAKE_ROOT, "tmp", "tempfile.tmp"), "w") as f):
        f.write("This is a temporary file.\n")

    with open(os.path.join(FAKE_ROOT, "var", "log", "syslog"), "w") as f):
        f.write("Jun 10 06:25:01 qldTecServices CRON[1298]: (root) CMD (cd / && run-parts --report /etc/cron.hourly)\n")

    with open(os.path.join(FAKE_ROOT, "var", "log", "auth.log"), "w") as f):
        f.write("Jun 10 06:25:01 qldTecServices sshd[1298]: Accepted password for admin from 192.168.1.100 port 22 ssh2\n")

    with open(os.path.join(FAKE_ROOT, "var", "log", "messages"), "w") as f):
        f.write("Jun 10 06:25:01 qldTecServices systemd[1]: Started Session 1 of user admin.\n")

    with open(os.path.join(FAKE_ROOT, "var", "www", "html", "index.html"), "w") as f):
        f.write("<html><body><h1>Welcome to QLD Tech Services</h1></body></html>\n")

    with open(os.path.join(FAKE_ROOT, "usr", "local", "bin", "custom_script.py"), "w") as f):
        f.write("#!/usr/bin/env python3\n\nprint('This is a custom script')\n")

    with open(os.path.join(FAKE_ROOT, "usr", "local", "lib", "custom_library.py"), "w") as f):
        f.write("# Custom library for QLD Tech Services\n\ndef custom_function():\n    print('This is a custom function')\n")

    with open(os.path.join(FAKE_ROOT, "usr", "local", "share", "readme.md"), "w") as f):
        f.write("# QLD Tech Services\n\nThis is the shared directory for QLD Tech Services.\n")

    with open(os.path.join(FAKE_ROOT, "usr", "bin", "example_bin"), "w") as f):
        f.write("#!/bin/bash\n\necho 'This is an example binary file'\n")

    with open(os.path.join(FAKE_ROOT, "usr", "sbin", "example_sbin"), "w") as f):
        f.write("#!/bin/bash\n\necho 'This is an example sbin file'\n")

    with open(os.path.join(FAKE_ROOT, "usr", "share", "doc", "example.txt"), "w") as f):
        f.write("This is an example documentation file.\n")

    # Finance Department Files
    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Finance", "financial_report.xlsx"), "w") as f):
        f.write("Quarter,Revenue,Expenses,Profit\nQ1,50000,30000,20000\nQ2,60000,35000,25000\nQ3,70000,40000,30000\nQ4,80000,45000,35000\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Finance", "tax_documents.pdf"), "wb") as f):
        f.write(b"%PDF-1.4\n%This is a dummy tax document.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Finance", "balance_sheet.xlsx"), "w") as f):
        f.write("Assets,Liabilities,Equity\n100000,50000,50000\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Finance", "expense_report.xlsx"), "w") as f):
        f.write("Date,Category,Amount\n2024-01-01,Office Supplies,500\n2024-02-15,Travel,1200\n")

    # HR Department Files
    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "HR", "employee_handbook.docx"), "w") as f):
        f.write("This is a dummy employee handbook.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "HR", "payroll.xlsx"), "w") as f):
        f.write("EmployeeID,Name,Department,Salary\n1,John Doe,Engineering,50000\n2,Jane Smith,Marketing,55000\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "HR", "training_schedule.xlsx"), "w") as f):
        f.write("Date,Topic,Trainer\n2024-01-10,Orientation,HR Team\n2024-02-20,Software Development,IT Team\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "HR", "leave_requests.pdf"), "wb") as f):
        f.write(b"%PDF-1.4\n%This is a dummy leave request document.\n")

    # Engineering Department Files
    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Engineering", "system_design.pdf"), "wb") as f):
        f.write(b"%PDF-1.4\n%This is a dummy system design document.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Engineering", "project_plan.docx"), "w") as f):
        f.write("This is a dummy project plan.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Engineering", "architecture_diagram.png"), "wb") as f):
        f.write(b"This is a dummy architecture diagram file.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Engineering", "codebase_overview.txt"), "w") as f):
        f.write("This document provides an overview of the codebase.\n")

    # Marketing Department Files
    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Marketing", "marketing_strategy.pdf"), "wb") as f):
        f.write(b"%PDF-1.4\n%This is a dummy marketing strategy document.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Marketing", "campaign_results.xlsx"), "w") as f):
        f.write("Campaign,Impressions,Clicks,Conversions\nSpring Sale,10000,500,50\nSummer Sale,15000,700,70\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Marketing", "social_media_plan.docx"), "w") as f):
        f.write("This is a dummy social media plan.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Marketing", "advertising_budget.xlsx"), "w") as f):
        f.write("Platform,Budget,Spent\nGoogle Ads,10000,8000\nFacebook Ads,5000,4000\n")

    # IT Department Files
    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "IT", "network_config.txt"), "w") as f):
        f.write("Interface: eth0\nIP: 192.168.1.100\nNetmask: 255.255.255.0\nGateway: 192.168.1.1\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "IT", "server_maintenance_schedule.txt"), "w") as f):
        f.write("Date: 2024-06-01\nTask: Update server software\nDate: 2024-06-15\nTask: Backup server data\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "IT", "software_inventory.xlsx"), "w") as f):
        f.write("Software,Version,License\nApache,2.4,Open Source\nMySQL,8.0,Open Source\nPython,3.9,Open Source\n")

    # Legal Department Files
    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Legal", "contracts.txt"), "w") as f):
        f.write("Contract 1: NDA Agreement\nContract 2: Employment Agreement\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Legal", "compliance_report.pdf"), "wb") as f):
        f.write(b"%PDF-1.4\n%This is a dummy compliance report.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Legal", "privacy_policy.docx"), "w") as f):
        f.write("This is a dummy privacy policy document.\n")

    # Operations Department Files
    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Operations", "operations_manual.pdf"), "wb") as f):
        f.write(b"%PDF-1.4\n%This is a dummy operations manual.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Operations", "maintenance_schedule.xlsx"), "w") as f):
        f.write("Date,Task,Status\n2024-06-01,Check HVAC,Completed\n2024-06-10,Inspect fire extinguishers,Pending\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Operations", "safety_procedures.txt"), "w") as f):
        f.write("Safety Procedures:\n- Wear protective gear\n- Follow safety signs\n- Report accidents immediately\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Operations", "inventory_list.csv"), "w") as f):
        f.write("Item,Quantity,Location\nPrinter Paper,500,Storage Room\nLaptops,20,Office\nProjectors,5,Conference Room\n")

    # Sales Department Files
    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Sales", "sales_forecast.xlsx"), "w") as f):
        f.write("Month,Projected Sales,Actual Sales\nJanuary,50000,45000\nFebruary,60000,55000\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Sales", "client_list.csv"), "w") as f):
        f.write("Client Name,Contact,Revenue\nABC Corp,John Doe,10000\nXYZ Inc,Jane Smith,20000\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Sales", "sales_presentation.pptx"), "wb") as f):
        f.write(b"This is a dummy sales presentation.\n")

    with open(os.path.join(FAKE_ROOT, "home", "admin", "Work", "Sales", "meeting_schedule.txt"), "w") as f):
        f.write("Meeting Schedule:\n- Monday: Sales Team Meeting\n- Wednesday: Client Call\n- Friday: Weekly Review\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser() 
    parser.add_argument('-a', '--address', type=str, required=True)
    parser.add_argument('-p', '--port', type=int, required=True)
    args = parser.parse_args()
    
    create_qld_tec_services_fs()  # Create the QLD Tec Services-like filesystem structure
    honeypot(args.address, args.port)
