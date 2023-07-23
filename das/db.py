#!/usr/bin/env python3

import os
import tempfile
from pathlib import Path
from collections import defaultdict

from tinydb import TinyDB

from das.common import Logger, run_command


class DB:
	"""Class for utilities that serve for manual DB manipulations."""

	def __init__(self, db_path):
		"""
		Constructor.

		:param db_path: a TinyDB database file path
		:type db_path: str
		"""
		self.db = TinyDB(db_path)

	def create_generic(self, scan_path, domains_path=None):
		"""Create TinyDB from a generic scan output and a list of domain names (projectdiscovery/dnsx must be in PATH).
		
		:param scan_path: an input file path with newline-separated scan output
		:type scan_path: pathlib.PosixPath
		:param domains_path: an input file path with newline-separated domain names
		:type domains_path: pathlib.PosixPath
		:return: number of hosts added to DB
		:rtype: int
		"""
		with open(scan_path) as f:
			# fmt -> 127.0.0.1:1337
			scan = f.read().splitlines()

		if domains_path:
			with open(domains_path) as f:
				domains = set(f.read().splitlines())

			with tempfile.NamedTemporaryFile('w', suffix='.txt') as tmp:
				dnsx_path = Path(tempfile.gettempdir()) / 'dnsx.txt'
				domains_punycode = [domain.encode('idna').decode() + '\n' for domain in domains]
				tmp.writelines(domains_punycode)
				run_command(f'dnsx -l {tmp.name} -re -silent -o {dnsx_path}')

			with open(dnsx_path) as f:
				dnsx = f.read().splitlines()

			Logger.print_info(f'Resolved {len(dnsx)} DNS records')
			os.remove(dnsx_path)

			domains = defaultdict(set)
			for line in dnsx:
				domain, ip = line.split()
				domain = domain.encode().decode('idna')
				ip = ip.replace('[', '').replace(']', '')
				domains[ip].add(domain)

			items = [{'ip': ip, 'port': int(port), 'domains': list(domains[ip])} for ip, port in (line.split(':') for line in scan)]
		else:
			items = [{'ip': ip, 'port': int(port), 'domains': []} for ip, port in (line.split(':') for line in scan)]

		self.db.truncate()
		self.db.insert_multiple(items)

		return len(set([i['ip'] for i in items]))
