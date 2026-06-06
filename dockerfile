FROM coady/pylucene:latest
WORKDIR /app
COPY  ./reddit-scraper /app
CMD ["python3"]
