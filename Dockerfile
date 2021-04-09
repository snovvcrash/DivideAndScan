FROM amd64/ubuntu:20.04
LABEL maintainer="snovvcrash@protonmail.ch"
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt update && apt install software-properties-common build-essential python3-pip wget git -y
COPY . /app
WORKDIR /app
RUN bash docker-install.sh
ENTRYPOINT ["das"]
