FROM python:3.6-alpine

RUN apk add --update --no-cache libpq postgresql-dev libffi libffi-dev bash
RUN apk add --update --no-cache --virtual=build-dependencies build-base 

WORKDIR /app
ADD requirements.txt .
RUN pip install -r requirements.txt

RUN apk del build-dependencies
RUN rm -rf /var/cache/apk/*

ADD . .

COPY docker/startup.sh /startup.sh
COPY docker/docker-entrypoint.sh /entrypoint.sh

EXPOSE 8000

CMD ["/startup.sh"]
ENTRYPOINT ["/entrypoint.sh"]
