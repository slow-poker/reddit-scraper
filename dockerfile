FROM coady/pylucene:latest
WORKDIR /app
COPY  . /app
CMD ["python3"]
