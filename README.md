# qldTecSSH-Honeypot

A sophisticated SSH honeypot simulating a corporate environment to capture malicious activities and interactions.

## Features
- Simulates a real corporate filesystem with multiple departments and realistic files.
- Logs all command executions and login attempts.
- Gradually slows down responses to trap attackers.
- No password required for SSH login, making it easy for attackers to gain access while all activities are logged.

## Potential Improvements
There are several areas for potential improvement in this SSH honeypot:
- Enhance the emulated shell commands with more realistic behaviors and responses.
- Implement a more sophisticated tarpit style system to slow down interaction as the session progresses.
- Explore adding additional fake files and directories to simulate a larger and more complex environment.

These enhancements can improve the realism and effectiveness of the honeypot in capturing and analyzing malicious activities.


## Installation:

Prerequisites:
Ensure you have Python 3.x installed on your system. You will also need to install the `paramiko` library if you haven't already:


## REQUIREMENTS:

pip install paramiko


## INSTALLING:

git clone https://github.com/your-username/qldTecSSH-Honeypot.git

cd qldTecSSH-Honeypot


## Usage:

Run the honeypot with the following command:

python main.py -a 0.0.0.0 -p 22 
(You can Change 0.0.0.0 your the ip of your system and bind to any port)

-a 0.0.0.0 specifies the address to bind to (all interfaces).
-p 22 specifies the port to bind to (default SSH port).


## Directory Structure
-------------------
The honeypot creates a realistic corporate filesystem with multiple departments and detailed files. Here are some of the key directories and files:


qldTecSSH-Honeypot
│
├── bin
├── boot
├── dev
├── etc
│   ├── config.txt
│   ├── passwd
│   └── shadow
├── home
│   └── admin
│       ├── Documents
│       │   ├── Projects
│       │   │   └── 2024
│       │   │       └── hidden
│       │   │           └── secret_key.txt
│       │   ├── Reports
│       │   ├── Personal
│       │   └── script.sh
│       ├── Downloads
│       ├── Pictures
│       └── readme.txt
├── lib
├── lib64
├── media
├── mnt
├── opt
├── proc
├── root
├── run
├── sbin
├── srv
├── sys
├── tmp
│   ├── session.log
│   └── tempfile.tmp
├── usr
│   ├── bin
│   ├── local
│   │   ├── bin
│   │   │   └── custom_script.py
│   │   ├── lib
│   │   │   └── custom_library.py
│   │   └── share
│   │       └── readme.md
│   └── sbin
├── var
│   ├── log
│   │   ├── auth.log
│   │   ├── messages
│   │   └── syslog
│   └── www
│       └── html
│           └── index.html
└── Work
    ├── Finance
    │   ├── balance_sheet.xlsx
    │   ├── expense_report.xlsx
    │   └── financial_report.xlsx
    ├── HR
    │   ├── employee_handbook.docx
    │   ├── leave_requests.pdf
    │   ├── payroll.xlsx
    │   └── training_schedule.xlsx
    ├── IT
    │   ├── network_config.txt
    │   ├── server_maintenance_schedule.txt
    │   └── software_inventory.xlsx
    ├── Legal
    │   ├── compliance_report.pdf
    │   ├── contracts.txt
    │   └── privacy_policy.docx
    ├── Engineering
    │   ├── architecture_diagram.png
    │   ├── codebase_overview.txt
    │   ├── project_plan.docx
    │   └── system_design.pdf
    ├── Marketing
    │   ├── advertising_budget.xlsx
    │   ├── campaign_results.xlsx
    │   ├── marketing_strategy.pdf
    │   └── social_media_plan.docx
    ├── Operations
    │   ├── inventory_list.csv
    │   ├── maintenance_schedule.xlsx
    │   ├── operations_manual.pdf
    │   └── safety_procedures.txt
    └── Sales
        ├── client_list.csv
        ├── meeting_schedule.txt
        ├── sales_forecast.xlsx
        └── sales_presentation.pptx
        
## Logging:

The honeypot logs all command executions and login attempts:

Command Executions: Logged in cmd_audits.log.
Login Attempts: Logged in creds_audits.log.
Alerts: Logged in alerts.log.

## Contributing:

Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License:

This project is licensed under the MIT License - see the LICENSE file for details.
