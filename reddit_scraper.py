#https://www.youtube.com/watch?v=2Ry78DUeONw

import requests
import json
import csv
import time
from bs4 import BeautifulSoup

def scrape_reddit() -> list[dict]:
    subreddits = [
        "https://www.reddit.com/r/Python"
    ]

    with requests.Session() as s:
        s.headers.update({
                'User-Agent' : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
            })

        all_data = []
        for url in subreddits:
            subreddit_name = url.split("/")[-1]
            print(f'Scraping for: {subreddit_name}')

            try:
                #send http request
                response = s.get(url, timeout=10)
                response.raise_for_status()

                #html parser object
                soup = BeautifulSoup(response.content, "html.parser")

                subreddit_data = {
                    "subreddit_name" : subreddit_name,
                    "url" : url,
                    "title" : soup.title.string if soup.title else "No title",
                    "scraped_at" : time.strftime("%Y-%m-%d %H:%M%S")
                }
            except Exception as e:
                print(f'Error: {e}')
            
            return subreddit_data


def main() -> None:
    data = scrape_reddit()

    if data:
        print(f'Processing the data...')
        json_string = json.dumps(data, indent=4)
        print(f'{json_string}')
        total_topics = 0
    else:
        print('There is no data')

#keep for vscode debugger
if __name__ == "__main__":
    main()


#Optimizations made
#1. switched from requests to sessions with TCP keep connection alive to reduce overhead
#2. 


#TODO
#1. take subreddit names from arg or file
#2. fix "Reddit - Please wait for verification" issue
#3. 