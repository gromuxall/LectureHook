#!/usr/bin/env python3
"""
    LectureHook

    Steven Madonna
    smadon3@uic.edu

    TODO:
        - make all downloads headless
        - make prompt to fill config file
"""
import configparser
import sys
import time
import os
import os.path
import glob
import calendar as cal
import argparse
import functools
import logging
from simple_term_menu import TerminalMenu
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def slow_down(func):
    '''
    Sleep 1 second before calling the function
    '''
    @functools.wraps(func)
    def wrapper_slow_down(*args, **kwargs):
        while len([i for i in glob.glob('*.crdownload')]) > 2:
            print('Max downloading three vids at once')
            time.sleep(5)
        return func(*args, **kwargs)
    return wrapper_slow_down


class ElementNotFound(Exception):
    """
    Exception raised for error in finding element
    """

    def __init__(self, element, message="Element not found"):
        self.element = element
        self.message = message
        super().__init__(self.message)


class Course:
    '''
    Contains all info and methods for courses
    scraped from Echo360
    '''
    # <Course> ------------------------------------------------------------- //
    def __init__(self, course):
        items = course.text.split('\n')
        self.num_vids = items[0]
        semester = items[1].split()
        self.term = semester[0]
        self.year = semester[1]
        self.crn = items[2]
        split_title = items[3].split(' - ')
        self.title = split_title[1]
        code_num = split_title[0].split()
        self.crs_code = code_num[0]
        self.crs_num = code_num[1]

    # <Course> ------------------------------------------------------------- //
    def __str__(self):
        return self.crs_code + ' ' + self.crs_num + ' - ' + self.title

    # <Course> ------------------------------------------------------------- //
    def term_enum(self):
        """
        Return numerical representation of semester
        order for ease of sorting
        """
        if self.term == 'Spring':
            return 1
        if self.term == 'Summer':
            return 2
        return 3

    # <Course> ------------------------------------------------------------- //
    def goto_course(self):
        """
        Re-find element (to prevent stale element reference) and select
        """
        javascript = "document.querySelectorAll(\"a[aria-label*=\'" + self.crn + "\']\")[0].click()"
        DRIVER.execute_script(javascript)
        time.sleep(2)
        self.get_lectures()

    # <Course> ------------------------------------------------------------- //
    def get_lectures(self):
        """
        Get lecture elements
        """
        #os.chdir('/home/smadonna/Downloads')
        lectures = []
        name = self.crs_code + ' ' + self.crs_num + ' - ' + self.title

        # wait for elements to appear
        WebDriverWait(DRIVER, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='class-row']")))

        rows = DRIVER.find_elements_by_xpath("//div[contains(@class, 'class-row')]")
        for idx, row in enumerate(rows):
            course = self.crs_code + self.crs_num
            title = row.find_element_by_class_name('header').text
            date = row.find_element_by_xpath(".//span[@class='date']").text
            index = idx
            lectures.append(Video(course, title, date, index))

        vid_names = [v.date for v in lectures]
        vid_names.insert(0, 'all videos')
        terminal_menu = TerminalMenu(menu_entries=vid_names, title=name)
        choice = terminal_menu.show()

        for vid in lectures:
            vid.download()
            print('Downloading lecture {} from {}'.format(vid.index, vid.date))

    # <Course> ------------------------------------------------------------- //
    def menu_line(self):
        """
        Provides a pretty formatted string for the menu
        """
        title_str = self.crs_code + ' ' + self.crs_num + ' - ' + self.title
        return title_str.ljust(42) + (self.crn).ljust(20)


class Video:
    """
    Object representing a class-row of a lecture for a given course
    """
    # <Video> -------------------------------------------------------------- //
    def __init__(self, course, title, date, index):
        self.course = course
        self.title = title
        self.date = date
        self.index = index

        # make map from month name to number
        cal_num = {name: num for num, name in enumerate(cal.month_name) if num}

    
    # <Video> -------------------------------------------------------------- //
    def button(self):
        media_capture = DRIVER.find_elements_by_xpath(
            "//*[contains(@class, 'courseMediaIndicator capture')]")
        
        return media_capture[self.index]

    # <Video> -------------------------------------------------------------- //
    @slow_down
    def download(self):
        """
        Clicks and selects quality, then downloading video
        """
        self.button().click()
        time.sleep(1)

        WebDriverWait(DRIVER, 30).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'Download original')]")
            )
        )
        time.sleep(1)

        DRIVER.find_element_by_xpath(
            "//*[contains(text(), 'Download original')]"
        ).click()

        WebDriverWait(DRIVER, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//select[@name='video-one-files']")
            )
        )

        # select HD version TODO: give choice for sd or hd
        #                   TODO: have this select be the webdriverwait above
        select = Select(DRIVER.find_element_by_xpath(
            "//select[@name='video-one-files']"
        ))
        select.select_by_index(1)

        btn = DRIVER.find_element_by_xpath(
            "//a[@class='btn primary medium downloadBtn']"
        )

        DRIVER.find_element_by_xpath(
            "//a[@class='btn primary medium downloadBtn']"
        ).click()
        


        time.sleep(2)
        add_download(self)
        LOGGER.info('Downloading video {}: {}'.format(self.index, self.date))



# -------------------------------------------------------------------------- //
def launch_page_echo():
    """
    Navigates to Echo360 site

    TODO:
        - check config file for values and prompt if no values
        - change hardcoded values to config file
    """
    DRIVER.get('https://echo360.org/courses')
    email_input = WebDriverWait(DRIVER, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name='email']"))
    )
    email_input.send_keys(CONFIG['LOGIN']['email'])
    email_input.submit()

    DRIVER.find_element_by_xpath("//input[@id='UserID']").send_keys(CONFIG['LOGIN']['userid'])
    password = DRIVER.find_element_by_xpath("//input[@id='password']")
    password.send_keys(CONFIG['LOGIN']['pass'])
    password.submit()
    print(MESSAGES['sign_in'])



# -------------------------------------------------------------------------- //
def add_download(vid):
    '''
    Because files may finish downloading out of order, this will
    search for a currently downloading file and append to the
    download list before another starts downloading
    '''
    curr_dwns = [i for i in glob.glob('*.crdownload')]

    for fname in curr_dwns:
        fname = fname.split('.crdownload')[0]
        if fname not in DOWNLOADS:
            DOWNLOADS[fname] = vid
            LOGGER.info('Added k:{} -> v:{}'.format(fname, vid))


# -------------------------------------------------------------------------- //
def cleanup_files():
    '''
    Deletes any unfinished .crdownloads
    '''
    curr_dwns = [i for i in glob.glob('*.crdownload')]

    for fname in curr_dwns:
        fname = fname.split('.crdownload')[0]
        if fname in DOWNLOADS:
            os.remove(fname + '.crdownload')
            LOGGER.info('Deleted unfinished file: {}.crdownload'.format(fname))

# -------------------------------------------------------------------------- //
def switch_to_frame():
    """
    Switches frames. Annoying.
    """
    iframe = WebDriverWait(DRIVER, 30).until(
        EC.presence_of_element_located((By.XPATH,\
                "//iframe[@class='classic-learn-iframe']"))
        )
    DRIVER.switch_to.frame(iframe)


# -------------------------------------------------------------------------- //
def get_courses():
    """
    Get list of courses
    """
    WebDriverWait(DRIVER, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[@role='gridcell']"))
    )
    containers = DRIVER.find_elements_by_xpath(("//span[@role='gridcell']"))

    for crs in containers:
        COURSES.append(Course(crs))




# -------------------------------------------------------------------------- //
def print_menu():
    """
    Sort and print course list, then return choice
    """
    global COURSES
    COURSES = sorted(COURSES, key=lambda x: x.crs_num)
    crs_names = [z.menu_line() for z in COURSES]

    #cookies = DRIVER.get_cookies()
    #for c in cookies:
    #    print(c)
    
    terminal_menu = TerminalMenu(crs_names)
    choice = terminal_menu.show()

    #print('\n{}\n'.format(COURSES[choice]))
    COURSES[choice].goto_course()



# -------------------------------------------------------------------------- //
def check_flags():
    """
    Checks optional flags against zero or both being set
    """
    if ARGS.echo360 and ARGS.collab:
        print('ERROR: Only one flag allowed')
        PARSER.print_help()
        sys.exit()
    if not ARGS.echo360 and not ARGS.collab:
        print('ERROR: One flag needed')
        PARSER.print_help()
        sys.exit()


# -------------------------------------------------------------------------- //
def main():
    """
    Main program
    """
    print('   __     __  __                               ')
    print('  / /    / /_/ /    LectureHook                ')
    print(' / /__  / __  /     ░░▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓    ')
    print('/____/ /_/ /_/      Part of the Hook® Suite    ')
    print('\n───────────────────────────────────────────\n')

    if ARGS.echo360:
        print(MESSAGES['echo'])
        launch_page_echo()
        get_courses()
        print_menu()
    elif ARGS.collab:
        print(MESSAGES['collab'])
        #launch_page_collab()
        #choose_course()
        #get_to_captures()
        #get_courses_collab
        #print_courses_collab


# -------------------------------------------------------------------------- //
if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description='Download lectures from Echo360 or Blackboard Collaborate.',
        usage='python new_lecturehook.py [-e] [-c]')
    PARSER.add_argument('-e', '--echo360', action='store_true', help='use this\
            flag if videos you want to download are hosted with Echo360')
    PARSER.add_argument('-c', '--collab', action='store_true', help='use this\
            flag if videos you want to download are hosted with Blackboard Collaborate')
    ARGS = PARSER.parse_args()

    check_flags()

    # setup the logger
    LOGGER = logging.getLogger('lhook_logger')
    #logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # read preliminary info from config file
    # TODO autogenerate config file
        # if config file doesn't exist, create one and prompt for input
    CONFIG = configparser.ConfigParser()
    CONFIG.read('courses.ini')

    # set browser options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    prefs = {'prompt_for_download': False}
    options.add_experimental_option('prefs', prefs)
    DRIVER = webdriver.Chrome(CONFIG['PATHS']['driver'], options=options)

    # global structs for ease of access
    COURSES = []
    DOWNLOADS = {}

    # msg dictionary for laziness
    MESSAGES = {
        'sign_in': 'Signing in...',
        'collab': 'Fetching videos from Blackboard Collaborate',
        'echo': 'Fetching videos from Echo360',
        }

    # begin program
    try:
        main()
    #except:
    #    print('Exiting')
    finally:
        print('Cleaning up unfinished files')
        DRIVER.quit()
        # TODO: reactivate this
        #cleanup_files()








"""
# -------------------------------------------------------------------------- //
def launch_page_collab():
    # Initial get of origin page
    DRIVER.get('https://uic.blackboard.com')
    DRIVER.maximize_window()

    # Click 'Sign In'
    DRIVER.find_element_by_xpath("//a[@class='btn btn-primary text-center signIn']").click()

    # Enter credentials
    DRIVER.find_element_by_id('UserID').send_keys(CONFIG['LOGIN']['userid'])
    DRIVER.find_element_by_id('password').send_keys(CONFIG['LOGIN']['pass'])
    DRIVER.find_element_by_xpath("//button[@type='submit']").click()
    print(MESSAGES['sign_in'])

    # Click 'My Courses', attempt ten times
    tries = 0
    while tries < 10:
        try:
            my_courses = WebDriverWait(DRIVER, 30).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "My Courses"))
            )
            my_courses.click()
            break
        except:
            tries = tries + 1
            time.sleep(1)


# -------------------------------------------------------------------------- //
def choose_course():
    #time.sleep(10)
    WebDriverWait(DRIVER, 30).until(
        EC.element_to_be_clickable((By.XPATH,\
            "//div[contains(@id, 'course-list')]"))
        )

    courses = DRIVER.find_elements_by_xpath(\
        "//a[@analytics-id='base.courses.courseCard.courseLink.link']"
        )

    # print list of courses
    for idx, crs in enumerate(courses, 1):
        print(idx, ') ', crs.find_element_by_xpath("//h4").text)

    # prompt for input
    choice = input('Choose course >> ')

    courses[int(choice) - 1].click()


# -------------------------------------------------------------------------- //
def get_to_captures():
    switch_to_frame()
    print('SWITCHED FRAMES')

    tries = 10
    
    # TODO redo with decorator timeout
    try:
        while tries > 0:
            links = DRIVER.find_elements_by_xpath("//a")
            names = map(lambda x: x.text, links)

            if 'Blackboard Collaborate Ultra' in names:
                for link in links:
                    if link.text == 'Blackboard Collaborate Ultra':
                        link.click()
                        print('CLICKED LINK')
                break

            tries = tries - 1
            time.sleep(1)
    except:
        print('ran out of tries')
"""
