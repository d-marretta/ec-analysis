import utils
import json
from string import punctuation
import os

def get_new_tweet_data(f):
    with open(f, mode='r', encoding='utf-8') as tweet:
        tweet_data = json.load(tweet)
    
    exclude = set(punctuation.replace('#','').replace('@',''))
    clean_text = ''
    for ch in tweet_data['text']:
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
    
    tweet_data['hashtags'] = list(hashtags)
    tweet_data['mentions'] = list(mentions)
    tweet_data['keyword'] = tweet_data['keyword'].strip()
    
    print(tweet_data)

def add_hash_and_mentions(d):

    for file in os.listdir(d):
        full_path = d + '/' + file

        with open(full_path, mode='r', encoding='utf-8') as tweet:
            return
    pass


if __name__ == '__main__':
    get_new_tweet_data('../tweets/tweet_7841.json')