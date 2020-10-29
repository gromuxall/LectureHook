#!/usr/bin/env python3
'''
    LectureHook

    Steven Madonna
    stevenmmadonna@gmail.com

'''
import sys
import os
import argparse
import logging
import pickle
from secrets import USERID, EMAIL, PASS, DVR_PATH

from seleniumrequests import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from simple_term_menu import TerminalMenu
from waits import elements_with_xpath
from app import App
from course_video import Course

# -------------------------------------------------------------------------- //
def fill_courses():
    '''Get list of courses'''
    containers = WebDriverWait(DRIVER, 10).until(
        elements_with_xpath("//span[@role='gridcell']"))

    with open('cookies.pickle', 'wb') as file_handle:
        pickle.dump(DRIVER.get_cookies(), file_handle,
                    protocol=pickle.HIGHEST_PROTOCOL)

    for crs in containers:
        Course.courses.append(Course(crs))
        Course.set_driver(DRIVER)
    Course.sort_courses()


# -------------------------------------------------------------------------- //
def print_menu():
    '''Sort and print course list, then return choice'''
    course_names = [z.menu_line() for z in Course.courses]
    choice = TerminalMenu(course_names).show()
    Course.courses[choice].goto_course()


# -------------------------------------------------------------------------- //
def check_root_path():
    '''Checks if path exists and changes to that directory if so'''
    # TODO: Check yaml file for root path, also, loop until root
    #       path is a valid one
    if not os.path.isdir(ARGS.root):
        print('ERROR: the path {} does not exist'.format(ARGS.root))

    os.chdir(ARGS.root)


# -------------------------------------------------------------------------- //
def load_session():
    '''Loads cookies into Selenium session'''
    DRIVER.get(App.get('site'))

    try:
        with open('cookies.pickle', 'rb') as cookie_handle:
            cookies = pickle.load(cookie_handle)
        for cookie in cookies:
            DRIVER.add_cookie(cookie)
        DRIVER.get(App.get('site'))
        DRIVER.get(App.get('site'))
    except Exception as e:
        print(MESSAGES['sign_in'])
        email_input = WebDriverWait(DRIVER, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='email']")))
        email_input.send_keys(App.get('email'))
        email_input.submit()

        DRIVER.find_element_by_xpath("//input[@id='UserID']").send_keys(App.get('username'))
        password = DRIVER.find_element_by_xpath("//input[@id='password']")
        password.send_keys(App.get('password'))
        password.submit()
        LOGGER.info(e)


# -------------------------------------------------------------------------- //
def main():
    '''Main program'''
    print(MESSAGES['intro'], MESSAGES['root'])
    load_session()
    fill_courses()
    print_menu()


# -------------------------------------------------------------------------- //
if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description='Download lectures from Echo360.',
        usage='python new_lecturehook.py [-r]')
    PARSER.add_argument('-r', '--root', required=True, help='type in full path\
            of the root folder you want the videos downloaded to')
    PARSER.add_argument('-w', '--window', action='store_true', help='show window')
    PARSER.add_argument('-l', '--log', action='store_true', help='debug logging')
    ARGS = PARSER.parse_args()
    APP = App(ARGS)
    '''
        - check for existence of file
        - initialize by creating file if it doesnt exist
        - check ARGS for root folder and if none, take folder and check it, switch to
        - check for session, and if exists, check for ttl value of cookie and prompt
            for password and username if past ttl value or no session exists
            
    '''

    LOGGER = logging.getLogger('lhook_logger')

    OPTIONS = Options()

    if not ARGS.window:
        OPTIONS.add_argument('--headless')

    if ARGS.log:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    PREFS = {'prompt_for_download': False}
    
    OPTIONS.add_experimental_option('prefs', PREFS)
    
    # TODO: set this in app
    DRIVER = Chrome(options=OPTIONS)


    # msg dictionary for laziness
    MESSAGES = {
        'intro': '\nLectureHook for Echo360',
        'root': '\nroot folder: {}'.format(ARGS.root),
        'sign_in': 'Signing in...',
        'collab': 'Fetching videos from Blackboard Collaborate',
        'echo': 'Fetching videos from Echo360',
        'exit': 'Exiting'
        }

    # begin program
    try:
        main()
    except Exception as err:
        #print(MESSAGES['exit'])
        LOGGER.info(err)
    finally:
        DRIVER.quit()
