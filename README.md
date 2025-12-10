# LinuxTerminalHelper
A simple AI assistant to help with Gnu/Linux terminal commands. written in python and based on Gemini 2.5-Flash.

Created as a coursework project during my IT engineering studies.

# Overview
LinuxTerminalHelper is a Python tool that assists with generating and understanding GNU/Linux terminal commands.

When installed correctly, you can run it simply by typing:
```bash
helper [your prompt]
```

You can set it up automatically using the included setup tool, or manually using the instructions below.

# Features
Simple helper command you can run from any terminal. The program is aware of your distribution and kernel version and has access to your installed packages (dpkg, pacman, rpm).
It can also read your journalctl and manpages.
The program will not execute any other terminal commands for safety reasons.

# Installation
> [!NOTE]
> If you move the project directory, you must update the alias.
> The setup tool can automatically fix this for you.

### Option 1: Automatic Installation (Recommended)

Open a terminal inside this project folder.

Run:
```bash
python setup-tool.py
```

This will configure everything and create the helper command for you.

**You will need to paste your own Google Gemini API key to the setup tool, which you can obtain from:** 

[https://aistudio.google.com/app/api-keys](https://aistudio.google.com/app/api-keys)

> [!NOTE]
> The setup tool cannot detect or fix an incorrect Gemini API key.
> You will have to fix it manually in your ~/.bashrc

### Option 2: Manual Installation

Add an alias to your ~/.bashrc (edit paths to match your setup):
```bash
alias helper='/path/to/linux-terminal-helper/venv/bin/python /path/to/linux-terminal-helper/linux-term-help.py'
```

Add your Gemini API key to your ~/.bashrc:
```bash
export GEMINI_API_KEY=[your key without brackets]
```

Load your updated bash configuration:
```bash
source ~/.bashrc
```

# Project Structure Notes
Keep all files inside the linux-terminal-helper directory.
If the folder is moved, the command will no longer work unless reconfigured.

# License
Distributed under GPL-3.0 License

# Contact
Project link: [https://github.com/Ramukka/AILinuxTerminalHelper](https://github.com/Ramukka/AILinuxTerminalHelper)
