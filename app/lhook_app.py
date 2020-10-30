#!/usr/bin/env python3

import sys
import os
import argparse
import logging
import pickle

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
    containers = WebDriverWait(APP.driver, 10).until(
        elements_with_xpath("//span[@role='gridcell']"))

    with open('cookies.pickle', 'wb') as file_handle:
        pickle.dump(APP.driver.get_cookies(), file_handle,
                    protocol=pickle.HIGHEST_PROTOCOL)

    for crs in containers:
        Course.courses.append(Course(crs))
        Course.set_driver(APP.driver)
    Course.sort_courses()


# -------------------------------------------------------------------------- //
def menu():
    '''Sort and print course list, then return choice'''
    course_names = [z.menu_line() for z in Course.courses]
    choice = TerminalMenu(course_names).show()
    Course.courses[choice].goto_course()

# -------------------------------------------------------------------------- //
def main():
    '''Main program'''
    os.chdir(APP.get('download_path'))
    fill_courses()
    menu()


# -------------------------------------------------------------------------- //
if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description='Download lectures from Echo360.',
        usage='python new_lecturehook.py')
    PARSER.add_argument('-w', '--window', action='store_true', help='show browser window')
    PARSER.add_argument('-l', '--log', action='store_true', help='debug logging')
    ARGS = PARSER.parse_args()
    
    APP = App()

    LOGGER = logging.getLogger('lhook_logger')

    #OPTIONS = Options()

    #if not ARGS.window:
    #    OPTIONS.add_argument('--headless')

    if ARGS.log:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    #PREFS = {'prompt_for_download': False}
    
    #OPTIONS.add_experimental_option('prefs', PREFS)
    
    # TODO: set this in app
    #DRIVER = Chrome(options=OPTIONS)


    # msg dictionary for laziness
    MESSAGES = {
        'intro': '\nLectureHook for Echo360',
        #'root': '\nroot folder: {}'.format(ARGS.root),
        'sign_in': 'Signing in...',
        'collab': 'Fetching videos from Blackboard Collaborate',
        'echo': 'Fetching videos from Echo360',
        'exit': 'Exiting'
        }

    # begin program
    """
    try:
        main()
    except Exception as err:
        #print(MESSAGES['exit'])
        LOGGER.info(err)
    finally:
        APP.driver.quit()
    """
    main()
