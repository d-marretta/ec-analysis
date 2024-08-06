import sys
sys.path.append('/home/daniele/Documents/Thesis/utils')
import matplotlib.pyplot as plt
import numpy as np
import string
from rank_bm25 import BM25Okapi
import json
import os
import utils
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import seaborn as sns
import pandas as pd

def get_scores(d, keywords, top_5 = False):
    docs = []
    for file in os.listdir(d):
        fullpath = d+'/'+file
        id = file.split('_')[1].split('.')[0]
        if os.path.isfile(fullpath):
            with open(fullpath, mode='r', encoding='utf-8') as fjson:
                post_data = json.load(fjson)

                exclude = set(string.punctuation)
                clean_text = ''
                
                for ch in post_data['text']:
                    if ch in exclude:
                        clean_text += ' '
                    else:
                        clean_text += ch

                docs.append((id,clean_text.lower()))
    
    tokenized_docs = [doc.split() for id,doc in docs]

    bm25 = BM25Okapi(tokenized_docs)

    keyword_scores = {}
    for keyword in keywords:
        keyword = keyword.lower().strip()
        doc_scores = bm25.get_scores(keyword.split())
        keyword_scores[keyword] = doc_scores
    
    docs_keywords_score = {}
    for i in range(len(tokenized_docs)):
        doc_scores = []
        for keyword, scores in keyword_scores.items():
            doc_scores.append((scores[i], keyword))
        if top_5:
            top_doc_scores = sorted(doc_scores, reverse=True)[:5]
            docs_keywords_score[docs[i][0]] = top_doc_scores
        else:
            docs_keywords_score[docs[i][0]] = doc_scores
    
    return docs_keywords_score

def cluster(keywords, docs_keywords_score, k, zero_fill=False):
    all_scores = []
    for i,scores in docs_keywords_score.items():
        doc_scores = []
        for keyword in keywords:
            keyword_found = False
            for score in scores:
                if keyword.lower().strip() == score[1].lower().strip():
                    doc_scores.append(score[0])
                    keyword_found = True
            if not keyword_found and zero_fill:
               doc_scores.append(np.float64(0.0))

        all_scores.append(doc_scores)

    kmeans = KMeans(n_clusters = k)
    clusters = kmeans.fit_predict(all_scores)

    return clusters, all_scores


def plot_cluster(save_name, clusters, all_scores):
    pca = PCA(n_components=2)
    all_scores_reduced = pca.fit_transform(all_scores)

    plt.figure(figsize=(20, 14))
    sns.scatterplot(x=all_scores_reduced[:,0], y = all_scores_reduced[:,1], hue=clusters, palette='viridis')

    plt.savefig(save_name)


def plot_keywords_scores(save_name, docs_keywords_score, keywords):
    total_relevance = dict()

    for i, keyword in enumerate(keywords):
        keyword = keyword.lower().strip()
        curr_sum = 0
        for doc, scores in docs_keywords_score.items():
            for score in scores:
                if score[1].lower().strip() == keyword:
                    curr_sum += score[0]
        
        total_relevance[keyword] = curr_sum
    
    df = pd.DataFrame(list(total_relevance.items()), columns=['Keyword', 'Total Relevance'])
    df = df.sort_values(by='Total Relevance', ascending=False)

    threshold = df['Total Relevance'].mean()

    plt.figure(figsize=(20, 15))
    plt.bar(df['Keyword'], df['Total Relevance'], color='skyblue')
    plt.axhline(y=threshold, color='r', linestyle='--', label=f'Mean = {threshold:.2f}')
    plt.xlabel('Keywords')
    plt.ylabel('Total Relevance Score')
    plt.title('Document Relevance Based on Keyword Scores')
    plt.xticks(rotation=90)
    plt.legend()
    plt.savefig(save_name)

def plot_documents_scores(save_name, docs_keywords_score):
    
    total_relevance = {doc: sum(score for score, _ in scores) for doc, scores in docs_keywords_score.items()}
    
    df = pd.DataFrame(list(total_relevance.items()), columns=['Document', 'Total Relevance'])
    df = df.sort_values(by='Total Relevance', ascending=False)

    threshold = df['Total Relevance'].mean()

    plt.figure(figsize=(20, 15))
    plt.bar(df['Document'], df['Total Relevance'], color='skyblue')
    plt.axhline(y=threshold, color='r', linestyle='--', label=f'Mean = {threshold:.2f}')
    plt.xlabel('Documents')
    plt.ylabel('Total Relevance Score')
    plt.title('Document Relevance Based on Keyword Scores')
    plt.xticks(rotation=90)
    plt.legend()
    plt.savefig(save_name)


if __name__ == '__main__':
    TWEETS_DIR = "../twitter_data/tweets"
    TWITTER_SAVE_DIR = "../twitter_data"
    FACEBOOK_DIR = "../facebook_data/facebook_posts"
    FACEBOOK_SAVE_DIR = "../facebook_data"

    keywords = utils.get_keywords('..')

    docs_keywords_score = get_scores(FACEBOOK_DIR, keywords, top_5=False)
    top5_docs_keywords_score = get_scores(FACEBOOK_DIR, keywords, top_5=True)

    clusters,all_scores = cluster(keywords, docs_keywords_score, 5, zero_fill=True)
    plot_cluster(FACEBOOK_SAVE_DIR+'/kmeans_allscores_63dims.png', clusters, all_scores)

    clusters,all_scores = cluster(keywords, top5_docs_keywords_score, 5, zero_fill=True)
    plot_cluster(FACEBOOK_SAVE_DIR+'/kmeans_top5_63dims.png', clusters, all_scores)

    plot_documents_scores(FACEBOOK_SAVE_DIR+'/documents_keyword_scores.png', docs_keywords_score=docs_keywords_score)
    plot_keywords_scores(FACEBOOK_SAVE_DIR+'/keywords_scores.png', docs_keywords_score=docs_keywords_score, keywords=keywords)


    docs_keywords_score = get_scores(TWEETS_DIR, keywords, top_5=False)
    top5_docs_keywords_score = get_scores(TWEETS_DIR, keywords, top_5=True)

    clusters,all_scores = cluster(keywords, docs_keywords_score, 5, zero_fill=True)
    plot_cluster(TWITTER_SAVE_DIR+'/kmeans_allscores_63dims.png', clusters, all_scores)

    clusters,all_scores = cluster(keywords, top5_docs_keywords_score, 5, zero_fill=True)
    plot_cluster(TWITTER_SAVE_DIR+'/kmeans_top5_63dims.png', clusters, all_scores)

    plot_documents_scores(TWITTER_SAVE_DIR+'/documents_keyword_scores.png', docs_keywords_score=docs_keywords_score)
    plot_keywords_scores(TWITTER_SAVE_DIR+'/keywords_scores.png', docs_keywords_score=docs_keywords_score, keywords=keywords)


