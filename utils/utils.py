import json
import os
from time import sleep
from string import punctuation
from langdetect import detect
import unicodedata
import emoji

def get_new_post_data(f):
    with open(f, mode='r', encoding='utf-8') as post:
        post_data = json.load(post)
    
    try:
        boh = post_data['mentions']
        return {}
    
    except KeyError:
        exclude = set(punctuation.replace('#','').replace('@',''))
        clean_text = ''
        for ch in post_data['text']:
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
        
        post_data['hashtags'] = list(hashtags)
        post_data['mentions'] = list(mentions)
        post_data['keyword'] = post_data['keyword'].strip()
        
        return post_data
    

def add_hash_and_mentions(posts_dir):

    for file in os.listdir(posts_dir):
        full_path = posts_dir + '/' + file

        new_post_data = get_new_post_data(full_path)

        if new_post_data:
            with open(full_path, mode='w', encoding='utf-8') as fjson:
                json.dump(new_post_data, fjson, indent=2)


def get_keywords(d):
    keywords = []
    with open(d+'/keywords.txt', mode='r', encoding='utf-8') as f:
        keywords = f.readlines()

    cleaned_keywords = []
    for keyword in keywords:
        cleaned_keywords.append(keyword.lower().strip())
        
    return cleaned_keywords

def scroll(driver, height, max_attempts, last_pos):
    # Try scrolling multiple times, in case the page has to load
    attempt = 0
    curr_pos = 0
    while attempt < max_attempts:
        driver.execute_script(f'window.scrollTo(0, {height})')
        sleep(0.5)
        curr_pos = driver.execute_script("return window.scrollY")
        if last_pos == curr_pos:
            # No scrolling happened, try again
            sleep(1)
            attempt += 1
        else:
            # Return new last_position, new height to scroll to and 
            # whether scrolling is still true or false
            return curr_pos,True
    
    return curr_pos,False

def get_ids_set(d):
    post_ids = set()
    starting_n = 0

    for file in os.listdir(d):
        full_path = d+'/'+file
        if os.path.isfile(full_path):
            with open(full_path, 'r', encoding='utf-8') as post_json:
                post_data = json.load(post_json)
                id = post_data["id"]
                post_ids.add(id)
            starting_n += 1

    return starting_n, post_ids

def perc_not_english(d):
    not_english = set()
    n_files = 0
    no_text = set()
    for file in os.listdir(d):
        n_files += 1
        fullpath = d+'/'+file
        id = file.split('_')[1].split('.')[0]
        if os.path.isfile(fullpath):
            with open(fullpath, mode='r', encoding='utf-8') as fjson:
                post_data = json.load(fjson)

                text = post_data['text']
                normalized = unicodedata.normalize('NFKD', text)
                no_emoji = emoji.replace_emoji(normalized, replace=' ')
                if not text:
                    no_text.add(id)
                    continue
                try:
                    lang = detect(no_emoji)
                except:
                    pass
                if lang != 'en':
                    not_english.add(id)

    return not_english, no_text

def clean_posts(d, not_english, no_text):
    for file in os.listdir(d):
        fullpath = d+'/'+file
        id = file.split('_')[1].split('.')[0]
        if (id in not_english) or (id in no_text):
            os.remove(fullpath)


if __name__ == '__main__':
    keywords = get_keywords('..')

    TWEETS_DIR = '../twitter_data/tweets'
    FACEBOOK_DIR = '../facebook_data/facebook_posts'
    
    not_english_tweets, no_text_tweets = perc_not_english(TWEETS_DIR)

    not_english_posts, no_text_posts = perc_not_english(FACEBOOK_DIR)

    clean_posts(TWEETS_DIR, not_english_tweets, no_text_tweets)
    clean_posts(FACEBOOK_DIR, not_english_posts, no_text_posts)

    # print(len(not_english_tweets))
    # print(len(no_text_tweets))
    # print(len(not_english_posts))
    # print(len(no_text_posts))



