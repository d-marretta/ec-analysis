import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
import pickle
from dotenv import load_dotenv
import os
import json

SCROLL_AMOUNT=800

def get_tweet_data(container, query):
    
    username = container.find_element(By.XPATH, './/div[@data-testid="User-Name"]//span[not(contains(text(), "@"))]').text
    tag = container.find_element(By.XPATH, './/div[@data-testid="User-Name"]//span[contains(text(), "@")]').text
    tweet_date = container.find_element(By.XPATH, './/time').get_attribute('datetime')

    if not tag or not tweet_date:
        print("Couldn't get tag and/or post date, skipping tweet...")
        return {}
    
    # Get all the text of the tweet
    text_spans = container.find_elements(By.XPATH, './/div[@data-testid="tweetText"]//span')
    text = ""
    for span in text_spans:
        text += span.text
    
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

def scroll(driver, height, max_attempts, last_pos):
    # Try scrolling multiple times, in case the page has to load
    attempt = 0
    curr_pos = 0
    while attempt < max_attempts:
        driver.execute_script(f'window.scrollTo(0, {height})')
        time.sleep(0.5)
        curr_pos = driver.execute_script("return window.scrollY")
        if last_pos == curr_pos:
            # No scrolling happened, try again
            time.sleep(1)
        else:
            # Return new last_position, new height to scroll to and 
            # whether scrolling is still true or false
            return curr_pos,True
    
    return curr_pos,False

def search_tweets(query, max_tweets, save_dir, seen_ids, starting_n):
    # Start chrom webdriver
    options = Options()
    options.add_argument('--headless')
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

    # Allow the page to load
    url = urllib.parse.quote(string=f"https://x.com/search?q={query}&src=typed_query", safe='/&?=:')
    driver.get(url)
    driver.maximize_window()
    time.sleep(3)

    print('Scraping started')
    print(f'Page url: {url}')
    print(f'Keyword: {query}\n')

    tweet_counter = 0
    tweet_ids = set()  # Current session of tweet ids
    tweet_datas = []   # List of dicts, each dict will be data of a tweet
    scrolling = True
    last_position = 0  # Current scroll amount
    height = 0         # Height to scroll to

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
                    print(f'\rGot {tweet_counter} tweet(s) out of {max_tweets}', end="")
            if tweet_counter >= max_tweets:
                break

        if tweet_counter >= max_tweets:
            print(f'\nCollected {tweet_counter} tweets')
            break

        # Scroll and update last position, scrolling flag and height to scroll to
        height += SCROLL_AMOUNT
        last_position, scrolling = scroll(driver=driver,height=height,max_attempts=3, last_pos=last_position)
        if not scrolling:
            print(f'\nCollected {tweet_counter} tweets')

    
    for data in tweet_datas:
        with open(save_dir+'/tweet_'+str(starting_n)+'.json', mode='w', encoding='utf-8') as outjson:
            json.dump(data, outjson, indent=2)
        starting_n += 1

    driver.close()
    return tweet_counter

def get_ids_set(d):
    tweet_ids = set()
    starting_n = 0

    for file in os.listdir(d):
        full_path = d+'/'+file
        if os.path.isfile(full_path):
            with open(full_path, 'r', encoding='utf-8') as tweet_json:
                post_data = json.load(tweet_json)
                id = post_data["id"]
                tweet_ids.add(id)
            starting_n += 1

    return starting_n, tweet_ids

def main():
    load_dotenv()
    TWEETS_DIR = '../tweets'
    starting_n, seen_ids = get_ids_set(TWEETS_DIR)

    keywords = ['Citizen Energy Communities','Renewable Energy Cooperatives','Energy Cooperatives','Energy communities','Community energy projects','Local energy initiatives','Renewable energy cooperatives','Community-owned energy','Distributed energy resources','Energy sharing schemes']
    curr_n = starting_n
    for keyword in keywords:
        n_tweets = search_tweets(keyword, 20, TWEETS_DIR, seen_ids, curr_n)
        curr_n += n_tweets

main()

    


