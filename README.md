<h1>LectureHook<img height="50" align="right" src="https://raw.githubusercontent.com/gromuxall/imagehosting/master/coursehook_badge_1.svg"></h1>

LectureHook is a command-line tool to download lecture videos from the echo360 cloud platform. If you can access your university's lecture videos from echo360.org, you should be able to use this program.

![in_use](https://github.com/gromuxall/imagehosting/raw/master/action.gif)  

# Table of Contents
- [Requirements](#requirements)
- [Installation](#installation)
    - [Linux/MacOS](##linux/macos)
    - [Windows](##windows)
    - [Manual](##manual)
- [Usage](#usage)

# Requirements
- Python3
- Google Chrome browser


# Installation

## Linux/MacOS
Clone the repo and run the provided install script:  
`git clone 'https://github.com/gromuxall/LectureHook.git' && cd LectureHook/app && chmod 755 install.sh && ./install.sh && source ~/.bashrc`  

Now run in your terminal with command:  
`lecturehook`

## Windows
A batch script is in the works, but in the meantime you can install manually with the instructions below

## Manual
The scripts above will automate the installation inside of a python virtual environment, as well as adding an alias for the program so you can just run it with the command `lecturehook`, but you can install it using the global python environment as well (currently the only option for Windows users). Navigate to the /app folder inside the installation and install the dependencies:  
`pip3 install -r requirements.txt`  

Now (while still inside of /app directory) run with:  
`python3 lhook_app.py`

# Usage
LectureHook is interactive via the command line and will fill in the appropriate fields of the configuration file, however, some options can be configured by opening the `config.yaml` file with a text editor and changing some values:

**Download Directory**  
Videos will download to a folder named `\Lectures` in the LectureHook directory by default, but you can enter your own path by replacing the value:  
`download_path: ~\your\chosen\path`

**Multithreading**  
Turn on multithreading for batch downloading:  
`multi: True`

**Headless**  
If you want to see the browser in action for some reason:  
`headless: True`