FROM python:3.7-slim-stretch

RUN apt update
RUN apt install -y python3-dev gcc unzip

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app app/

RUN python app/server.py

EXPOSE 8080

CMD ["python", "app/server.py", "serve"]