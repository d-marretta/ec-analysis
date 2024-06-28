import json
from rank_bm25 import BM25Okapi
import os
import matplotlib.pyplot as plt
import numpy as np

def get_scores(d, keywords):
    docs = []
    for file in os.listdir(d):
        fullpath = d+'/'+file
        
        if os.path.isfile(fullpath):
            with open(fullpath, mode='r', encoding='utf-8') as fjson:
                tweet_data = json.load(fjson)
                docs.append(tweet_data['text'].replace('#', ' ').lower())
    
    tokenized_docs = [doc.split() for doc in docs]

    bm25 = BM25Okapi(tokenized_docs)

    scores = [0 for i in range(len(docs))]

    for keyword in keywords:
        keyword = keyword.lower()
        doc_scores = bm25.get_scores(keyword.split())
        for i in range(len(scores)):
            scores[i] += doc_scores[i]
    
    for i, score in enumerate(scores):
        n_keywords = len(keywords)
        scores[i] = (score / n_keywords, i)

    scores.sort(reverse=True)
    print(scores[7000])
    print(docs[2461])

    least_scores = scores[-20:]
    least_docs = [docs[i] for score,i in least_scores]
    #print(least_scores)
    print()
    #print(least_docs)

    for i,(score,k) in enumerate(scores):
        scores[i] = score
    
    x = np.array(scores)
    y = []
    for i in range(len(scores)):
        y.append(i)

    y = np.array(y)

    plt.scatter(x,y)

    #plt.show()


def get_keywords(d):
    keywords = []
    with open(d+'/keywords.txt', mode='r', encoding='utf-8') as f:
        keywords = f.readlines()

    return keywords

def main():
    pass

if __name__ == '__main__':
    keywords = get_keywords('..')
    get_scores('../tweets', keywords)
    

