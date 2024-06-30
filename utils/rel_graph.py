import json
from string import punctuation
import os
import networkx
import matplotlib.pyplot as plt
from ipysigma import Sigma

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
    
    return tweet_data

def add_hash_and_mentions(tweets_dir):

    for file in os.listdir(tweets_dir):
        full_path = tweets_dir + '/' + file

        new_tweet_data = get_new_tweet_data(full_path)

        with open(full_path, mode='w', encoding='utf-8') as fjson:
            json.dump(new_tweet_data, fjson, indent=2)
    

def draw_graph(tweets_dir, graph_dir):

    tweets = []

    for file in os.listdir(tweets_dir):
        full_path = tweets_dir + '/' + file

        with open(full_path, mode='r', encoding='utf-8') as f:
            tweet_data = json.load(f)
            tweets.append(tweet_data)
    
    graph = networkx.DiGraph()

    for tweet in tweets:
        # TODO: add date time attribute
        tag = tweet['tag']
        mentions = tweet['mentions']
        hashtags = tweet['hashtags']

        graph.add_node(tag, type='user')

        for mention in mentions:
            graph.add_node(mention, type='user')
            graph.add_edge(tag, mention, type='mention')
        
        for hashtag in hashtags:
            graph.add_node(hashtag, type='hashtag')
            graph.add_edge(tag, hashtag, type='uses')
    
    graph.remove_nodes_from(list(networkx.isolates(graph)))
    
    #networkx.draw(graph, networkx.spring_layout(graph), with_labels=True, node_color='skyblue', edge_color='gray')
    #Sigma(graph, node_color='tag', node_label_size=graph.degree, node_size= graph.degree)

    Sigma.write_html(
        graph,
        graph_dir +'/relations.html',
        fullscreen=True,
        start_layout=True,
        node_metrics=["louvain"],
        node_color='louvain',
        node_size_range=(3,30),
        node_border_color_from='node',
        default_node_label_size=14,
        default_edge_type='curve',
        label_font='cursive',
        max_categorical_colors=1000,
        node_size=graph.degree,
        hide_edges_on_move=True
    )
        

if __name__ == '__main__':
    draw_graph('../tweets', '..')