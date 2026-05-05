#bs4 reddit scraping - https://www.youtube.com/watch?v=2Ry78DUeONw
#argeparse formatting https://stackoverflow.com/questions/52605094/python-argparse-increase-space-between-parameter-and-description

import requests
import argparse
import sys
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path

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
parser.add_argument('-p', '--posts', type=int, default=3, help='Max posts to pull per subreddit [0-1000]')
parser.add_argument('-c', '--category', choices=['hot', 'new', 'rising', 'controversial', 'top'], default='new', help='sort by categories before scraping')
parser.add_argument('-s', '--size', default='10mb', help='File chunk sizes for data in MB or KB')

#TO-DO
# parser.add_argument('-o', '--output-dir', help='File path / name of output dir')
# parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')
args = parser.parse_args()

#convert args.size to MB or KB
if args.size:
    file_size_units = args.size.upper()[-2:]
    file_size_int = int(args.size[:-2])
    if file_size_units == 'MB':
        max_size = file_size_int * 1024 * 1024 #convert to MB
    elif file_size_units == 'KB':
        max_size = file_size_int * 1024 #convert to KB
    else:
        raise argparse.ArgumentTypeError(f"Invalid size format: '{args.size}'. Use '1kb', '2MB', etc.")

#handles file size checks and writes - assumes it is called within a try{} block to reduce overhead
def write_with_check(dict_data, curr_file, subreddit, counter):
    data = str(dict_data) + '\n'
    data_size = len(data.encode('utf-8')) 
    file_size = curr_file.tell()    #get size of write buffer so that we don't have to travel to disk
    if  file_size + data_size > max_size:
        curr_file.close()
        counter += 1
        new_filepath = Path(curr_file.name).with_stem(f'{subreddit}{counter:05d}')
        new_file = open(new_filepath, 'a', encoding='utf-8')
        new_file.write(data)
        return new_file, counter
    
    curr_file.write(data)
    return curr_file, counter

#write the results of the scrape to results.txt
def results_file(dir_path, total_posts, total_comments):
    results = dir_path / 'results.txt'
    output = ('''FINAL RESULTS\n 
                +-----------------------------------------+\n
                posts scraped: {}\n
                comments scraped: {}\n
                +-----------------------------------------+\n'''
                .format(total_posts, total_comments)
                )
    print(output)
    with open(results, 'a', encoding='utf-8') as file:
        file.write(output)
        file.close()

def detect_duplicates(post_data,  unique_posts):
    id_value = post_data['post-id']
    if id_value not in unique_posts:
        unique_posts.add(id_value)
        return False
    return True
    


def scrape_reddit() -> list[dict]:
    if args.file:
        with open(args.file, 'r') as file:
                subreddits = file.read().splitlines()
                file.close()
    if args.text:
        subreddits = args.text

    unique_posts = set()

    #dir setup
    time_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dir_path = Path('Scrape-' + time_now)
    dir_path.mkdir(parents=True, exist_ok=True)

    #file setup - get first subreddit name
    filename_counter = 0
    data_filename = subreddits[0] + f'{filename_counter:05d}.txt'
    data_filepath = dir_path / data_filename

    try:
        data_file = open(data_filepath, 'a', encoding='utf-8')
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

    with requests.Session() as s:
        #generic user agent so that we aren't marked as a bot.
        s.headers.update({
                'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
            })

        #for results file
        total_posts = 0
        total_comments = 0
        
        for subreddit in subreddits:
            #user post limit
            post_limit_flag = False
            subreddit_posts_count = 0

            # limit=100 - reddit only allows 100 posts per page
            subreddit_url = 'https://old.reddit.com/r/' + subreddit + '/' + args.category + '/?limit=100'
            print(f'Beginning scrape for: {subreddit}')

            #for each next button page
            while True:
                try:
                    #send subreddit home page http request for html
                    print(f'fetching r/{subreddit} html')
                    subreddit_response = s.get(subreddit_url, timeout=10)
                    subreddit_response.raise_for_status()
                    time.sleep(2.5) 
                except Exception as e: #if can't find subreddit url move to next subreddit
                    print(f'Error: {e}')
                    time.sleep(2.5) #very basic rate limiter
                    break

                #html parser object
                subreddit_soup = BeautifulSoup(subreddit_response.content, 'html.parser')

                #only posts have data-rank attribute
                posts = subreddit_soup.find_all('div', attrs={'data-rank' : True} )
                post_urls = []
                for post in posts:
                    post_urls.append('https://old.reddit.com' + post.get('data-permalink'))
                    
                for url in post_urls:
                    try:
                        #send post page http request for html
                        print(f'Fetching post: {url}')
                        post_response = s.get(url, timeout=10)
                        post_response.raise_for_status()
                        time.sleep(2.5) 
                    except Exception as e:  #if can't find post url move to next url
                        print(f'Error: {e}')
                        time.sleep(2.5) 
                        continue
                    

                    page_soup = BeautifulSoup(post_response.content, 'html.parser')
                    #only the post has 'sitetable linklisting' not comments
                    page_post = page_soup.find(class_='sitetable linklisting').find('div')

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

                    is_dupe = detect_duplicates(post_data, unique_posts)
                    
                    #write post to data_file
                    if not is_dupe:
                        try:
                            data_file, filename_counter = write_with_check(post_data, data_file, subreddit, filename_counter)
                        except Exception as e:
                            print(f'Error: {e}')
                            sys.exit(1)
                        total_posts += 1
                        subreddit_posts_count += 1
                    
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

                        is_dupe = detect_duplicates(post_data, unique_posts)

                        #write comment to data_file
                        if not is_dupe:
                            try:
                                data_file, filename_counter = write_with_check(comment_data, data_file, subreddit, filename_counter)
                            except Exception as e:
                                print(f'Error: {e}')
                                sys.exit(1)
                            total_comments += 1

                    print(f'Finished parsing:\n')

                    #user set limit
                    if subreddit_posts_count >= args.posts:
                        print(f'Subreddit post limit reached')
                        post_limit_flag = True
                        break

                #stop getting new next buttons
                if post_limit_flag:
                    break
                    
                #traverse next-button
                subreddit_url = subreddit_soup.find('span', class_='next-button')
                if subreddit_url:
                    subreddit_url = subreddit_url.find('a').get('href')
                else:
                    print(f'Fully scraped: r/{subreddit}')
                    break
                
            #force new filenames for new subreddit
            data_file.close()
            print(f'Closed last file for {subreddit}')

    results_file(dir_path, total_posts, total_comments)



  
            


def main() -> None:
    scrape_reddit()

#keep for vscode debugger
if __name__ == '__main__':
    main()


#OPTIMIZATIONS MADE
#1. switched from requests to sessions with TCP keep connection alive to reduce overhead
#2. 

#TO-DO
#if 429 too many requests, implement big sleep of 5-10 seconds
#-multithreading
#-dynamic rate limiter
#-slightly randomized delays

#FIXES
#PRAW module needs lengthy approval ---> use beautiful soup
#-fix 'Reddit - Please wait for verification' issue ---> use old.reddit.com

#challenges
#data-url and data-permalink are usually the same, except for when a link is attached to a post
#1000 post limit per sorting method (new, hot, top, etc)