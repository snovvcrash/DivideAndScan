#!/usr/bin/env python3

from collections import defaultdict

from tinydb import TinyDB

with open('scan.txt') as f:
    # fmt -> 127.0.0.1:1337
    scan = f.read().splitlines()

# dnsx -l domains.txt -re -silent -o dnsx.txt
with open('dnsx.txt') as f:
    dnsx = f.read().splitlines()

domains = defaultdict(set)
for line in dnsx:
    domain, ip = line.split()
    if domain.startswith('xn--'):
        domain = domain.encode().decode('idna')
    ip = ip.replace('[', '').replace(']', '')
    domains[ip].add(domain)

items = [{'ip': ip, 'port': port, 'domains': list(domains[ip])} for ip, port in (line.split(':') for line in scan)]

db = TinyDB('db.json')
db.truncate()
db.insert_multiple(items)
