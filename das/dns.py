#!/usr/bin/env python3

import dns.resolver
from tinydb import TinyDB, Query
from tinydb.operations import add

from das.common import Logger

class DNS:
	"""Class for associating domain names (taken from an input file) with corresponding IP addresses (taken from the DB)."""

	def __init__(self, db_path, domains_path):
		"""
		Constructor.

		:param db_path: a TinyDB database file path
		:type db_path: pathlib.PosixPath
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
			answers = dns.resolver.resolve(domain, 'A')

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
