import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
from selenium.webdriver.common.by import By
import pickle
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import string

def parse_date_str(date):
    date_l = date.split(" ")
    months = ['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre']
    if date_l[1].lower() not in months:
        if date_l[0].lower() == 'ieri':
            yesterday = datetime.now() - timedelta(1)
            date_str = datetime.strftime(yesterday, '%d-%m-%y')
            return date_str
        else:
            today = datetime.today().strftime('%d-%m-%y')
            return today
    month_num = 0
    for i, month in enumerate(months):
        if date_l[1].lower() == month:
            month_num = '0'+str(i+1) if (i+1) <= 9 else str(i+1)
    
    try:
        year = str(int(date_l[2]))[2:]
    except ValueError:
        year = datetime.today().strftime("%y")

    day_num = '0'+date_l[0] if int(date_l[0]) <= 9 else date_l[0]
    date_str = day_num+'-'+month_num+'-'+year
    return date_str

def get_post_data(driver, url, query):
    
    username = driver.find_element(By.XPATH, '//h3//a').text
    post_date_str = driver.find_element(By.XPATH, '//footer//abbr').text
    post_date_str = parse_date_str(post_date_str)

    # Get all the text of the post
    text_ps = driver.find_elements(By.XPATH, '//p')
    text = ""
    for p in text_ps:
        filtered_p = "".join(filter(lambda s: s.isalnum() or s.isspace() or (s in string.punctuation), p.text))
        text += filtered_p
        
    
    post = {
        'id':url,
        'keyword':query,
        'username':username,
        'date':post_date_str,
        'text':text
    }

    # print(post)
    return post

def get_full_post_url(container):
    try:
        url = container.find_element(By.XPATH, './/a[contains(text(), "Notizia completa")]').get_attribute('href')
    except NoSuchElementException:
        url = ""
    return url

def get_full_urls(driver, max_posts):
    full_post_urls = []
    url_counter = 0
    while True:
        post_containers = driver.find_elements(By.XPATH, '//article')
        for container in post_containers:
            if url_counter >= max_posts:
                print(f'\nCollected {url_counter} urls')
                return full_post_urls
            
            full_post_url = get_full_post_url(container)
            if full_post_url:
                full_post_urls.append(full_post_url)
                url_counter += 1
        next_results_url = driver.find_element(By.XPATH, '//div[@id="see_more_pager"]/a').get_attribute('href')
        driver.get(next_results_url)
        time.sleep(1)


def search_posts(query, max_posts):
    # Start chrom webdriver
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.facebook.com/")

    # Get logins cookies
    cookies = pickle.load(open("auth_facebook.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://www.facebook.com/")

    driver.implicitly_wait(2)
    time.sleep(1)

    # Allow the page to load
    url = urllib.parse.quote(string=f"https://mbasic.facebook.com/search/posts/?q={query}", safe='/&?=:')
    driver.get(url)
    driver.maximize_window()
    time.sleep(3)

    print('Scraping started')
    print(f'Page url: {url}')
    print(f'Keyword: {query}\n')

    post_counter = 0
    post_datas = []   # List of dicts, each dict will be data of a post

    full_post_urls = get_full_urls(driver, max_posts)
    
    for url in full_post_urls:
        driver.get(url)
        time.sleep(1)
        post_data = get_post_data(driver, url, query)
            
        if post_data:
            # Check if the document is already in the db or in the ids list of current scraping session
            post_datas.append(post_data)
            post_counter += 1
            print(f'\rGot {post_counter} post(s) out of {max_posts}', end="")

    print()
    for i, data in enumerate(post_datas):
        with open('facebook_posts/post_'+str(i)+'.json', mode='w', encoding='utf-8') as outjson:
            json.dump(data, outjson, indent=2)

    driver.close()


def main():
    # Connect to database
    load_dotenv()

    search_posts('energy communities', 10)

main()

    


