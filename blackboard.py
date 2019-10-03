# -------------------------------------------------------//
#
#   < blackboard.py >
#
#   > Download lecture capture from Blackboard
#
# -------------------------------------------------------//
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import configparser, schedule, time, datetime, csv
import os, os.path, glob

# import config file
config = configparser.ConfigParser()
config.read('courses.ini')

# set options for chrome
chrome_options = Options()
    # set browser to allow multiple simultaneous downloads
prefs = {'profile.default_content_setting_values.automatic_downloads': 1}
    # set download path
moreprefs = {"download.default_directory": config['DOWNLOAD']['path']}

prefs.update(moreprefs)
chrome_options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(config['DRIVER']['path'], options=chrome_options)

os.chdir(config['DOWNLOAD']['path'])

# getToMyCourses ----------------------------------------//
#   traverses the Blackboard menu to find course list,
#     and then clicking chosen course
# -------------------------------------------------------//
def getToMyCourses():
    # Initial get of origin page
    driver.get(config['SITE']['site'])
    driver.maximize_window()

    # Click 'Sign In'
    driver.find_element_by_xpath("//a[@class='btn btn-primary text-center signIn']").click()

    # Enter Credentials
    driver.find_element_by_id('UserID').send_keys(config['LOGIN']['userid'])
    driver.find_element_by_id('password').send_keys(config['LOGIN']['pass'])
    driver.find_element_by_xpath("//button[@type='submit']").click()

    # Click 'My Courses', attempt ten times
    n = 0
    while n < 10: 
        try:
            my_courses = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "My Courses")))
            my_courses.click()
            break;
        except:
            n = n + 1
            time.sleep(1)
# end getToMyCourses()


# getTo341LectureCapture --------------------------------//
#    traverses and loads the lecture capture page
# -------------------------------------------------------//
def getToLectureCapture():
    crs = str(config['CODE']['code1'] + " " + config['COURSE_NUM']['course_num1'])
    
    course = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '" + crs + "')]")))
    course.click()

    iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@name='classic-learn-iframe']"))
        )
    driver.switch_to.frame(iframe)

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//ul[@id='courseMenuPalette_contents']/li/a")))

    lec_cap_link = driver.find_element_by_xpath("//*[contains(text(), 'Lecture Capture')]")
    lec_cap_link.click() 
# end getToLectureCapture()


# switchToFrame -----------------------------------------//
#    switches to new frame for lecture captures
# -------------------------------------------------------//
def switchToFrame():
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//iframe[@id='contentFrame']")))
    driver.switch_to.frame(iframe)
# end switchToFrame()


# appendFileName ----------------------------------------//
#    because files may finish downloading out of order,
#    this will search for a currently downloading file
#    and append to list before another starts downloading
# -------------------------------------------------------//
def appendFileName(cr_list):
    dwnld_ext = 'crdownload'
    all_filenames = [i for i in glob.glob('hd*.{}'.format(dwnld_ext))]
    
    for f in all_filenames:
        newf = f.split('.crdownload')[0]
        if newf not in cr_list:
            cr_list.append(newf)
            print('Appended: ' + newf)


# downloadCaptures --------------------------------------//
#    takes a number to download that specific lecture
#    capture and checks that number against the number
#    of lectures available to download
# -------------------------------------------------------//
def downloadCaptures(csv_num, cr_list):

    # wait for elements to appear
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='class-row']")))
   
    # extract buttons
    media_capture = driver.find_elements_by_xpath("//*[contains(@class, 'courseMediaInd')]")
    num_lec = len(media_capture) - csv_num
    
    if num_lec > 0:
        media_capture[csv_num].click()
        
        WebDriverWait(driver,20).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Download original')]")))
        
        # Needs half a second or it hits view occasionally
        time.sleep(1)

        (driver.find_element_by_xpath("//*[contains(text(), 'Download original')]")).click()
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//select[@name='video-one-files']")))
        
        # select HD version
        select = Select(driver.find_element_by_xpath("//select[@name='video-one-files']"))
        select.select_by_index(1)

        # click download button
        (driver.find_element_by_xpath("//a[@class='btn primary medium downloadBtn']")).click()
        
        # Needs a second to establish this download as created before the other
        time.sleep(2)
        appendFileName(cr_list)

        print('[' + str(csv_num + 1) + '/' + str(len(media_capture)) + '] downloading')
        
        # Recursive call to get next video
        downloadCaptures(csv_num + 1, cr_list)
# end downloadCaptures()


# wait_for_download -------------------------------------//
#    checks for files with extension .crdownload, which
#    indicates that a file is still downloading and
#    sleeps if so
# -------------------------------------------------------//
def waitForDownload(start_num, cr_list):
    dwnld_ext = 'crdownload'
    video_ext = 'mp4'
    crs = config['CODE']['code1'] + config['COURSE_NUM']['course_num1'] + 'lec'

    all_filenames = [i for i in glob.glob('hd*.{}'.format(dwnld_ext))]

    while len(all_filenames) > 0:
        print('Downloads in progress...')

        time.sleep(5)
        all_filenames = [i for i in glob.glob('hd*.{}'.format(dwnld_ext))]

    print('All files downloaded')
    
    all_filenames = [i for i in glob.glob('hd*.{}'.format(video_ext))]

    for i in range(0, len(cr_list)):
        crs_str = str(crs + f'{(i + start_num + 1):02}' + '.' + video_ext)
        os.rename(cr_list[i], crs_str) 
# end waitForDownload()



# - main() ----------------------------------------------//

cr_list = list()
curr_lecs = len([i for i in glob.glob('*.{}'.format('mp4'))])

getToMyCourses()
getToLectureCapture()
switchToFrame()
downloadCaptures(curr_lecs, cr_list)
waitForDownload(curr_lecs, cr_list)

