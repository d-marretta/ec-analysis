import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from selenium.webdriver.common.by import By
import pickle
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from string import punctuation
from os import listdir
from os.path import isfile

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
    try:
        username = driver.find_element(By.XPATH, '//h3//a').text
    except NoSuchElementException:
        print('Could not find username, skipping post; Url: ' + url)
        return None
    
    try:
        post_date_str = driver.find_element(By.XPATH, '//footer//abbr').text
    except NoSuchElementException:
        print('Could not find date; Url: ' + url)
        post_date_str = ""

    if post_date_str:
        post_date_str = parse_date_str(post_date_str)

    # Get all the text of the post
    try:
        text_ps = driver.find_elements(By.XPATH, '//p')
    except NoSuchElementException:
        print('Could not find text; Url: ' + url)

    text = ""
    if text_ps:
        for p in text_ps:
            text += p
        
    
    post = {
        'id':url.split('&eav')[0],
        'url':url,
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

def get_full_urls(driver, max_posts, post_ids):
    full_post_urls = []
    url_counter = 0
    while True:
        post_containers = driver.find_elements(By.XPATH, '//article')
        for container in post_containers:
            if url_counter >= max_posts:
                print(f'\nCollected {url_counter} urls')
                return full_post_urls
            
            full_post_url = get_full_post_url(container)
            if full_post_url and (full_post_url.split('&eav')[0] not in post_ids):
                full_post_urls.append(full_post_url)
                url_counter += 1
        try:
            next_results_url = driver.find_element(By.XPATH, '//div[@id="see_more_pager"]/a').get_attribute('href')
        except NoSuchElementException:
            print(f'\nCollected {url_counter} urls')
            return full_post_urls
        
        sleep(3)
        driver.get(next_results_url)


def search_posts(driver, url, query, max_posts, post_ids, nfiles):

    # Allow the page to load
    driver.get(url)
    sleep(5)

    print(f'Page url: {url}')
    print(f'Keyword: {query}\n')

    post_counter = 0
    post_datas = []   # List of dicts, each dict will be data of a post
    session_urls = []
    full_post_urls = get_full_urls(driver, max_posts, post_ids)
    
    for url in full_post_urls:
        driver.get(url)
        sleep(10)
        post_data = get_post_data(driver, url, query)
            
        if post_data:
            #if
            post_datas.append(post_data)
            post_counter += 1
            print(f'\rGot {post_counter} post(s) out of {max_posts}', end="")

    print()
    for data in post_datas:
        with open('facebook_posts/post_'+str(nfiles)+'.json', mode='w', encoding='utf-8') as outjson:
            json.dump(data, outjson, indent=2)
        nfiles += 1


def get_urls_set(d):
    post_ids = set()
    nfiles = 0

    for file in listdir(d):
        full_path = d+'/'+file
        if isfile(full_path):
            with open(full_path, 'r', encoding='utf-8') as post_json:
                post_data = json.load(post_json)
                id = post_data["id"].split('&eav')[0]
                post_ids.add(id)
            nfiles += 1
    return nfiles, post_ids

def setup():
    # Start chrom webdriver
    options = Options()
    #options.add_argument('--headless')
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
    driver.maximize_window()

    sleep(2)
    print('Scraping started')

    return driver

def main(): 
    load_dotenv()
    POSTS_DIR = './facebook_posts'
    driver = setup()

    nfiles, post_ids = get_urls_set(POSTS_DIR)
    print('Already collected: '+str(nfiles)+' files')

    keywords = ['Citizen Energy Communities','Renewable Energy Cooperatives','Energy Cooperatives','Energy communities','Community energy projects','Local energy initiatives','Renewable energy cooperatives','Community-owned energy','Distributed energy resources','Energy sharing schemes']
    for keyword in keywords:
        url = urllib.parse.quote(string=f"https://mbasic.facebook.com/search/top/?q={keyword}", safe='/&?=:')
        search_posts(driver, url, keyword, 300, post_ids, nfiles)

        url = urllib.parse.quote(string=f"https://mbasic.facebook.com/search/posts/?q={keyword}", safe='/&?=:')
        search_posts(driver, url, keyword, 300, post_ids, nfiles)
    
    driver.close()

main()

    


