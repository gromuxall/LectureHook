# LectureHook

LectureHook automates a Chrome browser to navigate to and download all of the lecture captures for a specified course. It is run at the command line and will require an input.

## Installation

**Dependencies**
- Python version 3.4 or later
- Chrome browser

- Chrome WebDriver for your version of Chrome

    + [Download it here](https://chromedriver.chromium.org/downloads)
    + extract and move chromedriver to a permanent location

- Selenium
    
    Install Selenium through the pip package manager
    ```sh
    $ pip install selenium
    ```

## Usage
1. Fill out included config file
    ```sh
    [SITE]
    site = https://uic.blackboard.com

    [LOGIN]
    userid = netid3
    pass = fakepassword23

    [PATHS]
    driver = /home/full/path/to/chromedriver
    dwn1 = /home/full/path/to/course1/lectures/folder
    dwn2 = /home/full/path/to/course2/lectures/folder
    ...
    
    [CODE]
    code1 = CS
    code2 = BIOE
    ...

    [NUM]
    num1 = 341
    num2 = 112
    ...

    [TIME]
    time1 = 
    time2 = 11am
    ...
    ```
2. 
