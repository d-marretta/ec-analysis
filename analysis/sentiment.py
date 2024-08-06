from transformers import AutoModelForSequenceClassification
from transformers import AutoTokenizer, AutoConfig
import numpy as np
import os
from scipy.special import softmax
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
import unicodedata
import emoji
import matplotlib.pyplot as plt

def preprocess(text):
    normalized = unicodedata.normalize('NFKD', text)
    no_emoji = emoji.replace_emoji(normalized, replace=' ')
    new_text = []
    for t in no_emoji.split(' '):
        if t.startswith('@') and len(t) > 1:
            t = '@user'
        elif t.startswith('http'):
            t = 'http'
        new_text.append(t)

    return " ".join(new_text)



def output_sentiment(model, tokenizer, config, text):
    encoded_text = tokenizer(text, return_tensors='pt')
    output = model(**encoded_text)

    scores = output[0][0].detach().numpy()
    scores = softmax(scores)

    ranking = np.argsort(scores)
    ranking = ranking[::-1]

    sentiment = config.id2label[ranking[0]]

    return sentiment



def analyze_texts(d, model, tokenizer, config):
    for file in os.listdir(d):
        full_path = d + '/' + file

        with open(full_path, mode='r', encoding='utf-8') as post:
            post_data = json.load(post)
        
        text = preprocess(post_data['text'])

        if len(text) <= 510:
            try:
                sentiment = output_sentiment(model, tokenizer, config, text)
                post_data['sentiment'] = sentiment
            except:
                print(text)

        else:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=510, chunk_overlap=120)
            chunks = text_splitter.split_text(text)
            sentiments = []
            for chunk in chunks:
                try:
                    chunk_sentiment = output_sentiment(model, tokenizer, config, chunk)
                    sentiments.append(chunk_sentiment)

                except:
                    print(chunk)

            
            positives = 0
            neutrals = 0
            negatives = 0
            for sent in sentiments:
                if sent == 'positive':
                    positives += 1
                elif sent == 'neutral':
                    neutrals += 1
                else:
                    negatives += 1
            
            sentiments_list = [positives,neutrals,negatives]
            sentiments_set = set(sentiments_list)
            if len(sentiments_list) == len(sentiments_set):
                m = max(sentiments_list)
                if m == positives:
                    sentiment = 'positive'
                elif m == neutrals:
                    sentiment = 'neutral'
                else:
                    sentiment = 'negative'
            
            elif len(set(sentiments_list)) == 1:
                sentiment = 'neutral'

            else:
                m = min(sentiments_list)
                if m == positives:
                    sentiment = 'negative'
                elif m == neutrals:
                    sentiment = 'neutral'
                else:
                    sentiment = 'positive'

            if sentiment:
                post_data['sentiment'] = sentiment

        with open(full_path, mode='w', encoding='utf-8') as new_post:
            json.dump(post_data, new_post, indent=2)


def plot_sentiments(d, save_name):
    positives = 0
    neutrals = 0
    negatives = 0

    for file in os.listdir(d):
        full_path = d + '/' + file

        with open(full_path, mode='r', encoding='utf-8') as f:
            data = json.load(f)
            try:
                sentiment = data['sentiment']
            except KeyError:
                pass

            if sentiment == 'positive':
                positives += 1
            elif sentiment == 'neutral':
                neutrals += 1
            else:
                negatives += 1
    
    labels = ['Positives', 'Neutrals', 'Negatives']
    values = [positives, neutrals, negatives]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values, color='skyblue')
    plt.ylabel('Counts')
    plt.title('Counts of positives, neutrals and negatives')
    plt.savefig(save_name)

if __name__ == '__main__':
    MODEL = f'cardiffnlp/twitter-roberta-base-sentiment-latest'
    TWEETS_DIR = '../twitter_data/tweets'
    POSTS_DIR = '../facebook_data/facebook_posts'

    # tokenizer = AutoTokenizer.from_pretrained(MODEL)
    # config = AutoConfig.from_pretrained(MODEL)
    # model = AutoModelForSequenceClassification.from_pretrained(MODEL)

    # analyze_texts(TWEETS_DIR, model, tokenizer, config)

    # analyze_texts(POSTS_DIR, model, tokenizer, config)

    plot_sentiments(POSTS_DIR, '../facebook_data/sentiments.png')
    plot_sentiments(TWEETS_DIR, '../twitter_data/sentiments.png')


    