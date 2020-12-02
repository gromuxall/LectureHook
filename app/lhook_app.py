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

#import errno
import concurrent.futures
from simple_term_menu import TerminalMenu
from task import Task
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

    Course.set_driver(APP.driver)
    
    for crs in containers:
        Course.courses.append(Course(crs))   
    Course.sort_courses()


# -------------------------------------------------------------------------- //
def clean_exit():
    '''Exits program gracefully by cleaning up any unfinished
    files and killing the driver process

    TODO: identify and clean up unfinished files
    '''
    APP.driver.quit()
    sys.exit()


# -------------------------------------------------------------------------- //
def menu(option, course=None):
    '''Sort and print course list, then return choice'''
    if option == 'courses':
        course_names = [x.menu_line() for x in Course.courses]
        course_names.append('(X) Exit')
        choice = TerminalMenu(course_names).show()
        
        if choice == len(course_names)-1:
            clean_exit()

        Course.courses[choice].goto_course()        
        menu('lectures', Course.courses[choice])
    elif option == 'lectures':
        # reference Course.sorted_courses[idx].lectures
        # so you can add checkmark to lecture names
        vid_names = [v.date for v in course.lectures]
        vid_names.insert(0, 'Download All Lectures')
        vid_names.insert(0, '<< Back to Courses')

        lec_choice = TerminalMenu(menu_entries=vid_names,
                                  title=course.long_name()).show()

        qty_choice = TerminalMenu(menu_entries=['SD', 'HD'],
                                  title='Quality').show()

        if lec_choice == 0:
            menu('courses')
        if lec_choice == 1: # Chose 'All Videos'
            if App.get('multi'):
                with concurrent.futures.ThreadPoolExecutor(
                        max_workers=3) as executor:
                    futures = []
                    tasks = []
                    for vid in course.lectures:
                        tasks.append(Task(vid, qty_choice, True))
                    for task in tasks:
                        futures.append(executor.submit(task.download))
                    for _ in concurrent.futures.as_completed(futures):
                        pass
            else:
                for vid in course.lectures:
                    Task(vid, qty_choice).download()
            menu('courses')

        else:
            Task(course.lectures[lec_choice-1], qty_choice).download()
            course.lectures[lec_choice-1].mark_dwn()
            menu('lectures', course)


# -------------------------------------------------------------------------- //
def main():
    '''Main program'''
    os.chdir(APP.get('download_path'))
    fill_courses()
    menu('courses')


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

    if ARGS.log:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    MESSAGES = {
        'intro': '\nLectureHook for Echo360',
        'sign_in': 'Signing in...',
        'collab': 'Fetching videos from Blackboard Collaborate',
        'echo': 'Fetching videos from Echo360',
        'exit': 'Exiting'
        }

    try:
        main()
    except Exception as err:
        logging.info(err)
    finally:
        clean_exit()