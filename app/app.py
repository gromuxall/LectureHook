import os
import sys
import yaml
import logging
import pickle
import getpass
from functools import wraps
from seleniumrequests import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from waits import elements_with_xpath
from utils import chrome_version, get_chromedriver

LOGGER = logging.getLogger(__name__)

class App:
    '''Wrapper class for configuration'''
    _config = {
        'email': None,
        'password': None,
        'multi': False, # multithreading turned off by default
        'headless': True,
        'driver_path': None,
        'download_path': '../Lectures',
        'url': 'https://echo360.org/courses',
    }
    #_setters = ['username', 'password', 'root', 'driver', 'multi', 'window',
    #            'log']
    driver = None

    
    # <App> ---------------------------------------------------------------- //
    def update(func):
        '''Updates yaml file with any changes to class _config'''
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            with open('config.yaml', 'w') as handle:
                yaml.dump(App._config, handle)
            return result
        return wrapper
    
    # <App> ---------------------------------------------------------------- //
    @staticmethod
    @update
    def first_time_setup():
        '''Set up chromedriver and add path to config file'''
    
        get_chromedriver(chrome_version())
        App._config['driver_path'] = '{}/chromedriver'.format(os.getcwd())

        # change permissions for chromedriver
        os.chmod(App._config['driver_path'], 755)


    # <App> ---------------------------------------------------------------- //
    def __init__(self):
        '''Loads config file from install directory and populates the _config
        dictionary.

        If no config file is found, one is created and populated with the
        defaults.
        '''
        try:
            with open('config.yaml', 'r') as handle:
                App._config = yaml.full_load(handle)
        except FileNotFoundError:
            # create config file
            with open('config.yaml', 'w+') as handle:
                    yaml.dump(App._config, handle)

        if not App._config['driver_path']:
            App.first_time_setup()

        App.check_path()
        App.setup_driver()
        App.load_session()

    # <App> ---------------------------------------------------------------- //
    @staticmethod
    def check_path():
        '''Confirms that download_path is a valid path'''
        path = App._config['download_path']
        if not os.path.isdir(path):
            try:
                os.mkdir(path)
            except OSError:
                print('ERROR: cannot create path: {}'.format(path))
            sys.exit()

    # <App> ---------------------------------------------------------------- //
    @staticmethod
    def setup_driver(url=None):
        '''Configures and sets class member driver'''
        opt = Options()
        opt.add_experimental_option('prefs', {'prompt_for_download': False})

        if App._config['headless']:
            opt.add_argument('--headless')
        
        if not url:
            url = App._config['url']

        if not App._config['driver_path']:
            print('ERROR: Driver path not set! Either set manually in '
                  'config.yaml or delete config.yaml and re-run')
            sys.exit()

        App.driver = Chrome(executable_path=App._config['driver_path'], options=opt)
        App.driver.get(App._config['url'])
    

    # <App> ---------------------------------------------------------------- //
    @staticmethod
    def load_session():
        '''Loads saved session, prompting for password if not present'''
        try:
            with open('cookies.pickle', 'rb') as handle:
                cookies = pickle.load(handle)
            for cookie in cookies:
                App.driver.add_cookie(cookie)
            App.driver.get(App._config['url'])
            App.driver.get(App._config['url'])
        except Exception as e:
            App.setup_session()

        # Wait for next page to load to ensure correct login
        WebDriverWait(App.driver, 10).until(
            elements_with_xpath("//span[@role='gridcell']"))

        # dump session
        with open('cookies.pickle', 'wb') as file_handle:
            pickle.dump(App.driver.get_cookies(), file_handle, 
                        protocol=pickle.HIGHEST_PROTOCOL)

    
    # <App> ---------------------------------------------------------------- //
    @staticmethod
    @update
    def setup_session():
        '''Take email and password to establish session'''
        print('No session present, sign in (this should happen rarely):')
        
        if not App._config['email']:
            App._config['email'] = input('Enter school email address: ')
            App._config['password'] = getpass.getpass(prompt='Enter password: ')
            print('Signing in and setting up persistent session...')
        
            email_input = WebDriverWait(App.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='email']")))
            email_input.send_keys(App._config['email'])
            email_input.submit()

        user = App._config['email'].split('@')[0]
        try:
            App.driver.find_element_by_xpath("//input[@id='UserID']").send_keys(user)
        except NoSuchElementException:
            print('Email must be incorrect, please change in yaml file')
            sys.exit()
        pbox = App.driver.find_element_by_xpath("//input[@id='password']")
        pbox.send_keys(App._config['password'])
        pbox.submit()
    
    
    # <App> ---------------------------------------------------------------- //
    @staticmethod
    def get(name):
        return App._config[name]

    '''
    # <App> ---------------------------------------------------------------- //
    @staticmethod
    def set(name, value):
        
        if name in App._setters:
            App._config[name] = value
            #App.update()
        else:
            raise NameError('Name not accepted in set() method')
    '''

if __name__ == "__main__":
    app = App()
