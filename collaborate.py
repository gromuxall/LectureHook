'''
Functions to scrape off Blackboard collaborate
'''

'''
# -------------------------------------------------------------------------- //
def switch_to_frame():
    """
    Switches frames. Annoying.
    """
    iframe = WebDriverWait(DRIVER, 30).until(
        EC.presence_of_element_located((By.XPATH,\
                "//iframe[@class='classic-learn-iframe']"))
        )
    DRIVER.switch_to.frame(iframe)


# -------------------------------------------------------------------------- //
def launch_page_collab():
    # Initial get of origin page
    DRIVER.get('https://uic.blackboard.com')
    DRIVER.maximize_window()

    # Click 'Sign In'
    DRIVER.find_element_by_xpath("//a[@class='btn btn-primary text-center signIn']").click()

    # Enter credentials
    DRIVER.find_element_by_id('UserID').send_keys(CONFIG['LOGIN']['userid'])
    DRIVER.find_element_by_id('password').send_keys(CONFIG['LOGIN']['pass'])
    DRIVER.find_element_by_xpath("//button[@type='submit']").click()
    print(MESSAGES['sign_in'])

    # Click 'My Courses', attempt ten times
    tries = 0
    while tries < 10:
        try:
            my_courses = WebDriverWait(DRIVER, 30).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "My Courses"))
            )
            my_courses.click()
            break
        except:
            tries = tries + 1
            time.sleep(1)


# -------------------------------------------------------------------------- //
def choose_course():
    #time.sleep(10)
    WebDriverWait(DRIVER, 30).until(
        EC.element_to_be_clickable((By.XPATH,\
            "//div[contains(@id, 'course-list')]"))
        )

    courses = DRIVER.find_elements_by_xpath(\
        "//a[@analytics-id='base.courses.courseCard.courseLink.link']"
        )

    # print list of courses
    for idx, crs in enumerate(courses, 1):
        print(idx, ') ', crs.find_element_by_xpath("//h4").text)

    # prompt for input
    choice = input('Choose course >> ')

    courses[int(choice) - 1].click()
'''
