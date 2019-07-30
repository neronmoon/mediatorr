FROM python:3

COPY . /opt/app
WORKDIR /opt/app
RUN pip install -r requirements.yml

CMD python ./console
