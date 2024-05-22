from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
import pickle

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome()
driver.get("https://www.x.com/")
while True:
    sleep(6)
    try:
        state=driver.get_cookies()
    except:
        break
pickle.dump(state,open("auth.pkl","wb"))
print(state)