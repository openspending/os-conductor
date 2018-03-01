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

ENV OS_CONDUCTOR_CACHE=cache:11211
ENV OS_API=os-api-loader:8000
ENV OS_CONDUCTOR=os-conductor:8000

COPY docker/startup.sh /startup.sh

EXPOSE 8000

CMD ["/startup.sh"]
