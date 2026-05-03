#https://www.youtube.com/watch?v=2Ry78DUeONw

import requests
import json
import csv
import time
from bs4 import BeautifulSoup

def scrape_reddit() -> list[dict]:
    subreddits = [
        'Python',
    ]

    with requests.Session() as s:
        #generic user agent so that we aren't marked as a bot.
        s.headers.update({
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
            })

        all_data = []
        posts_count = 0
        comments_count = 0
        for subreddit in subreddits:
            # limit=100 - reddit only allows 100 posts per page
            subreddit_url = 'https://old.reddit.com/r/' + subreddit + '/new/?limit=100'
            print(f'Beginning scrape for: {subreddit}')

            try:
                #send subreddit home page http request
                print(f'fetching r/{subreddit} html')
                subreddit_response = s.get(subreddit_url, timeout=10)
                subreddit_response.raise_for_status()

                #html parser object
                soup = BeautifulSoup(subreddit_response.content, 'html.parser')

                #only posts have data-rank attribute
                posts = soup.find_all('div', attrs={'data-rank' : True} )
                post_urls = []
                for post in posts:
                    post_urls.append('https://old.reddit.com' + post.find('a').get('href'))

                for url in post_urls:
                    print(f'fetching {url}')
                    post_response = s.get(url, timeout=10)
                    post_response.raise_for_status()
                    soup = BeautifulSoup(post_response.content, 'html.parser')
                    #only the post has 'sitetable linklisting' not comments
                    page_post = soup.find(class_='sitetable linklisting').find('div')

                    print(f'Parsing post...')
                    post_data = {
                        'subreddit_name' : subreddit,
                        'title' : page_post.find('a', class_='title').get_text(),
                        'post-id' : page_post.get('data-fullname'),
                        'author' : page_post.get('data-author'),
                        'author-id' : page_post.get('data-author-fullname'),
                        'url' : url,
                        'date-posted' : page_post.find('time').get('title'),
                        'live-timestamp' : page_post.find('time', class_='live-timestamp').get_text(),
                        'score' : page_post.get('data-score', 'Unknown'), #some subreddits hide scores for the first 60mins
                        'comments' : page_post.get('data-comments-count'),
                        'promoted' : page_post.get('data-promoted'),
                        'nsfw' : page_post.get('data-nsfw'),
                        'golds' : page_post.get('data-gildings'), 
                        'content' : page_post.find('div', class_='md').get_text()
                    }
                    all_data.append(post_data)
                    posts_count += 1
                    print(f'Post parsing finished')

                    print(f'Parsing comments...')
                    comments = soup.find_all('div', attrs={'data-type' : 'comment'})
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
                        comments_count += 1
                        
                        all_data.append(comment_data)
                    print(f'Comment parsing finished')
                    print(f'Finished parsing: {url}\n')

            except Exception as e:
                print(f'Error: {e}')
            
    return (all_data, posts_count, comments_count)


def main() -> None:
    data, num_posts, num_comments = scrape_reddit()

    if data:
        print(f'Processing the data...')
        json_string = json.dumps(data, indent=4)
        print(f'{json_string}')
        print('FINAL RESULTS')
        print('-----------------------------------------')
        print(f'# of posts scraped: {num_posts}')
        print(f'# of comments scraped: {num_comments}')
    else:
        print('There is no data')

#keep for vscode debugger
if __name__ == '__main__':
    main()


#OPTIMIZATIONS MADE
#1. switched from requests to sessions with TCP keep connection alive to reduce overhead
#2. 

#TO-DO
#-collect comments
#-take subreddit names from arg or file
#-error handling
#-multithreading
#-randomized delays?

#FIXES
#PRAW module needs lengthy approval ---> use beautiful soup
#-fix 'Reddit - Please wait for verification' issue ---> use old.reddit.com

#