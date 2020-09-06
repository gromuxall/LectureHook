#!/usr/bin/env python3
"""
    LectureHook

    Steven Madonna
    smadon3@uic.edu

    TODO:
        - pickle session to file and load to avoid login
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
import errno
from tqdm import tqdm
from js import *
import concurrent.futures
from secrets import USERID, EMAIL, PASS, DVR_PATH
from seleniumrequests import Chrome
from progress.spinner import Spinner
from progress.bar import Bar
from simple_term_menu import TerminalMenu
#from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from tqdm.utils import _term_move_up

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
            #rename_files()
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


class Course():
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
        self.url = course.find_element_by_xpath(".//a").get_attribute('href')
        self.lectures = []

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
    def folder_name(self):
        return self.crs_code + self.crs_num

    # <Course> ------------------------------------------------------------- //
    def goto_course(self):
        """
        Changes active driver window to chosen course
        """
        DRIVER.get(self.url)
        time.sleep(2) # TODO change this
        
        self.fill_lectures()

    
    # <Course> ------------------------------------------------------------- //
    def menu_line(self):
        """
        Provides a pretty formatted string for the menu
        """
        title_str = self.crs_code + ' ' + self.crs_num + ' - ' + self.title
        return title_str.ljust(42) + (self.crn).ljust(20)
    

    # <Course> ------------------------------------------------------------- //
    def fill_lectures(self):
        """
        Get lecture elements
        """

        # wait for elements to appear
        WebDriverWait(DRIVER, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='class-row']")))
        # TODO: have rows equal the webdriverwait
        rows = DRIVER.find_elements_by_xpath("//div[contains(@class, 'class-row')]")
        
        for idx, row in enumerate(rows):
            title = row.find_element_by_class_name('header').text
            date = row.find_element_by_xpath(".//span[@class='date']").text
            self.lectures.append(Video(self, title, date, idx))

        '''here is where I should extract all the video links'''
        DRIVER.execute_script(
            '''
            {}

            btns = document.querySelectorAll("div[class*='courseMediaIndicator capture']")
            click_all(btns)
            '''.format(CLICK_ALL)
            )

        '''move this to a wait function and make decorator for timing and killing'''
        tries = 30
        while tries > 0:
            try:
                li_elems = DRIVER.find_elements_by_xpath("//div[@class='menu-items']/ul/li/a")
                if (len(li_elems) / 3) == len(self.lectures):
                    break
            except Exception as e:
                #print('waiting....{}'.format(e))
                time.sleep(1)
                tries -= 1
        
        DRIVER.execute_script(
            '''
            {}{}

            li_elems = document.querySelectorAll(".menu-items ul li a");
            dwns = filter_list(li_elems)
            click_all(dwns)
            '''.format(CLICK_ALL, FILTER_LIST)
            )
        
        '''move this to a wait function and make decorator for timing and killing'''
        selects = []
        tries = 30
        while tries > 0:
            try:
                selects = DRIVER.find_elements_by_xpath(
                        "//select[@name='video-one-files']")
                if len(selects) == len(self.lectures):
                    break
            except Exception as e:
                print('len(selects): {}, len(self.lectures): {}'.format(len(selects), len(self.lectures)))
                time.sleep(1)
                tries -= 1

        for sel, vid in zip(selects, self.lectures):
            ops = sel.find_elements_by_xpath("./option")
            vid.sd_link = ops[0].get_attribute('value').split(' || ')[0]# split off into method
            vid.hd_link = ops[1].get_attribute('value').split(' || ')[0]

        vid_names = [v.date for v in self.lectures]
        vid_names.insert(0, 'all videos')

        name = self.crs_code + ' ' + self.crs_num + ' - ' + self.title
        terminal_menu = TerminalMenu(menu_entries=vid_names, title=name)
        choice = terminal_menu.show()

        quality_menu = TerminalMenu(menu_entries=['SD', 'HD'],
                                    title='Quality')
        qchoice = quality_menu.show()

        check_dir(self.folder_name())

        if choice == 0:
            # download all videos
            if qchoice == 0: # change this to enum SD=0, HD=1
                vid_urls = [(vid, vid.sd_link) for vid in self.lectures]
            else:
                vid_urls = [(vid, vid.hd_link) for vid in self.lectures]
            #pbar = tqdm(total=len(self.lectures), initial=0, position=0, ncols=90,
            #            bar_format='{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}')
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                tasks = []
                for vid in self.lectures:
                    tasks.append(Task(vid))
                for task in tasks:
                    futures.append(executor.submit(task.download))
                #for _ in concurrent.futures.as_completed(futures):
                #    pbar.update(1)
        else:
            vid = self.lectures[choice-1]
            if qchoice == 0:
                download_file((vid, vid.sd_link))
            else:
                download_file((vid, vid.hd_link))


class Task():
    
    def __init__(self, vid):
        self.vid = vid
        self.length = get_content_len(vid.sd_link) #TODO: big NO-NO, using sd_link as a sample!
        self.url = vid.sd_link
        text = 'lec{}.mp4'.format(str(vid.index).zfill(2))
        self.pbar = tqdm(total=int(int(self.length)/8192), initial=0, unit='B',
                    position=vid.index, desc=text, leave=True, ncols=90,
                    bar_format='{desc} {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}')
        self.pbar.update(0)

    def download(self):
        with DRIVER.request('GET', self.url, stream=True) as res:
            res.raise_for_status()
            text = 'lec{}.mp4'.format(str(self.vid.index).zfill(2))

            with open('{}.mp4'.format(self.vid.vid_title()), 'wb') as file:
                for chunk in res.iter_content(chunk_size=8192):
                    self.pbar.update(1)
                    file.write(chunk)
            #self.pbar.close()


# -------------------------------------------------------------------------- //
def download_file(entry):
    '''
    Downloads a file in chunks and updates progress bar
    '''
    vid, url = entry
    length = get_content_len(url)
    with DRIVER.request('GET', url, stream=True) as res:
        res.raise_for_status()
        text = 'lec{}.mp4'.format(str(vid.index).zfill(2))
        pbar = tqdm(total=int(int(length)/8192), initial=0, unit='B',
                    position=vid.index, desc=text, leave=False, ncols=90,
                    bar_format='{desc} {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}')

        with open('{}.mp4'.format(vid.vid_title()), 'wb') as file:
            for chunk in res.iter_content(chunk_size=8192):
                pbar.update(1)
                file.write(chunk)

        #tqdm.write('{} finished downloading.'.format(vid.vid_title()))
        #tqdm.write(_term_move_up() + '\r')
        pbar.close()


class Video():
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
        self.sd_link = ''    #<---- make this a tuple url = (SD, HD)
        self.hd_link = ''

        # make map from month name to number
        self.cal_num = {name: str(num).zfill(2) for num, name in enumerate(cal.month_name) if num}


    # <Video> -------------------------------------------------------------- //
    def button(self):
        media_capture = DRIVER.find_elements_by_xpath(
            "//*[contains(@class, 'courseMediaIndicator capture')]")

        return media_capture[self.index]

    # <Video> -------------------------------------------------------------- //
    def get_date(self):
        '''
        Returns string with numeric date

        Example:
        August 29, 2019 => 08-29-2019
        '''
        splits = self.date.replace(',', ' ').split()
        return '{}-{}-{}'.format(self.cal_num[splits[0]], splits[1].zfill(2), splits[2])


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
                                               crs.title, crs.term,
                                               crs.year, crs.crn)

    # <Video> -------------------------------------------------------------- //
    def lecture_line(self):
        '''
        Return a formatted line with video information
        '''
        return 'Lecture {} - {}'.format(self.index, self.date)


    # <Video> -------------------------------------------------------------- //
    def vid_title(self):
        '''
        Return formatted video title
        '''
        crs = self.course
        return '{}{}-lec{}_{}'.format(crs.crs_code, crs.crs_num,
                                      str(self.index).zfill(2), self.get_date())


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
    #def download(self, qchoice):
        """
        Clicks and selects quality, then downloading video
        """
    #    download_file(self.get_url(qchoice), self)
    #    time.sleep(2)




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
    """
    DRIVER.get('https://echo360.org/courses')
    email_input = WebDriverWait(DRIVER, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name='email']"))
    )
    email_input.send_keys(EMAIL)
    email_input.submit()

    DRIVER.find_element_by_xpath("//input[@id='UserID']").send_keys(USERID)
    password = DRIVER.find_element_by_xpath("//input[@id='password']")
    password.send_keys(PASS)
    password.submit()
    print(MESSAGES['sign_in'])



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
def check_dir(path):
    '''
    Check if directory exists

    on True:
       changes to chosen directory

    on False:
        creates directory and changes to it
    '''
    try:
        os.mkdir(path)
        os.chdir(path)
    except IOError as err:
        if err.errno == errno.EEXIST:
            print('Downloading to {}'.format(path))
            os.chdir(path)


# -------------------------------------------------------------------------- //
def check_root_path():
    """
    Checks if path exists and changes to that directory if so
    """
    if not os.path.isdir(ARGS.root):
        print('ERROR: the path {} does not exist'.format(ARGS.root))

    os.chdir(ARGS.root)


# -------------------------------------------------------------------------- //
def main():
    """
    Main program
    """
    print('\n┌───────────────────────────────────────────┐')
    print('│  LectureHook for Echo360                  │')
    print('└───────────────────────────────────────────┘\n')

    print('Downloading to {}'.format(ARGS.root))
    launch_page_echo()
    get_courses()
    print_menu()


# -------------------------------------------------------------------------- //
if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        #description='Download lectures from Echo360 or Blackboard Collaborate.',
        description='Download lectures from Echo360.',
        #usage='python new_lecturehook.py [-e] [-c]')
        usage='python new_lecturehook.py [-r]')
    PARSER.add_argument('-r', '--root', required=True, help='type in full path\
            of the root folder you want the videos downloaded to')
    PARSER.add_argument('-w', '--window', action='store_true', help='show window')
    ARGS = PARSER.parse_args()

    check_root_path()

    # setup the logger
    LOGGER = logging.getLogger('lhook_logger')
    #logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # read preliminary info from config file
    # TODO autogenerate config file
        # if config file doesn't exist, create one and prompt for input
    #CONFIG = configparser.ConfigParser()
    #CONFIG.read('courses.ini')

    # set browser options
    options = Options()
    
    if not ARGS.window:
        options.add_argument('--headless')
    #options.add_argument('--disable-gpu')
    prefs = {'prompt_for_download': False}
    options.add_experimental_option('prefs', prefs)
    DRIVER = Chrome(DVR_PATH, options=options)

    # global structs for ease of access
    COURSES = []

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
        DRIVER.quit()
