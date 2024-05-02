FROM python:3

RUN apt-get -y update
RUN apt-get install -y ffmpeg

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -U --pre yt-dlp

COPY . /usr/src/app

EXPOSE 8080

VOLUME ["/usr/src/app/gallery-dl"]

CMD [ "python3", "./gallery_dl_server.py" ]