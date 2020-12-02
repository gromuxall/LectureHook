import os
import logging

from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from enum import Enum
import calendar as cal

from app import App

from waits import elements_with_xpath, elements_by_length
from js import CLICK_ALL_FUNC, CLICK_ALL_BTNS, CLICK_ALL_LINKS, FILTER_LIST_FUNC


class Course:
    '''Contains all info and methods for courses scraped from Echo360'''
    courses = []
    driver = None
    cal_num = {name: str(num).zfill(2) for num, name in
               enumerate(cal.month_name) if num}

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
        self.crs_url = course.find_element_by_xpath(".//a").get_attribute('href')
        self.lectures = []

    # <Course> ------------------------------------------------------------- //
    @staticmethod
    def set_driver(driver):
        '''Set WebDriver for whole class if not already set'''
        if not Course.driver:
            Course.driver = driver

    @staticmethod
    def get_driver():
        '''Get WebDriver'''
        return Course.driver

    # <Course> ------------------------------------------------------------- //
    def __str__(self):
        return self.long_name()

    # <Course> ------------------------------------------------------------- //
    @staticmethod
    def sort_courses():
        '''Sort the static variable list courses'''
        Course.courses = sorted(Course.courses, key=lambda x: x.crs_num)

    # <Course> ------------------------------------------------------------- //
    @staticmethod
    def clean_link(string):
        '''Utility that splits off url from accompanying information'''
        link = 'https://echo360.org/media/download/{}/video/{}'
        splits = string.get_attribute('value').split(' || ')
        code = splits[0]
        quality = splits[2]
        return link.format(code, quality)
        

    # <Course> ------------------------------------------------------------- //
    @staticmethod
    def check_dir(dir_path):
        '''Creates directory if nonexistent'''
        try:
            os.mkdir(dir_path)
        except IOError as err:
            pass

    # <Course> ------------------------------------------------------------- //
    def short_name(self):
        '''Return short string representation of course'''
        return '{}{}'.format(self.crs_code, self.crs_num)

    # <Course> ------------------------------------------------------------- //
    def long_name(self):
        '''Return long string representation of course'''
        return '{} - {}'.format(self.short_name(), self.title)

    # <Course> ------------------------------------------------------------- //
    def dir_path(self):
        '''Return path to this course's folder'''
        return '{}/{}'.format(App.get('download_path'), self.short_name())

    # <Course> ------------------------------------------------------------- //
    def menu_line(self):
        '''Provides a pretty formatted string for the menu'''
        return self.long_name().ljust(42) + (self.crn).ljust(20)

    # <Course> ------------------------------------------------------------- //
    def goto_course(self):
        '''Changes active driver window to chosen course'''
        self.driver.get(self.crs_url)
        #Course.check_dir(self.short_name())
        Course.check_dir(self.dir_path())
        self.fill_lectures()

    # <Course> ------------------------------------------------------------- //
    def extract_links(self, selects):
        '''Extracts the SD and HD version links from options in the passed
        in list of selects and fills those values in for the video objects
        '''
        for sel, vid in zip(selects, self.lectures):
            ops = sel.find_elements_by_xpath("./option")
            vid.links['SD'] = Course.clean_link(ops[Quality.SD.value])
            vid.links['HD'] = Course.clean_link(ops[Quality.HD.value])

    # <Course> ------------------------------------------------------------- //
    def fill_lectures(self):
        '''Get lecture elements'''
        wait = WebDriverWait(self.driver, 10)
        rows = wait.until(
            elements_with_xpath("//div[@class='class-row']"))

        for idx, row in enumerate(rows):
            try:
                row.find_element_by_xpath(
                    ".//*[contains(@class, 'courseMediaIndicator capture')]")
                self.lectures.append(Video(
                    self,
                    row.find_element_by_class_name('header').text,
                    row.find_element_by_xpath(".//span[@class='date']").text,
                    idx))
            except NoSuchElementException:
                pass
                logging.info('Element not found')

        num_lecs = len(self.lectures)

        # find and click all btns to bring up video options
        self.driver.execute_script('{}{}'.format(CLICK_ALL_FUNC, CLICK_ALL_BTNS))

        # there are three list elements, so multiply num_lecs by three
        wait.until(elements_by_length(
            "//div[@class='menu-items']/ul/li/a", num_lecs * 3))

        # find and click all 'Download Original' links
        self.driver.execute_script('{}{}{}'.format(CLICK_ALL_FUNC, FILTER_LIST_FUNC,
                                                   CLICK_ALL_LINKS))

        selects = wait.until(elements_by_length(
            "//select[@name='video-one-files']", num_lecs))
        self.extract_links(selects)


class Quality(Enum):
    '''Integer representing position of quality in dropdown options
    for select
    '''
    SD = 0
    HD = 1


class Video(Course):
    '''Object representing a class-row of a lecture for a given course'''

    # <Video> -------------------------------------------------------------- //
    def __init__(self, course, title, date, index):
        self.course = course
        self.title = title
        self.date = date
        self.index = index
        self.links = {'SD': '', 'HD': ''}

    # <Video> -------------------------------------------------------------- //
    def get_content_len(self, quality):
        '''Returns integer content length of video'''
        res = Course.driver.request('HEAD', self.links[Quality(quality).name])
        return int(res.headers['Content-Length'])

    # <Video> -------------------------------------------------------------- //
    def url(self, num):
        '''Return link for specified quality'''
        return self.links[Quality(num).name]

    # <Video> -------------------------------------------------------------- //
    def mark_dwn(self):
        '''Return title and checkmark'''
        self.date = '✓ - ' + self.date

    # <Video> -------------------------------------------------------------- //
    def get_date(self):
        '''Returns string with numeric date

        Example:
            August 29, 2019 => 08-29-2019
        '''
        splits = self.date.replace(',', ' ').split()
        return '{}-{}-{}'.format(Course.cal_num[splits[0]],
                                 splits[1].zfill(2), splits[2])

    # <Video> -------------------------------------------------------------- //
    def vid_title(self):
        '''Return formatted video title'''
        crs = self.course
        return '{}{}-{}_{}'.format(crs.crs_code, crs.crs_num,
                                   str(self.index).zfill(2), self.get_date())
