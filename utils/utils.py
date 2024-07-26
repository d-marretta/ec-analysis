import json
import os
from time import sleep

def get_keywords(d):
    keywords = []
    with open(d+'/keywords.txt', mode='r', encoding='utf-8') as f:
        keywords = f.readlines()

    cleaned_keywords = []
    for keyword in keywords:
        cleaned_keywords.append(keyword.lower().strip())
        
    return cleaned_keywords

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

    

