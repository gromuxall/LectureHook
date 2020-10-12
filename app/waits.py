'''
    waits.py

    Custom Selenium Wait classes
'''

class elements_with_xpath(object):
    '''
    An expectation for checking that a group of elements
    are present

    returns a list of WebElements with the specified xpath
    '''
    def __init__(self, xpath):
        self.xpath = xpath

    def __call__(self, driver):
        elements = driver.find_elements_by_xpath(self.xpath)
        if elements:
            return elements
        return False

class elements_by_length(object):
    '''
    An expectation for checking that elements are present
    and meets a list length requirement

    returns a list of WebElements with the specified xpath
    '''
    def __init__(self, xpath, length):
        self.xpath = xpath
        self.length = length

    def __call__(self, driver):
        elements = driver.find_elements_by_xpath(self.xpath)
        if len(elements) == self.length:
            return elements
        return False
