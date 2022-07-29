FROM python:3.9

WORKDIR /opt/app
COPY requirements.txt /opt/app
RUN pip install -r requirements.txt
COPY . /opt/app

CMD python ./console start
