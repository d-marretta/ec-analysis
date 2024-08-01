import sys

sys.path.append('/home/daniele/Documents/Thesis/utils')

import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
import pickle
from dotenv import load_dotenv
import json
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import utils

SCROLL_AMOUNT=700

def get_tweet_data(container, query):
    try:
        username = container.find_element(By.XPATH, './/div[@data-testid="User-Name"]//span[not(contains(text(), "@"))]').text
    except:
        username = ""


    try:    
        tag = container.find_element(By.XPATH, './/div[@data-testid="User-Name"]//span[contains(text(), "@")]').text
    except:
        tag = ""

    try:
        tweet_date = container.find_element(By.XPATH, './/time').get_attribute('datetime')
    except:
        tweet_date = ""
        
    if not tag or not tweet_date:
        return {}
    
    # Get all the text of the tweet
    retry_stale = True
    while retry_stale:
        text_spans = container.find_elements(By.XPATH, './/div[@data-testid="tweetText"]//span')
        text = ""
        try:
            for span in text_spans:
                text += span.text
            retry_stale = False
        except StaleElementReferenceException:
            continue
    
    tweet = {
        'id':(tag+tweet_date),
        'keyword':query,
        'username':username,
        'tag':tag,
        'date':tweet_date,
        'text':text
    }

    # print(tweet)
    return tweet


def search_tweets(driver, query, max_tweets, save_dir, seen_ids, starting_n):
    # Allow the page to load
    url = urllib.parse.quote(string=f"https://x.com/search?q={query}&src=typed_query", safe='/&?=:')
    driver.get(url)
    time.sleep(10)

    print(f'Page url: {url}')
    print(f'Keyword: {query}\n')

    tweet_counter = 0
    tweet_ids = set()  # Current session of tweet ids
    tweet_datas = []   # List of dicts, each dict will be data of a tweet
    scrolling = True
    last_position = 0  # Current scroll amount
    height = 0         # Height to scroll to
    
    skipped = 0
    already_seen = 0

    while scrolling:
        tweet_containers = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        for container in tweet_containers:
            tweet_data = get_tweet_data(container=container, query=query)
            if tweet_data:
                tweet_id = tweet_data['id']

                # Check if the document is already in the db or in the ids list of current scraping session
                if (tweet_id not in tweet_ids) and (tweet_id not in seen_ids):
                    tweet_ids.add(tweet_id)
                    tweet_datas.append(tweet_data)
                    tweet_counter += 1
                    print(f'\rGot {tweet_counter} tweet(s) out of {max_tweets}; Skipped: {skipped}; Already seen: {already_seen}', end="")
                else:
                    already_seen += 1

            else:
                skipped += 1

            if tweet_counter >= max_tweets:
                break

        if tweet_counter >= max_tweets:
            print(f'\nCollected {tweet_counter} tweets')
            break

        # Scroll and update last position, scrolling flag and height to scroll to
        height += SCROLL_AMOUNT
        last_position, scrolling = utils.scroll(driver=driver,height=height,max_attempts=4, last_pos=last_position)
        if not scrolling:
            print(f'\nCollected {tweet_counter} tweets')
    
    time.sleep(5)
    
    for data in tweet_datas:
        with open(save_dir+'/tweet_'+str(starting_n)+'.json', mode='w', encoding='utf-8') as outjson:
            json.dump(data, outjson, indent=2)
        starting_n += 1

    return tweet_counter, tweet_ids


def setup():
    # Start chrom webdriver
    options = Options()
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.x.com/")

    # Get logins cookies
    cookies = pickle.load(open("../auth_x.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://www.x.com/")

    driver.implicitly_wait(2)
    time.sleep(1)
    driver.maximize_window()

    print('Scraping started')
    return driver

def main():
    load_dotenv()
    TWEETS_DIR = '../twitter_data/tweets'
    KEYWORDS_DIR = '..'
    driver = setup()
    starting_n, seen_ids = utils.get_ids_set(TWEETS_DIR)
    print('Already collected: '+str(starting_n)+' files')

    keywords = utils.get_keywords(KEYWORDS_DIR)

    curr_n = starting_n
    for keyword in keywords:
        retry = True
        n_tweets, new_tweet_ids = search_tweets(driver, keyword.lower(), 400, TWEETS_DIR, seen_ids, curr_n)
        if n_tweets == 0 and retry:
            time.sleep(120)
            retry = False
            n_tweets, new_tweet_ids = search_tweets(driver, keyword.lower(), 400, TWEETS_DIR, seen_ids, curr_n)

        curr_n += n_tweets
        seen_ids.update(new_tweet_ids)

    driver.close()

if __name__ == '__main__':
    main()