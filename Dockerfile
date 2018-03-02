FROM python:3.6-alpine

RUN apk --no-cache add \
    python3 \
    git \
    libpq \
    wget \
    libffi \
    libffi-dev \
    ca-certificates \
    python3-dev \
    postgresql-dev \
    build-base \
    bash \
    curl
RUN update-ca-certificates

WORKDIR /app
ADD requirements.txt .
RUN pip install -r requirements.txt

ADD . .

COPY docker/startup.sh /startup.sh
COPY docker/docker-entrypoint.sh /entrypoint.sh

EXPOSE 8000

CMD ["/startup.sh"]
ENTRYPOINT ["/entrypoint.sh"]
