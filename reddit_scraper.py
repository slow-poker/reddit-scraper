#bs4 reddit scraping - https://www.youtube.com/watch?v=2Ry78DUeONw
#argeparse formatting https://stackoverflow.com/questions/52605094/python-argparse-increase-space-between-parameter-and-description

import requests
import json
import argparse
import sys
import time
import random
from bs4 import BeautifulSoup

#callback shenanigans for formatting help menu
def wide_formatter(prog):
    return argparse.HelpFormatter(prog, max_help_position=52)

#flag arg helper object
parser = argparse.ArgumentParser(
    description='Group 5 Reddit Web Scraper Part A',
    formatter_class = wide_formatter
)

#args
# Add the two options to the group
input_opt = parser.add_mutually_exclusive_group(required=True)
input_opt.add_argument('-f', '--file', help='File path to subreddit list')
input_opt.add_argument('-t', '--text', nargs='+', metavar='SUB1', help='Subreddit name(s)')
parser.add_argument('-p', '--posts', type=int, default=10, help='Max posts to pull per subreddit [0-1000]')
parser.add_argument('-c', '--category', choices=['hot', 'new', 'rising', 'controversial', 'top'], default='new')


#TO-DO
# parser.add_argument('-s', '--size', default='10MB', help='File chunk sizes for data') 
# parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')
args = parser.parse_args()

def scrape_reddit() -> list[dict]:
    
    if args.file:
        try:
            with open(args.file, 'r') as file:
                subreddits = file.read().splitlines()
        except Exception as e:
            print(f'Error: {e}')
            sys.exit(1)
    
    if args.text:
        subreddits = args.text

    with requests.Session() as s:
        #generic user agent so that we aren't marked as a bot.
        s.headers.update({
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
            })

        posts_count = 0
        comments_count = 0
        for subreddit in subreddits:
            # limit=100 - reddit only allows 100 posts per page
            subreddit_url = 'https://old.reddit.com/r/' + subreddit + '/' + args.category + '/?limit=1'
            print(f'Beginning scrape for: {subreddit}')

            try:
                while True:
                    #send subreddit home page http request
                    print(f'fetching r/{subreddit} html')
                    subreddit_response = s.get(subreddit_url, timeout=10)
                    subreddit_response.raise_for_status()

                    #html parser object
                    subreddit_soup = BeautifulSoup(subreddit_response.content, 'html.parser')

                    #only posts have data-rank attribute
                    posts = subreddit_soup.find_all('div', attrs={'data-rank' : True} )
                    post_urls = []
                    for post in posts:
                        post_urls.append('https://old.reddit.com' + post.get('data-permalink'))

                    for url in post_urls:
                        print(f'Fetching post: {url}')
                        post_response = s.get(url, timeout=10)
                        post_response.raise_for_status()
                        page_soup = BeautifulSoup(post_response.content, 'html.parser')
                        #only the post has 'sitetable linklisting' not comments
                        page_post = page_soup.find(class_='sitetable linklisting').find('div')

                        with open('output.txt', 'a', encoding='utf-8') as file:
                            print(f'Parsing post and comments...')
                            post_data = {
                                'subreddit_name' : subreddit,
                                'title' : page_post.find('a', class_='title').get_text(),
                                'post-id' : page_post.get('data-fullname'),
                                'author' : page_post.get('data-author'),
                                'author-id' : page_post.get('data-author-fullname'),
                                'url' : url,
                                'attached-url' : page_post.get('data-url') if page_post.get('data-url') != page_post.get('data-permalink') else "None",
                                'date-posted' : page_post.find('time').get('title'),
                                'live-timestamp' : page_post.find('time', class_='live-timestamp').get_text(),
                                'score' : page_post.get('data-score', 'Unknown'), #some subreddits hide scores for the first 60mins
                                'comments' : page_post.get('data-comments-count'),
                                'promoted' : page_post.get('data-promoted'),
                                'nsfw' : page_post.get('data-nsfw'),
                                'golds' : page_post.get('data-gildings'),  
                                'content': div.get_text() if (div := page_post.find('div', class_='md')) else "None"
                            }
                            
                            file.write(str(post_data) + '\n')
                            posts_count += 1
                            
                            comments = page_soup.find_all('div', attrs={'data-type' : 'comment'})
                            for comment in comments:
                                comment_data = {
                                    'subreddit_name' : subreddit,
                                    'post-id' : post_data['post-id'],
                                    'comment-id' : comment.get('data-fullname'),
                                    'author' : comment.get('data-author'),
                                    'author-id' : comment.get('data-author-fullname'),
                                    'url' : 'https://old.reddit.com' + comment.get('data-permalink'), 
                                    'data-commented' : comment.find('time').get('title'),
                                    'live-timestamp' : comment.find('time').get_text(), 
                                    'score' : comment.find('span', class_=['score unvoted', 'score-hidden']).get_text(), #some subreddits hide scores for the first 60mins
                                    'replies' : comment.get('data-replies'),
                                    'content' : comment.find('div', class_='md').get_text()
                                }
                                file.write(str(comment_data) + '\n')
                                comments_count += 1

                                if posts_count >= args.posts:
                                    with open('results.txt', 'a', encoding='utf-8') as file:
                                        output = ('''FINAL RESULTS\n 
                                                +-----------------------------------------+\n
                                                posts scraped: {}\n
                                                comments scraped: {}\n
                                                +-----------------------------------------+\n'''
                                                .format(posts_count, comments_count)
                                                )
                                        file.write(output)
                                    return
                            print(f'Finished parsing: {url}\n')

                    subreddit_url = subreddit_soup.find('span', class_='next-button')
                    if subreddit_url:
                        subreddit_url = subreddit_url.find('a').get('href')
                    else:
                        break

            except Exception as e:
                print(f'Error: {e}')
                sys.exit(1)
            


def main() -> None:
    scrape_reddit()

#keep for vscode debugger
if __name__ == '__main__':
    main()


#OPTIMIZATIONS MADE
#1. switched from requests to sessions with TCP keep connection alive to reduce overhead
#2. 

#TO-DO
#file storage
#----double check main and make seperate file for stats
#change from json to csv i think
#time checks
#-multithreading
#-rate limiting ~ 60 requests per minute 
#-slightly randomized delays

#FIXES
#PRAW module needs lengthy approval ---> use beautiful soup
#-fix 'Reddit - Please wait for verification' issue ---> use old.reddit.com

#challenges
#data-url and data-permalink are usually the same, except for when a link is attached to a post
#1000 post limit per sorting method (new, hot, top, etc)