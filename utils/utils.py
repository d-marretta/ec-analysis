import json
from rank_bm25 import BM25Okapi
import os
import matplotlib.pyplot as plt
import numpy as np
import string
from time import sleep

def get_scores(d, keywords):
    docs = []
    for file in os.listdir(d):
        fullpath = d+'/'+file
        
        if os.path.isfile(fullpath):
            with open(fullpath, mode='r', encoding='utf-8') as fjson:
                tweet_data = json.load(fjson)

                exclude = set(string.punctuation)
                clean_text = ''
                
                for ch in tweet_data['text']:
                    if ch in exclude:
                        clean_text += ' '
                    else:
                        clean_text += ch

                docs.append(clean_text.lower())
    
    tokenized_docs = [doc.split() for doc in docs]

    bm25 = BM25Okapi(tokenized_docs)

    scores = [0 for i in range(len(docs))]

    for keyword in keywords:
        keyword = keyword.lower().strip()
        doc_scores = bm25.get_scores(keyword.split())
        for i in range(len(scores)):
            scores[i] += doc_scores[i]
    
    for i, score in enumerate(scores):
        n_keywords = len(keywords)
        scores[i] = (score / n_keywords, i)

    scores.sort(reverse=True)
    
    #print(scores[7000])
    #print(docs[2461])

    return scores



def plot_scores(scores):
    for i,(score,k) in enumerate(scores):
        scores[i] = score
    
    x = np.array(scores)
    y = np.array([i for i in range(len(scores))])

    plt.figure(figsize=(20, 14))
    plt.scatter(x,y, s=0.5)

    plt.show()

def get_keywords(d):
    keywords = []
    with open(d+'/keywords.txt', mode='r', encoding='utf-8') as f:
        keywords = f.readlines()

    return keywords

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

if __name__ == '__main__':
    keywords = get_keywords('..')
    scores = get_scores('../tweets', keywords)
    plot_scores(scores)
    

