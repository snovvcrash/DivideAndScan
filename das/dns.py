#!/usr/bin/env python3

import os
import tempfile
from pathlib import Path
from collections import defaultdict

import dns.resolver
from tinydb import TinyDB, Query
from tinydb.operations import add

from das.common import Logger, run_command


class DNS:
	"""Class for mapping domain names (taken from an input file) to corresponding IP addresses (taken from the DB)."""

	def __init__(self, db_path, domains_path):
		"""
		Constructor.

		:param db_path: a TinyDB database file path
		:type db_path: str
		:param domains_path: an input file path with newline-separated domain names
		:type domains_path: pathlib.PosixPath
		"""
		self.db = TinyDB(db_path)
		self.Host = Query()

		with open(domains_path, 'r') as f:
			self.domains = set(f.read().splitlines())

	def resolve(self):
		"""Resolve domain names taken from the input file and put them to the DB."""
		Logger.print_info(f'Domain names to resolve -> {len(self.domains)}')

		for domain in self.domains:
			try:
				answers = dns.resolver.resolve(domain, 'A')
			except:
				continue

			doc_ids = []
			for ip in answers:
				result = self.db.search(self.Host.ip == str(ip))

				found = False
				if result:
					Logger.print_success(f'IP {str(ip)} -> {domain}')

					for item in result:
						if domain not in item['domains']:
							doc_ids.append(item.doc_id)
					found = True

			if doc_ids:
				self.db.update(add('domains', [domain]), doc_ids=doc_ids)
			elif not found:
				Logger.print_warning(f'None -> {domain}')

	def update(self):
		"""Update existing DB with new domains names (taken from an input file).

		:return: number of hosts updated with domain names in the DB
		:rtype: int
		"""

		with tempfile.NamedTemporaryFile('w', suffix='.txt') as tmp:
			dnsx_path = Path(tempfile.gettempdir()) / 'dnsx.txt'
			domains_punycode = [domain.encode('idna').decode() + '\n' for domain in self.domains]
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

		items, hosts = self.db.all(), set()
		for i in range(len(items)):
			ip = items[i]['ip']
			if ip in domains:
				t = set(items[i]['domains'])
				t.update(domains[ip])
				items[i]['domains'] = list(t)
				hosts.add(ip)

		self.db.truncate()
		self.db.insert_multiple(items)

		return len(hosts)
