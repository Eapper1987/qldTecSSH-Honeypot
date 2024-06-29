# qldTecSSH-Honeypot

A sophisticated SSH honeypot simulating a corporate environment to capture malicious activities and interactions.

## Features

### Corporate Filesystem Simulation

- **Realistic Filesystem:** Simulates a corporate environment with multiple departments and realistic files to enhance the authenticity of the honeypot.

### Command and Login Logging

- **Comprehensive Logging:** Logs all command executions and login attempts, allowing detailed analysis of attacker behavior.

- **Log Files:**
- 
  - `cmd_audits.log`: Records all commands executed by the attacker.
  - 
  - `creds_audits.log`: Records all login attempts and credentials used.
  - 
  - `alerts.log`: Records access to sensitive files and execution of bait scripts.

### Tarpit Feature

- **Gradual Response Slowdown:** Gradually slows down responses to trap attackers, making their interactions more time-consuming and frustrating.

### No Password Requirement

- **Easy Access:** No password required for SSH login, making it easy for attackers to gain access while all activities are monitored and logged.

### Fake Malware Simulation

- **Bait Files and Scripts:** Includes fake files and scripts such as `passwords.txt` and `run_me.sh` that, when accessed or executed, simulate malware actions like log deletion, file encryption, and
data exfiltration.
- 
- **Alert Mechanism:** Accessing these bait files triggers alerts and logs the event.

### Raining Characters Effect

- **Visual Disruption:** Implements a "raining characters" effect that mimics terminal corruption, adding to the deception and confusion of the attacker.

## Potential Improvements

There are several areas for potential improvement in this SSH honeypot:

- **Enhanced Shell Command Emulation:** Improve the realism of the emulated shell commands and their responses.
- 
- **Sophisticated Tarpit Mechanism:** Develop a more advanced tarpit system that dynamically adjusts interaction delays.
- 
- **Expanded Filesystem Simulation:** Add more fake files and directories to simulate a larger and more complex corporate environment.
- 

## Installation

git clone https://github.com/your-username/qldTecSSH-Honeypot.git

cd qldTecSSH-Honeypot

pip install -r requirements.txt


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
