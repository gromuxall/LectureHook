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
    @slow_down
    def download(self):
        """
        Clicks and selects quality, then downloading video
        """
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

        # select HD version TODO: give choice for sd or hd
        #                   TODO: have this select be the webdriverwait above
        select = Select(DRIVER.find_element_by_xpath(
            "//select[@name='video-one-files']"
        ))
        select.select_by_index(1)

        options = DRIVER.find_elements_by_xpath("//option")
        print(options[1].text)

        btn = DRIVER.find_element_by_xpath(
            "//a[@class='btn primary medium downloadBtn']"
        ).get_attribute('href')

        
        #res = DRIVER.request('HEAD', btn)
        #print(res.headers)

        DRIVER.find_element_by_xpath(
            "//a[@class='btn primary medium downloadBtn']"
        ).click()


