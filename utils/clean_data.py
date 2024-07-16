import matplotlib.pyplot as plt
import numpy as np
import string
from rank_bm25 import BM25Okapi
import json
import os
import utils
from string import punctuation

def get_new_post_data(f):
    with open(f, mode='r', encoding='utf-8') as post:
        post_data = json.load(post)
    
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

        with open(full_path, mode='w', encoding='utf-8') as fjson:
            json.dump(new_post_data, fjson, indent=2)


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

if __name__ == '__main__':
    keywords = utils.get_keywords('..')
    scores = get_scores('../facebook_data/facebook_posts', keywords)
    plot_scores(scores)