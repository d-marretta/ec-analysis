import matplotlib.pyplot as plt
import numpy as np
import string
from rank_bm25 import BM25Okapi
import json
import os
import utils
from string import punctuation
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import seaborn as sns
import pandas as pd
from langdetect import detect

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

    # pca = PCA(n_components=3)
    # all_scores_reduced = pca.fit_transform(all_scores)

    # fig = plt.figure(figsize=(20, 14))
    # ax = fig.add_subplot(111, projection='3d')
    
    # scatter = ax.scatter(all_scores_reduced[:,0], all_scores_reduced[:,1], all_scores_reduced[:,2], c=clusters, cmap='viridis')
        
    # ax.set_xlabel('PCA Component 1')
    # ax.set_ylabel('PCA Component 2')
    # ax.set_zlabel('PCA Component 3')

    # plt.show()


def plot_scores(save_name, docs_keywords_score):
    
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
                if not text:
                    no_text.add(id)
                    continue
                try:
                    lang = detect(text)
                except:
                    print(text)

                if lang != 'en':
                    # print(text)
                    # print(lang)
                    # print('-------------------------------------------------------')
                    not_english.add(id)
    
    print(len(not_english))
    print(len(no_text))
    print(len(no_text) / n_files * 100)
    perc = (len(not_english) / n_files) * 100
    
    return perc

if __name__ == '__main__':
    keywords = utils.get_keywords('..')
    #docs_keywords_score = get_scores('../facebook_data/facebook_posts', keywords, top_5=False)
    #clusters,all_scores = cluster(keywords, docs_keywords_score, 6, zero_fill=True)
    #plot_cluster('../facebook_data/kmeans_allscores_63dims.png', clusters, all_scores)

    #plot_scores('../facebook_data/documents_keyword_scores.png', docs_keywords_score=docs_keywords_score)

    print(perc_not_english('../facebook_data/facebook_posts'))

