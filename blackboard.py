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
def getToLectureCapture(i_num):
    crs = str(config['CODE']['code' + str(i_num)] + " " + config['NUM']['num' + str(i_num)])
       
    # clicks link to specific course
    course = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '" + crs + "')]")))
    course.click()

    # changes frame
    iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[@name='classic-learn-iframe']"))
        )
    driver.switch_to.frame(iframe)

    # waits for side menu to appear
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//ul[@id='courseMenuPalette_contents']/li/a")))

    # clicks Lecture Capture link in side menu
    lec_cap_link = driver.find_element_by_xpath("//*[contains(text(), 'Lecture Capture')]")
    lec_cap_link.click()
# end getToLectureCapture()


# timePage ----------------------------------------------//
#    navigates through time page if present 
# -------------------------------------------------------//
def timePage(t):
    course_time = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '" + t + "')]")))
    course_time.click()
# end timePage()


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
    all_filenames = [i for i in glob.glob('hd*.{}'.format('crdownload'))]
    
    for f in all_filenames:
        newf = f.split('.crdownload')[0]
        if newf not in cr_list:
            cr_list.append(newf)


# downloadCaptures --------------------------------------//
#    takes a number to download that specific lecture
#    capture and checks that number against the number
#    of lectures available to download
# -------------------------------------------------------//
def downloadCaptures(num, cr_list):

    # wait for elements to appear
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='class-row']")))
   
    # extract buttons
    media_capture = driver.find_elements_by_xpath("//*[contains(@class, 'courseMediaInd')]")
    num_lec = len(media_capture) - num
    
    if num_lec > 0:
        media_capture[num].click()
        
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

        print('[' + str(num + 1) + '/' + str(len(media_capture)) + '] downloading')
        
        # Recursive call to get next video
        downloadCaptures(num + 1, cr_list)
# end downloadCaptures()


# waitForDownload ---------------------------------------//
#    checks for files with extension .crdownload, which
#    indicates that a file is still downloading and
#    sleeps if so
# -------------------------------------------------------//
def waitForDownload(start_num, cr_list, i_num):
    all_filenames = [i for i in glob.glob('hd*.{}'.format('crdownload'))]

    while len(all_filenames) > 0:
        print('Downloads in progress...')
        time.sleep(5)
        all_filenames = [i for i in glob.glob('hd*.{}'.format('crdownload'))]

    print('All files downloaded')
# end waitForDownload()


# renameFiles -------------------------------------------//
#    rename files based on generated course code and number
# -------------------------------------------------------//
def renameFiles(start_num, cr_list, i_num):
    crs = config['CODE']['code' + str(i_num)] + config['NUM']['num' + str(i_num)] + 'lec'

    for i in range(0, len(cr_list)):
        crs_str = str(crs + f'{(i + start_num + 1):02}' + '.mp4')
        os.rename(cr_list[i], crs_str) 

    print('All files renamed')
# end renameFiles()
    

# wait_for_download -------------------------------------//
#    checks for files with extension .crdownload, which
#    indicates that a file is still downloading and
#    sleeps if so
# -------------------------------------------------------//
def displayMenu():
    i = 1

    print("\n~-------------")
    print("  Lecture Capture Scraper")
    print("\n~-------------")

    while config['NUM']['num' + str(i)]:
        course = config['CODE']['code' + str(i)] + ' ' + config['NUM']['num' + str(i)]
        print('(' + str(i) + ') ' + course)
        i = i + 1
    
    print('Course choice: ', end=' ')
    i_num = input()
    print('Downloading lectures from ' + config['CODE']['code' + str(i_num)] + ' ' + config['NUM']['num' + str(i_num)])
    return i_num
# end displayMenu()


# main() ------------------------------------------------//

# display menu and get course choice
i_num = displayMenu()

# configure options for chrome
chrome_options = Options()
# set browser to allow multiple simultaneous downloads
prefs = {'profile.default_content_setting_values.automatic_downloads': 1}
# set download path
moreprefs = {"download.default_directory": config['PATHS']['dwn' + str(i_num)]}
prefs.update(moreprefs)
chrome_options.add_experimental_option("prefs", prefs)

# list of file names
cr_list = list()

# if a time for lecture captures must be specified
course_time = config['TIME']['time' + str(i_num)]

# launch webdriver
driver = webdriver.Chrome(config['PATHS']['driver'], options=chrome_options)

# change current working directory
os.chdir(config['PATHS']['dwn' + str(i_num)])

# check current number of lecture videos in folder
curr_lecs = len([i for i in glob.glob('*.{}'.format('mp4'))])

print("Downloading to " + os.getcwd())

getToMyCourses()
getToLectureCapture(i_num)

if course_time:
    timePage(course_time)

switchToFrame()
downloadCaptures(curr_lecs, cr_list)
waitForDownload(curr_lecs, cr_list, i_num)
renameFiles(curr_lecs, cr_list, i_num)

driver.quit()
