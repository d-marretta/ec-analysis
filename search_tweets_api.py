import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

def search_x(query, bearer_token, tweet_fields=""):        
    headers = {"Authorization":f"Bearer {bearer_token}"}

    if tweet_fields:
        url = f'https://api.twitter.com/2/tweets/search/recent?query={query}&tweet.fields={tweet_fields}'
    else:
        url = f'https://api.twitter.com/2/tweets/search/recent?query={query}'
    
    response = requests.get(url=url, headers=headers)

    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    
    return response.json()

query = "energy communities"

response = search_x(query=query, bearer_token=BEARER_TOKEN)

print(json.dumps(response, indent=4, sort_keys=True))



