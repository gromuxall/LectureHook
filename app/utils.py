import platform
import os
from zipfile import ZipFile
from lxml import html

import requests


def chrome_version():
    '''Determines os and returns version of Chrome'''
    path = None
    paths = {
        'Linux': 
            '/usr/bin/google-chrome',
        'Darwin': 
            '/Applications/Google \Chrome.app/Contents/MacOS/Google \Chrome',
        'Windows': 
            'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    }
    
    try:
        path = paths[platform.system()]
    except KeyError:
        raise NotImplemented('Unknown Operating System')

    # get version string and return the major version number
    ver = os.popen('{} --version'.format(path))
    if not ver:
        raise FileNotFoundError('Google Chrome is not installed')
    return ver.read().strip('Google Chrome ').strip().split('.', 1)[0]


def get_chromedriver(version):
    '''Takes major version number of Chrome and downloads correct
    chromedriver version and unzips'''
    # download correct chromedriver version
    page = requests.get('https://chromedriver.chromium.org/downloads')
    tree = html.fromstring(page.content)
    ver_num = tree.xpath("//a[contains(text(), 'ChromeDriver {}')]".format(version))
        
    # link may possibly be repeated on page, take first one if so
    if len(ver_num) > 1:
        ver_num = ver_num[0]
    
    # extract just the version number
    ver = ver_num.text.split('ChromeDriver ')[1]
    
    # download the chromedriver zip files
    with open('chromedriver.zip', 'wb') as file:
        response = requests.get('https://chromedriver.storage.googleapis.com/{}/chromedriver_linux64.zip'.format(ver))
        file.write(response.content)

    # extract from zip file
    try:
        with ZipFile('chromedriver.zip', 'r') as zipObj:
            zipObj.extractall()
    except OSError as err:
        if err.errno == 26:
            print('Chromedriver already present')

    # remove unneeded file
    os.remove('chromedriver.zip')