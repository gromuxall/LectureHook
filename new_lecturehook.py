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
from seleniumrequests import Chrome
from progress.spinner import Spinner
from progress.bar import Bar
from simple_term_menu import TerminalMenu
#from selenium import webdriver
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
        if len([i for i in glob.glob('*.crdownload')]) > 2:
            spinner = Spinner('MAX downloading three videos  ')
            while len([i for i in glob.glob('*.crdownload')]) > 2:
                spinner.next()
            rename_files()
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
            course = self
            title = row.find_element_by_class_name('header').text
            date = row.find_element_by_xpath(".//span[@class='date']").text
            index = idx
            lectures.append(Video(course, title, date, index))

        vid_names = [v.date for v in lectures]
        vid_names.insert(0, 'all videos')
        terminal_menu = TerminalMenu(menu_entries=vid_names, title=name)
        choice = terminal_menu.show()

        # TODO right now this just downloads all of them, so change
        quality_menu = TerminalMenu(menu_entries=['SD', 'HD', 'Audio Only'],
                title='Quality')
        qchoice = quality_menu.show()
        
        for vid in lectures:
            vid.download(qchoice)
            #print('Downloading lecture {} from {}'.format(vid.index, vid.date))

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
        self.done = False

        # make map from month name to number
        cal_num = {name: num for num, name in enumerate(cal.month_name) if num}


    # <Video> -------------------------------------------------------------- //
    def button(self):
        media_capture = DRIVER.find_elements_by_xpath(
            "//*[contains(@class, 'courseMediaIndicator capture')]")

        return media_capture[self.index]

    # <Video> -------------------------------------------------------------- //
    def complete(self):
        '''
        Mark as done for renaming so we don't rename twice
        '''
        self.done = True

    # <Video> -------------------------------------------------------------- //
    def is_done(self):
        '''
        Check renaming completion of video
        '''
        return self.done

    # <Video> -------------------------------------------------------------- //
    def header_line(self):
        '''
        Returns a formatted line with course information
        '''
        crs = self.course
        return '{} {} - {}\n{} {} - {}'.format(crs.crs_code, crs.crs_num, 
                crs.title, crs.term, crs.year, crs.crn)

    # <Video> -------------------------------------------------------------- //
    def lecture_line(self):
        '''
        Return a formatted line with video information
        '''
        return 'Lecture {} - {}'.format(self.index, self.date)

    # <Video> -------------------------------------------------------------- //
    def get_url(self, choice):
        '''
        Finds download urls for sd and hd versions
        '''
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

        select = Select(DRIVER.find_element_by_xpath(
            "//select[@name='video-one-files']"
        ))
        select.select_by_index(choice)

        url = DRIVER.find_element_by_xpath(
            "//a[@class='btn primary medium downloadBtn']"
        ).get_attribute('href')
        
        # click cancel button
        DRIVER.find_element_by_xpath(
            "//a[@class='btn white medium']"
        ).click()

        return url

    # <Video> -------------------------------------------------------------- //
    def download(self, qchoice):
        """
        Clicks and selects quality, then downloading video
        """
        download_file(self.get_url(qchoice), self)

        time.sleep(2)
        add_download(self)


# -------------------------------------------------------------------------- //
def download_file(url, vid):
    '''
    Downloads a file in chunks and updates progress bar
    '''
    length = get_content_len(url)
    with DRIVER.request('GET', url, stream=True) as res:
        res.raise_for_status()
        print('\n─────────────────────────────────────────────')
        print(vid.header_line())
        print(vid.lecture_line())
        prog_bar = Bar('{}.mp4'.format(vid.index), max=int(length)/8192,
                       fill='▓', suffix='%(percent)d%%')

        with open('{}.mp4'.format(vid.index), 'wb') as file:
            for chunk in res.iter_content(chunk_size=8192):
                prog_bar.next()
                file.write(chunk)


# -------------------------------------------------------------------------- //
def get_content_len(url):
    '''
    Returns integer content length of video
    '''
    res = DRIVER.request('HEAD', url)
    return int(res.headers['Content-Length'])


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
def rename_files():
    '''
    Renames downloaded files
    '''
    dwns = [i for i in glob.glob('*.mp4')]
    print('dwns: {}'.format(dwns))


    for key, val in DOWNLOADS.items():
        filename = '{}'.format(key)
        print('filename: {}'.format(filename))
        if filename in dwns:
            #print('key: {} val:{}'.format(key, val.date))
            new_val = DOWNLOADS.pop().index
            os.rename(filename, '{}.mp4'.format(new_val))
            print('renaming: {} to {}'.format(filename, new_val))


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

    terminal_menu = TerminalMenu(crs_names)
    choice = terminal_menu.show()

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
    DRIVER = Chrome(CONFIG['PATHS']['driver'], options=options)

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
        # TODO: reactivate thiss
        #cleanup_files()

