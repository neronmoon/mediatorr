FROM python:3

RUN apt-get update && apt-get install -y sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app
COPY requirements.txt /opt/app
RUN pip install -r requirements.txt
COPY . /opt/app

CMD python ./console start
