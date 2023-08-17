#!/usr/bin/env bash

# Nmap

apt install nmap xsltproc -y
nmap --script-updatedb

# Masscan

pushd /tmp 2>&1 > /dev/null
wget https://github.com/ivre/masscan/archive/refs/heads/master.zip -O masscan-master.zip
unzip -q masscan-master.zip
cd masscan-master
make
make install
popd 2>&1 > /dev/null && rm -rf /tmp/masscan-master*

# RustScan

pushd /tmp 2>&1 > /dev/null

# https://github.com/RustScan/RustScan/releases/2.0.1
wget https://api.github.com/repos/RustScan/RustScan/releases/33533387 -qO- \
| grep "browser_download_url.*amd64.deb" \
| cut -d: -f2,3 \
| tr -d \" \
| wget -qO rustscan.deb -i-

dpkg -i rustscan.deb
wget https://gist.github.com/snovvcrash/8b85b900bd928493cd1ae33b2df318d8/raw/fe8628396616c4bf7a3e25f2c9d1acc2f36af0c0/rustscan-ports-top1000.toml -O /root/.rustscan.toml
popd 2>&1 > /dev/null && rm /tmp/rustscan.deb

# Naabu

mkdir /opt/naabu
pushd /opt/naabu 2>&1 > /dev/null

wget https://api.github.com/repos/projectdiscovery/naabu/releases/latest -qO- \
| grep "browser_download_url.*linux_amd64.zip" \
| cut -d: -f2,3 \
| tr -d \" \
| wget -qO naabu.zip -i-

unzip -q naabu.zip
chmod +x naabu
ln -s `readlink -f naabu` /usr/local/bin/naabu
popd 2>&1 > /dev/null && rm /opt/naabu/naabu.zip

# NimScan

mkdir /opt/nimscan
pushd /opt/nimscan 2>&1 > /dev/null

wget https://api.github.com/repos/elddy/NimScan/releases/latest -qO- \
| grep 'browser_download_url.*NimScan"' \
| cut -d: -f2,3 \
| tr -d \" \
| wget -qO nimscan -i-

chmod +x nimscan
ln -s `readlink -f nimscan` /usr/local/bin/nimscan
popd 2>&1 > /dev/null

# sx

mkdir /opt/sx
pushd /opt/sx 2>&1 > /dev/null

wget https://api.github.com/repos/v-byte-cpu/sx/releases/latest -qO- \
| grep "browser_download_url.*linux_amd64.tar.gz" \
| cut -d: -f2,3 \
| tr -d \" \
| wget -qO sx.tar.gz -i-

tar -xzf sx.tar.gz
chmod +x sx
ln -s `readlink -f sx` /usr/local/bin/sx
popd 2>&1 > /dev/null && rm /opt/sx/sx.tar.gz

# dnsx

mkdir /opt/pd
pushd /opt/pd 2>&1 > /dev/null

wget https://api.github.com/repos/projectdiscovery/dnsx/releases/latest -qO- \
| grep "browser_download_url.*linux_amd64.zip" \
| cut -d: -f2,3 \
| tr -d \" \
| wget -qO dnsx.zip -i-

unzip -q dnsx.zip
chmod +x dnsx
ln -s `readlink -f dnsx` /usr/local/bin/dnsx
popd 2>&1 > /dev/null && rm /opt/pd/dnsx.zip

# DivideAndScan

cd /app
pip3 install .
