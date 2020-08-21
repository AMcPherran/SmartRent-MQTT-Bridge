import time
from selenium import webdriver
import asyncio
import os, re

smartrent_email = os.environ.get('SMARTRENT_EMAIL')      
smartrent_password = os.environ.get('SMARTRENT_PASSWORD')

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

# How often to refresh the SmartRent Control page to keep the connection going
page_refresh_interval_seconds = 360

driver = None

def login():
    global driver
    print("Preparing to launch Chrome Webdriver")
    chrome_options = webdriver.ChromeOptions()
    ### Ignore certificate errors because we're MITMing the connection
    chrome_options.add_argument("--ignore-certificate-errors")
    ### Can't be headless because SmartRent will detect and block
    #chrome_options.add_argument('--window-size=1420,1080')
    #chrome_options.add_argument("--headless")
    #chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument(f'user-agent={user_agent}')
    #chrome_options.add_argument('--disable-dev-shm-usage')
    ### Run through the MITM proxy
    chrome_options.add_argument('--proxy-server=127.0.0.1:8080')
    print("Set arguments")
    driver = webdriver.Chrome(options=chrome_options)
    print("Got a webdriver")
    driver.get('https://control.smartrent.com/login/?')
    print("Navigated to SmartRent login page(username)")
    time.sleep(3)
    email_box = driver.find_element_by_xpath('/html/body/main/div/div/div/section/form/div[1]/input')
    email_box.send_keys(smartrent_email)
    email_box.submit()
    time.sleep(3)
    print("Navigated to SmartRent login page(password)")
    password_box = driver.find_element_by_xpath('/html/body/main/div/div/div/section/form/div/input')
    # Enter login credentials
    password_box.send_keys(smartrent_password)
    password_box.submit()
    print("Logged In")
    time.sleep(3)
    driver.get('https://control.smartrent.com/resident')
    return

# Clear Chrome's tmp files so they don't eat your whole disk
def purgeTmp():
    for f in os.listdir('/tmp/'):
        if re.search('/.org.chromium.Chromium.*/', f):
            os.remove(os.path.join('/tmp/', f))

def main():
    time.sleep(10)
    login()
    while True:
        time.sleep(page_refresh_interval_seconds)
        ### Maintain connection by refreshing page
        print("Refreshing page...")
        driver.get('https://control.smartrent.com/resident')
        purgeTmp()
        print("Done.")




if __name__ == "__main__":
    # execute only if run as a script
    main()
