FROM amd64/ubuntu:20.04
LABEL maintainer="snovvcrash@protonmail.ch"
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt update && apt install python3.9 python3.9-distutils sudo make gcc unzip wget tree -y
RUN wget -qO- https://bootstrap.pypa.io/pip/get-pip.py | /usr/bin/python3.9
COPY . /app
WORKDIR /app
RUN bash docker-install.sh
ENTRYPOINT ["das"]
