import json
from rank_bm25 import BM25Okapi
import os

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

    scores = []

    for keyword in keywords:
        keyword = keyword.lower()
        doc_scores = bm25.get_scores(keyword.split())
        for i in range(len(scores)):
            scores[i] += doc_scores[i]
    
    for i, score in enumerate(scores):
        n_keywords = len(keywords)
        score = (score / n_keywords, i)
    
    scores.sort(reverse=True)
    least_scores = scores[-5:]
    least_docs = [docs[i] for score,i in least_scores]
    print(least_scores)
    print(least_docs)
    

