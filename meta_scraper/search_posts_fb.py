import sys
sys.path.append('/home/daniele/Documents/Thesis/utils')

import urllib.parse
from selenium import webdriver
from selenium.webdriver.common import action_chains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common import keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException,StaleElementReferenceException, TimeoutException
from time import sleep
from selenium.webdriver.common.by import By
import pickle
from dotenv import load_dotenv
import json
import utils
import dateparser
from datetime import datetime

SCROLL_AMOUNT = 4000


def parse_date_str(date):
    settings = {
        'RELATIVE_BASE': datetime.today().replace(minute=0, hour=23, second=0, microsecond=0)
    }
    parsed_date = ''
    if 'at' in date:
        parsed_date = str(dateparser.parse(date.replace(' at', ''), languages=['en'], settings=settings))
    else:
        parsed_date = str(dateparser.parse(date, languages=['en'], settings=settings))
    
    if parsed_date == 'None':
        return date
    
    return parsed_date



def get_post_data(driver, container, query):
    username = ''
    date = ''
    text = ''
    mentions = set()
    hashtags = set()

    retry_stale = True
    try:
        while retry_stale:
            username_and_groups = container.find_elements(By.XPATH, './/div[@data-type="text"]/div[@class="native-text"]/span[@class="rtl-ignore f2 a" and @style="color:#050505;"]')
            try:
                for i,name_span in enumerate(username_and_groups):
                    if i == 0:
                        username = name_span.text.strip()
                    else:
                        mentions.add(name_span.text.strip())
                retry_stale=False
            except StaleElementReferenceException:
                continue
    except StaleElementReferenceException:
        return None, True
    except NoSuchElementException:
        return None, False

    
    try:
        date = container.find_element(By.XPATH, './/div[@data-type="text"]/div[@class="native-text"]/span[@class="f5" and @style="color:#8a8d91;"]').text[:-2]
        if date == 'Sponsored':
            return None,False
    except NoSuchElementException:
        pass
    except StaleElementReferenceException:
        return None,True

    parsed_date = parse_date_str(date)

    try:
        see_more = container.find_element(By.XPATH, './/div[@data-type="text"]/div[@class="native-text" and @style="color:#050505;"]/span[@style="color:#65676b;" and contains(text(), "See more")]/../..')
        #WebDriverWait(driver, 20).until_not(expected_conditions.presence_of_element_located((By.XPATH,'.//div[@data-type="text"]/div[@class="native-text" and @style="color:#050505;"]/span[@style="color:#65676b;" and contains(text(), "See more")]')))
        driver.execute_script("arguments[0].click();",see_more)
        sleep(5)
        return None,True
    except NoSuchElementException:
        pass
    except StaleElementReferenceException:
        return None,True


    try:
        retry_stale = True
        while retry_stale:
            text_div = container.find_element(By.XPATH, './/div[@data-type="text"]/div[@class="native-text" and @style="color:#050505;"]')
            try:
                text = text_div.text
                retry_stale = False
            except StaleElementReferenceException:
                continue
    except NoSuchElementException:
        return None, False

    try:
        #tag_spans = container.find_elements(By.XPATH, './/div[@data-type="text"]/div[@class="native-text" and @style="color:#050505;"]/span[@class="f2 a" and @style="color:#1763cf;"]')
        tag_spans = WebDriverWait(container,2,ignored_exceptions=(StaleElementReferenceException)).until(expected_conditions.presence_of_all_elements_located((By.XPATH, './/div[@data-type="text"]/div[@class="native-text" and @style="color:#050505;"]/span[@class="f2 a" and @style="color:#1763cf;"]')))
        for tag in tag_spans:
            tag_text = tag.text
            if '/' in tag_text or '.' in tag_text or 'https' in tag_text:
                continue
            elif tag_text.startswith("#"):
                hashtags.add(tag_text.strip())
            else:
                mentions.add(tag_text.strip())
                
    except NoSuchElementException:
        pass

    except TimeoutException:
        pass


    post = {
        'id':username+text,
        'keyword':query,
        'username':username,
        'date':parsed_date,
        'text':text,
        'mentions':list(mentions),
        'hashtags':list(hashtags)
    }

    # print(post)
    return post, False

def click_posts(driver):
    posts_button = driver.find_element(By.XPATH, '//div[@role="button" and @aria-label="Posts"]')
    posts_button.click()


def search_posts(driver, save_dir, url, query, max_posts, post_ids, starting_n, ac):

    # Allow the page to load
    driver.get(url)
    sleep(5)

    click_posts(driver)

    sleep(4)

    print(f'Page url: {url}')
    print(f'Keyword: {query}\n')

    post_counter = 0
    post_datas = []   # List of dicts, each dict will be data of a post
    session_ids = set()

    scrolling = True
    last_position = 0  # Current scroll amount
    height = 0         # Height to scroll to

    already_seen = 0
    skipped = 0

    scrolling_elem = driver.find_element(By.XPATH, '//div[@class="m vscroller"]')
    sleep(1)

    while True:
        containers = driver.find_elements(By.XPATH, '//div[contains(@class, "m") and contains(@class, "displayed")]')
        for container in containers:
            post_data, see_more_pressed = get_post_data(driver, container, query)
            if see_more_pressed:
                continue
            if post_data:
                id = post_data['id']
                if (id not in session_ids) and (id not in post_ids):
                    session_ids.add(id)
                    post_datas.append(post_data)
                    post_counter += 1
                    with open(save_dir+'/post_'+str(starting_n)+'.json', mode='w', encoding='utf-8') as outjson:
                        json.dump(post_data, outjson, indent=2)
                    starting_n += 1
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

        height += SCROLL_AMOUNT
        last_position, scrolling = scroll(driver=driver,height=height,max_attempts=2, last_pos=last_position, scroller=scrolling_elem, ac=ac)
        if not scrolling:
            print(f'\nCollected {post_counter} posts')
            break   

    print()        
    
    return post_counter, session_ids

def scroll(driver, height, max_attempts, last_pos, scroller, ac):
    # Try scrolling multiple times, in case the page has to load
    attempt = 0
    curr_pos = 0
    while attempt < max_attempts:
        try:
            driver.execute_script(f'arguments[0].scrollTo(0, {height})', scroller)
            sleep(1)
            curr_pos = driver.execute_script("return arguments[0].scrollTop", scroller)
            if last_pos == curr_pos or (abs(curr_pos-last_pos) < 10):
                ac.move_by_offset(0,-925)
                ac.click_and_hold().perform()
                sleep(15)
                ac.release().perform()

                ac.move_by_offset(0,925)
                ac.click_and_hold().perform()
                sleep(15)
                ac.release().perform()
                attempt += 1
            else:
                # Return new last_position, new height to scroll to and 
                # whether scrolling is still true or false
                return curr_pos,True
        except StaleElementReferenceException:
            scroller = driver.find_element(By.XPATH, '//div[@class="m vscroller"]')

    return curr_pos,False

def setup():
    # Start chrom webdriver
    options = Options()
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19')
    driver = webdriver.Chrome(options=options)
    driver.get("https://m.facebook.com/")

    # Get logins cookies
    cookies = pickle.load(open("../auth_facebook.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://m.facebook.com/")

    driver.implicitly_wait(2)
    driver.maximize_window()

    sleep(3)
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

    ac = action_chains.ActionChains(driver)
    ac.move_by_offset(1661,980)

    for keyword in keywords:
        keyword = keyword.lower().strip()
        url = urllib.parse.quote(string=f"https://m.facebook.com/search_results/?q={keyword}", safe='/&?=:')
        n_posts, new_ids = search_posts(driver, POSTS_DIR, url, keyword, 250, post_ids, starting_n, ac)
        starting_n += n_posts
        post_ids.update(new_ids)
    
    driver.close()

if __name__ == '__main__':
    main()