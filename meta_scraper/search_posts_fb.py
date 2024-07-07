import sys
sys.path.append('/home/daniele/Documents/Thesis/utils')

import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException,StaleElementReferenceException
from time import sleep
from selenium.webdriver.common.by import By
import pickle
from dotenv import load_dotenv
import json
import utils
import base64
import pytesseract
from PIL import Image
import cv2
import numpy as np
from string import punctuation
import dateparser
from datetime import datetime

SCROLL_AMOUNT = 800


def parse_date_str(date):
    settings = {
        'RELATIVE_BASE': datetime.today().replace(minute=0, hour=23, second=0, microsecond=0)
    }
    parsed_date = ''
    if 'at' in date:
        parsed_date = str(dateparser.parse(date.replace(' at', ''), languages=['en'], settings=settings))
    else:
        parsed_date = str(dateparser.parse(date, languages=['en'], settings=settings))
    
    return parsed_date


def get_date_str(driver, canvas):
    canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(22);",canvas)

    canvas_png = base64.b64decode(canvas_base64)

    with open('date.png', 'wb') as f:
        f.write(canvas_png)
    
    img = cv2.imread('date.png')

    white = np.full(img.shape, 255, dtype=np.uint8)

    # Create a mask to identify black pixels
    black_mask = cv2.inRange(img, lowerb=np.array([0, 0, 0]), upperb=np.array([0, 0, 0]))

    # Change black pixels to white using bitwise operations
    img = cv2.bitwise_or(white, white, mask=black_mask)

    # Resize and add border
    img = cv2.copyMakeBorder(img, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    result = cv2.resize(img,None,fx=3, fy=3, interpolation = cv2.INTER_CUBIC)

    cv2.imwrite('date.png', result)
    
    return pytesseract.image_to_string(Image.open('date.png'))



def get_hashtags_from_text(text):
    exclude = set(punctuation.replace('#','').replace('@',''))
    clean_text = ''
    for ch in text:
        if ch in exclude:
            clean_text += ' '
        else:
            clean_text += ch

    hashtags = set()
    mentions = set()
    words = clean_text.split()
    for word in words:
        if word.startswith('@'):
            cont_mentions = word.strip()[1:].split('@')
            for ment in cont_mentions:
                if ment:
                    mentions.add(f'@{ment}')

        elif word.startswith('#'):
            cont_hashtags = word.strip()[1:].split('#')
            for hash in cont_hashtags:
                if hash:
                    hashtags.add(f'#{hash.lower()}')
    
    return hashtags, mentions


def get_post_data(driver, container, query):
    username= ''

    # Try get normal username
    try:
        retry_stale = True
        attempts = 0
        while retry_stale and attempts <= 5:
            attempts += 1
            try:
                username = container.find_element(By.XPATH, './/h3//strong').text
                retry_stale = False
            except StaleElementReferenceException:
                continue


    except NoSuchElementException:
        username = ''
    
    # If it doesn't work try username of group
    if not username:
        try:
            retry_stale = True
            attempts = 0
            while retry_stale and attempts <= 5:
                attempts += 1
                try:
                    username = container.find_element(By.XPATH, './/h3//a[contains(@href, "groups")]/span').text
                    retry_stale = False
                except StaleElementReferenceException:
                    continue

        except NoSuchElementException:
            return None
    
    if not username:
        return None
    
    try:
        canvas = None
        retry_stale = True
        attempts = 0
        while retry_stale and attempts <= 5:     
            attempts += 1
            try:
                canvas = container.find_element(By.XPATH, './/canvas')
                retry_stale = False
            except StaleElementReferenceException:
                continue

        if canvas:
            post_date_str = get_date_str(driver, canvas)
        else:
            return None

    except NoSuchElementException:
        return None

    post_date_str = parse_date_str(post_date_str)

    # Get all the text and tags of the post
    mentions = set()
    try:
        text_div = container.find_element(By.XPATH, './/div[@data-ad-preview="message" or @data-ad-comet-preview="message"]')

        try:
            altro_button = text_div.find_element(By.XPATH, './/div[@role="button" and contains(text(), "See more")]')
            altro_button.click()
        except NoSuchElementException:
            altro_button = None

        text_div = container.find_element(By.XPATH, './/div[@data-ad-preview="message" or @data-ad-comet-preview="message"]')
        
        try:
            tags_spans = text_div.find_elements(By.XPATH, './/a[@role="link"]/span')
            for tag in tags_spans:
                mentions.add(tag.text)

        except NoSuchElementException:
            mentions = set()

        text = text_div.text

    except NoSuchElementException:
        return None
        
    hashtags, at_mentions = get_hashtags_from_text(text)
    if at_mentions:
        mentions.update(at_mentions)

    post = {
        'id':username+post_date_str+str(len(text)),
        'keyword':query,
        'username':username,
        'date':post_date_str,
        'text':text,
        'mentions':list(mentions),
        'hashtags':list(hashtags)
    }

    # print(post)
    return post



def search_posts(driver, save_dir, url, query, max_posts, post_ids, starting_n):

    # Allow the page to load
    driver.get(url)
    sleep(5)

    print(f'Page url: {url}')
    print(f'Keyword: {query}\n')

    post_counter = 0
    post_datas = []   # List of dicts, each dict will be data of a post
    session_ids = set()

    height = 0
    last_position = 0
    scrolling = True

    already_seen = 0
    skipped = 0

    while scrolling:
        containers = driver.find_elements(By.XPATH, '//div[@style="border-radius: max(0px, min(var(--card-corner-radius), calc((100vw - 4px - 100%) * 9999))) / var(--card-corner-radius);"]')
        for container in containers:
            post_data = get_post_data(driver, container, query)
                
            if post_data:
                id = post_data['id']
                if (id not in session_ids) and (id not in post_ids):
                    session_ids.add(id)
                    post_datas.append(post_data)
                    post_counter += 1
                    print(f'\rGot {post_counter} post(s) out of {max_posts}; Skipped: {skipped}; Already seen: {already_seen}', end="")
                else:
                    already_seen += 1
            else:
                skipped += 1
        
            if post_counter >= max_posts:
                break

        if post_counter >= max_posts:
            print(f'\nCollected {post_counter} posts')
            break

         # Scroll and update last position, scrolling flag and height to scroll to
        height += SCROLL_AMOUNT
        last_position, scrolling = utils.scroll(driver=driver,height=height,max_attempts=4, last_pos=last_position)
        if not scrolling:
            print(f'\nCollected {post_counter} posts')

    print()

    sleep(5)

    for data in post_datas:
        with open(save_dir+'/post_'+str(starting_n)+'.json', mode='w', encoding='utf-8') as outjson:
            json.dump(data, outjson, indent=2)
        starting_n += 1
    
    return post_counter, session_ids



def setup():
    # Start chrom webdriver
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.facebook.com/")

    # Get logins cookies
    cookies = pickle.load(open("../auth_facebook.pkl", "rb"))
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
    POSTS_DIR = '../facebook_posts'
    KEYWORDS_DIR = '..'
    driver = setup()

    starting_n, post_ids = utils.get_ids_set(POSTS_DIR)
    print('Already collected: '+str(starting_n)+' files')

    keywords = utils.get_keywords(KEYWORDS_DIR)
    
    for keyword in keywords:
        keyword = keyword.lower().strip()
        keyword = 'energy communities'

        # url = urllib.parse.quote(string=f"https://www.facebook.com/search/posts/?q={keyword}", safe='/&?=:')
        # n_posts, new_ids = search_posts(driver, POSTS_DIR, url, keyword, 15, post_ids, starting_n)
        # starting_n += n_posts
        # post_ids.update(new_ids)

        url = urllib.parse.quote(string=f"https://www.facebook.com/search/top?q={keyword}", safe='/&?=:')
        n_posts, new_ids = search_posts(driver, POSTS_DIR, url, keyword, 1, post_ids, starting_n)
        starting_n += n_posts
        post_ids.update(new_ids)
    
    driver.close()

if __name__ == '__main__':
    main()