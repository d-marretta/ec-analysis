import json
import os
import networkx
from ipysigma import Sigma
from datetime import datetime


def transform_date(date_string):
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        return date_obj.strftime("%d %B %Y at %H:%M")
    except ValueError:
        try:
            date_obj = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return date_obj.strftime("%d %B %Y at %H:%M")
        except ValueError:
            return "Invalid date format"
    

def draw_graph(posts_dir, graph_dir, with_mentions=True, with_hashtags=True):

    posts = []

    for file in os.listdir(posts_dir):
        full_path = posts_dir + '/' + file

        with open(full_path, mode='r', encoding='utf-8') as f:
            post_data = json.load(f)
            posts.append(post_data)
    
    graph = networkx.DiGraph()
    if 'twitter' in posts_dir:
        tag_string = 'tag'
    elif 'facebook' in posts_dir:
        tag_string = 'username'

    for post in posts:
        tag = post[tag_string]
        mentions = post['mentions']
        hashtags = post['hashtags']
        date = transform_date(post['date'])

        graph.add_node(tag, type='user', date=date)

        if with_mentions:
            for mention in mentions:
                graph.add_node(mention, type='user')
                graph.add_edge(tag, mention, type='mention')
        
        if with_hashtags:
            for hashtag in hashtags:
                hashtag = hashtag.lower()
                graph.add_node(hashtag, type='hashtag')
                graph.add_edge(tag, hashtag, type='uses')
    
    graph.remove_nodes_from(list(networkx.isolates(graph)))
    
    #networkx.draw(graph, networkx.spring_layout(graph), with_labels=True, node_color='skyblue', edge_color='gray')
    #Sigma(graph, node_color='tag', node_label_size=graph.degree, node_size= graph.degree)

    if not with_mentions:
        graph_dir = graph_dir + '/relations_no_mentions.html'
    elif not with_hashtags:
        graph_dir = graph_dir + '/relations_no_hashtags.html'
    else:
        graph_dir = graph_dir + '/relations.html'
    Sigma.write_html(
        graph,
        graph_dir,
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
    TWEETS_DIR = "../twitter_data/tweets"
    TWITTER_GRAPH_DIR = "../twitter_data"
    FACEBOOK_DIR = "../facebook_data/facebook_posts"
    FACEBOOK_GRAPH_DIR = "../facebook_data"
    draw_graph(TWEETS_DIR, TWITTER_GRAPH_DIR)
    draw_graph(FACEBOOK_DIR, FACEBOOK_GRAPH_DIR)

    draw_graph(TWEETS_DIR, TWITTER_GRAPH_DIR, with_mentions=False)
    draw_graph(FACEBOOK_DIR, FACEBOOK_GRAPH_DIR, with_mentions=False)

    draw_graph(TWEETS_DIR, TWITTER_GRAPH_DIR, with_hashtags=False)
    draw_graph(FACEBOOK_DIR, FACEBOOK_GRAPH_DIR, with_hashtags=False)
