FROM python:3

COPY requirements.txt /opt/app
RUN pip install -r requirements.txt

COPY . /opt/app
WORKDIR /opt/app

CMD python ./console start
