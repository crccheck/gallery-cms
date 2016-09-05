FROM python:3

# Install requirements
RUN apt-get -qq update && \
    apt-get install -y libexiv2-dev libboost-python-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
ADD requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

# Install app
COPY . /app

ENV PORT 8080
EXPOSE 8080
