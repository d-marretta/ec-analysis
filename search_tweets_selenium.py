
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
import pickle
from dotenv import load_dotenv
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

SCROLL_AMOUNT=800

def get_tweet_data(container):
    
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
        '_id':(tag+tweet_date),
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

def search_tweets(query, max_tweets, coll):
    # Start chrom webdriver
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.x.com/")

    # Get logins cookies
    cookies = pickle.load(open("auth.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://www.x.com/")

    driver.implicitly_wait(2)
    time.sleep(1)

    # Allow the page to load
    url = urllib.parse.quote(string=f"https://x.com/search?q={query}&src=typed_query&f=top", safe='/&?=:')
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
            tweet_data = get_tweet_data(container=container)
            if tweet_data:
                tweet_id = tweet_data['_id']

                # Check if the document is already in the db or in the ids list of current scraping session
                if (tweet_id not in tweet_ids) and (coll.find_one({"_id":tweet_id}) == None):
                    tweet_ids.add(tweet_id)
                    tweet_datas.append(tweet_data)
                    tweet_counter += 1
                    print(f'\rGot {tweet_counter} tweet(s) out of {max_tweets}', end="")

        if tweet_counter >= max_tweets:
            print(f'\nCollected {tweet_counter} tweets')
            break

        # Scroll and update last position, scrolling flag and height to scroll to
        height += SCROLL_AMOUNT
        last_position, scrolling = scroll(driver=driver,height=height,max_attempts=3, last_pos=last_position)
    
    print('Inserting into database...')
    coll.insert_many(tweet_datas)
    print('Inserting completed')

    driver.close()


def main():
    # Connect to database
    load_dotenv()
    db_conn = MongoClient(os.getenv('DB_URI'), server_api=ServerApi('1'))
    db = db_conn.get_database('TweetsDB')
    coll = db.get_collection('tweets')

    search_tweets('#energycommunities', 10, coll)

main()

    


