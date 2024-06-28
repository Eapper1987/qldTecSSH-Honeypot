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

(You can Change 0.0.0.0 to the ip of your system and bind to any port number)

-a 0.0.0.0 specifies the address to bind to (all interfaces).
-p 22 specifies the port to bind to (default SSH port).


## Directory Structure
-------------------
The honeypot creates a realistic corporate filesystem with multiple departments and detailed files. Here are some of the key directories and files:

        
## Logging:

The honeypot logs all command executions and login attempts:

Command Executions: Logged in cmd_audits.log.
Login Attempts: Logged in creds_audits.log.
Alerts: Logged in alerts.log.

## Monitoring and Security:

Monitor the honeypot logs regularly for any suspicious activity. Since running a honeypot involves risks of unauthorized access attempts, consider firewall rules and other security measures to limit exposure.

## Cloud Provider Considerations:

If using Linode or another cloud provider, review their security recommendations and ensure you configure firewall rules and access controls appropriately to mitigate risks.

## Contributing:

Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License:

This project is licensed under the MIT License - see the LICENSE file for details.
