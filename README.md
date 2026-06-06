# How to Install: *windows
```bash
# Clone the repository
git clone https://github.com/slow-poker/reddit-scraper.git
cd reddit-scraper

# Install dependencies
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

# Syntax Usage
```text
usage: reddit_scraper.py [-h] (-f FILE | -t SUB1 [SUB1 ...]) [-p POSTS] [-c {hot,new,rising,controversial,top}]
                         [-s SIZE]

Group 5 Reddit Web Scraper Part A

options:
  -h, --help                                        show this help message and exit
  -f FILE, --file FILE                              File path to subreddit list
  -t SUB1 [SUB1 ...], --text SUB1 [SUB1 ...]        Subreddit name(s)
  -p POSTS, --posts POSTS                           Max posts to pull per subreddit [0-1000]
  -c {hot,new,rising,controversial,top}, --category {hot,new,rising,controversial,top}
                                                    sort by categories before scraping
  -s SIZE, --size SIZE                              File chunk sizes for data in MB or KB
```

# Example Usage
```text
python .\reddit_scraper.py -f subreddits.txt -p 300 -s 10MB -c new
-f  take in the newline delimited list of subreddits from subreddits.txt
-p  scrape 300 posts from each subreddit given
-s  store the data in files of size 10MB
-c  sort by new while scraping
```

---
# Setup Indexer 
This should work in both powershell and bash, simply copy and paste it into your terminal.

Requires Docker to be installed

Windows: https://docs.docker.com/desktop/setup/install/windows-install/

Mac: https://docs.docker.com/desktop/setup/install/mac-install/
```bash
#download repo
git clone https://github.com/dillonhoh/reddit-scraper.git
cd reddit-scraper

#build and run container
docker build -t 172index .
docker run -dit -p 127.0.0.1:5000:5000 --name 172index 172index

#download dependencies
docker exec 172index pip install -r requirements.txt

#run indexer
docker exec 172index python3 index_reddit.py "newscrape/gaming00000.txt" reddit_index

#run webapge at http://127.0.0.1:5000/
docker exec 172index python3 app.py
cd ..

#to stop the container run:
#docker stop 172index
#docker rm 172index
```
