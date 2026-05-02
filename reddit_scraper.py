#https://www.youtube.com/watch?v=2Ry78DUeONw

import requests
import json
import csv
import time
from bs4 import BeautifulSoup

def scrape_reddit() -> list[dict]:
    subreddits = [
        'Python'
    ]

    with requests.Session() as s:
        #generic user agent so that we aren't marked as a bot.
        s.headers.update({
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
            })

        all_data = []
        for subreddit in subreddits:
            url = 'https://old.reddit.com/r/' + subreddit + '/?limit=5'
            print(f'Scraping for: {subreddit}')

            try:
                #send http request
                response = s.get(url, timeout=10)
                response.raise_for_status()

                #html parser object
                soup = BeautifulSoup(response.content, 'html.parser')

                #only posts have data-rank attribute
                posts = soup.find_all('div', attrs={'data-rank' : True} )
                post_list = []
                post_data = {}
                for post in posts:
                    post_data = {
                        'subreddit_name' : subreddit,
                        'url' : url,
                        'title' : post.find('a', class_='title').get_text(),
                        'author' : post.get('data-author', 'No author'),
                        'data_rank' : post.get('data-rank')
                        #'scraped_at' : time.strftime('%Y-%m-%d %H:%M%S')
                    }
                    post_list.append(post_data)
            except Exception as e:
                print(f'Error: {e}')
            
            return post_list


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
if __name__ == '__main__':
    main()


#OPTIMIZATIONS MADE
#1. switched from requests to sessions with TCP keep connection alive to reduce overhead
#2. 

#TO-DO
#-take subreddit names from arg or file
#-error handling
#-multithreading
#-randomized delays?

#FIXED
#PRAW module needs lengthy approval ---> use beautiful soup
#-fix 'Reddit - Please wait for verification' issue ---> use old.reddit.com