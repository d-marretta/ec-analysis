from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
import pickle


def get_login_cookies_social(url, social_name):
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome()
    driver.get(url)
    while True:
        sleep(6)
        try:
            state=driver.get_cookies()
        except:
            break
    pickle.dump(state,open("auth_"+social_name+".pkl","wb"))
    print(state)

def main():
    get_login_cookies_social('https://www.facebook.com', 'facebook')