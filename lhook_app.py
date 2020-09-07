#!/usr/bin/env python3
'''
    LectureHook

    Steven Madonna
    stevenmmadonna@gmail.com

'''
import sys
import time
import os
import os.path
import calendar as cal
import argparse
import logging
import errno
import pickle
import concurrent.futures
from enum import Enum
from secrets import USERID, EMAIL, PASS, DVR_PATH
import yaml
from tqdm import tqdm
from simple_term_menu import TerminalMenu

from seleniumrequests import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from waits import elements_with_xpath, elements_by_length
from js import CLICK_ALL_FUNC, CLICK_ALL_BTNS, CLICK_ALL_LINKS, FILTER_LIST_FUNC


class ElementNotFound(Exception):
    '''Exception raised for error in finding element'''
    def __init__(self, element, message="Element not found"):
        self.element = element
        self.message = message
        super().__init__(self.message)


class Quality(Enum):
    '''Integer representing position of quality in dropdown options
       for select
    '''
    SD = 0
    HD = 1


class App():
    '''Wrapper class for configuration'''
    _config = {
        'username': '',
        'password': '',
        'root': '',
        'driver': '',
        'site': 'https://echo360.org/courses',
    }
    _setters = ['username', 'password', 'root', 'driver']

    # <App> ---------------------------------------------------------------- //
    def __init__(self):
        try:
            with open('config.yaml') as handle:
                App._config = yaml.load(handle, Loader=yaml.FullLoader)
        except FileNotFoundError:
            pass

    # <App> ---------------------------------------------------------------- //
    @staticmethod
    def get(name):
        '''Get specified config value'''
        return App._config[name]

    # <App> ---------------------------------------------------------------- //
    @staticmethod
    def set(name, value):
        '''Set specified config value and save state to yaml'''
        if name in App._setters:
            App._config[name] = value

            with open('config.yaml', 'w') as handle:
                yaml.dump(App._config, handle)
        else:
            raise NameError('Name not accepted in set() method')

    # <App> ---------------------------------------------------------------- //
    @staticmethod
    def check_root_path():
        '''Checks if path exists and changes to that directory if so'''
        # TODO: Check yaml file for root path, also, loop until root
        #       path is a valid one
        if not os.path.isdir(ARGS.root):
            print('ERROR: the path {} does not exist'.format(ARGS.root))

        os.chdir(ARGS.root)


class Course():
    '''Contains all info and methods for courses scraped from Echo360'''
    courses = []

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
        return self.long_name()

    # <Course> ------------------------------------------------------------- //
    @staticmethod
    def sort_courses():
        '''
        Sort the static variable list courses
        '''
        Course.courses = sorted(Course.courses, key=lambda x: x.crs_num)

    # <Course> ------------------------------------------------------------- //
    @staticmethod
    def split_link(string):
        '''
        Utility that splits off url from accompanying information
        '''
        return string.get_attribute('value').split(' || ')[0]

    # <Course> ------------------------------------------------------------- //
    @staticmethod
    def check_dir(path):
        '''
        Check if directory exists

        True:
           changes to chosen directory

        False:
            creates directory and changes to it
        '''
        try:
            os.mkdir(path)
            os.chdir(path)
        except IOError as err:
            if err.errno == errno.EEXIST:
                os.chdir(path)
        print('Downloading to {}'.format(path)) #TODO change this

    # <Course> ------------------------------------------------------------- //
    def short_name(self):
        '''
        Return short string representation of course
        '''
        return '{}{}'.format(self.crs_code, self.crs_num)

    # <Course> ------------------------------------------------------------- //
    def long_name(self):
        '''
        Return long string representation of course
        '''
        return '{} - {}'.format(self.short_name(), self.title)

    # <Course> ------------------------------------------------------------- //
    def menu_line(self):
        '''
        Provides a pretty formatted string for the menu
        '''
        return self.long_name().ljust(42) + (self.crn).ljust(20)

    # <Course> ------------------------------------------------------------- //
    def goto_course(self):
        '''
        Changes active driver window to chosen course
        '''
        DRIVER.get(self.url)
        time.sleep(2) # TODO change this, add a wait here

        Course.check_dir(self.short_name())
        self.fill_lectures()

    # <Course> ------------------------------------------------------------- //
    def extract_links(self, selects):
        '''
        Extracts the SD and HD version links from options in the passed
        in list of selects and fills those values in for the video objects
        '''
        for sel, vid in zip(selects, self.lectures):
            ops = sel.find_elements_by_xpath("./option")
            vid.links['SD'] = Course.split_link(ops[Quality.SD.value])
            vid.links['HD'] = Course.split_link(ops[Quality.HD.value])

    # <Course> ------------------------------------------------------------- //
    def fill_lectures(self):
        '''
        Get lecture elements
        '''
        wait = WebDriverWait(DRIVER, 10)
        rows = wait.until(
            elements_with_xpath("//div[@class='class-row']"))

        for idx, row in enumerate(rows):
            self.lectures.append(Video(
                self,
                row.find_element_by_class_name('header').text,
                row.find_element_by_xpath(".//span[@class='date']").text,
                idx))

        num_lecs = len(self.lectures)

        # find and click all btns to bring up video options
        DRIVER.execute_script('{}{}'.format(CLICK_ALL_FUNC, CLICK_ALL_BTNS))

        # there are three list elements, so multiply num_lecs by three
        wait.until(elements_by_length(
            "//div[@class='menu-items']/ul/li/a", num_lecs * 3))

        # find and click all 'Download Original' links
        DRIVER.execute_script('{}{}{}'.format(CLICK_ALL_FUNC, FILTER_LIST_FUNC,
                                              CLICK_ALL_LINKS))

        selects = wait.until(elements_by_length(
            "//select[@name='video-one-files']", num_lecs))
        self.extract_links(selects)

        vid_names = [v.date for v in self.lectures]
        vid_names.insert(0, 'All Lectures')

        lec_choice = TerminalMenu(menu_entries=vid_names,
                                  title=self.long_name()).show()

        qty_choice = TerminalMenu(menu_entries=['SD', 'HD'],
                                  title='Quality').show()

        if lec_choice == 0: # Chose 'All Videos'
            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=3) as executor:
                futures = []
                tasks = []
                for vid in self.lectures:
                    tasks.append(Task(vid, qty_choice))
                for task in tasks:
                    futures.append(executor.submit(task.download))
                #for ret in concurrent.futures.as_completed(futures):
                #    #tiasks[ret].finish_
        else:
            Task(self.lectures[lec_choice-1], qty_choice).download()


class Video():
    '''
    Object representing a class-row of a lecture for a given course
    '''
    cal_num = {name: str(num).zfill(2) for num, name in
               enumerate(cal.month_name) if num}

    # <Video> -------------------------------------------------------------- //
    def __init__(self, course, title, date, index):
        self.course = course
        self.title = title
        self.date = date
        self.index = index
        self.links = {'SD': '', 'HD': ''}

    # <Video> -------------------------------------------------------------- //
    def get_content_len(self, quality):
        '''
        Returns integer content length of video
        '''
        res = DRIVER.request('HEAD', self.links[Quality(quality).name])
        return int(res.headers['Content-Length'])

    # <Video> -------------------------------------------------------------- //
    def url(self, num):
        '''
        Return link for specified quality
        '''
        return self.links[Quality(num).name]

    # <Video> -------------------------------------------------------------- //
    def get_date(self):
        '''
        Returns string with numeric date

        Example:
        August 29, 2019 => 08-29-2019
        '''
        splits = self.date.replace(',', ' ').split()
        return '{}-{}-{}'.format(Video.cal_num[splits[0]],
                                 splits[1].zfill(2), splits[2])

    # <Video> -------------------------------------------------------------- //
    def vid_title(self):
        '''
        Return formatted video title
        '''
        crs = self.course
        return '{}{}-lec{}_{}'.format(crs.crs_code, crs.crs_num,
                                      str(self.index).zfill(2), self.get_date())


class Task():
    '''
    Object for initializing progress bar for downloads and performing
    the download upon call
    '''
    def __init__(self, vid, quality):
        self.vid = vid
        self.url = vid.url(quality)
        self.length = vid.get_content_len(quality)
        text = 'lec{}.mp4'.format(str(vid.index).zfill(2))
        self.pbar = tqdm(total=int(int(self.length)/8192), initial=0,
                         position=vid.index, desc=text, leave=False,
                         ncols=90, bar_format='{desc} {percentage:3.0f}\
                                               %|{bar}| {n_fmt}/{total_fmt}')
        self.pbar.update(0)

    # <Task> --------------------------------------------------------------- //
    def finish_msg(self):
        '''
        Display confirmation message
        '''
        self.pbar.display(msg='{} downloaded.'.format(self.vid.vid_title()),
                          pos=self.vid.index)

    # <Task> --------------------------------------------------------------- //
    def download(self):
        '''
        Stream downloads file pointed to by self.url and returns index
        '''
        with DRIVER.request('GET', self.url, stream=True) as res:
            res.raise_for_status()

            with open('{}.mp4'.format(self.vid.vid_title()), 'wb') as file:
                for chunk in res.iter_content(chunk_size=8192):
                    self.pbar.update(1)
                    file.write(chunk)
                self.finish_msg()
        return self.vid.index



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
    Course.sort_courses()


# -------------------------------------------------------------------------- //
def print_menu():
    '''
    Sort and print course list, then return choice
    '''
    course_names = [z.menu_line() for z in Course.courses]
    choice = TerminalMenu(course_names).show()
    Course.courses[choice].goto_course()


# -------------------------------------------------------------------------- //
def check_root_path():
    '''
    Checks if path exists and changes to that directory if so
    '''
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
        email_input.send_keys(EMAIL)
        email_input.submit()

        DRIVER.find_element_by_xpath("//input[@id='UserID']").send_keys(USERID)
        password = DRIVER.find_element_by_xpath("//input[@id='password']")
        password.send_keys(PASS)
        password.submit()


# -------------------------------------------------------------------------- //
def save_state(config):
    '''
    Loads previous state of program
    '''
    with open('config.yaml', 'w') as fp:
        yaml.dump(config, fp)


# -------------------------------------------------------------------------- //
def main():
    '''
    Main program
    '''
    print(MESSAGES['intro'], MESSAGES['root'])
    load_session()
    #launch_page_echo()
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

    # TODO: if no root path
    check_root_path()
    LOGGER = logging.getLogger('lhook_logger')
    
    OPTIONS = Options()

    if not ARGS.window:
        OPTIONS.add_argument('--headless')

    if ARGS.log:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    PREFS = {'prompt_for_download': False}
    OPTIONS.add_experimental_option('prefs', PREFS)
    DRIVER = Chrome(DVR_PATH, options=OPTIONS)
    

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
        print(MESSAGES['exit'])
        LOGGER.info(err)
    finally:
        DRIVER.quit()
