#!/usr/bin/env python3

import os
import ast
from datetime import datetime
from abc import ABC, abstractmethod

from tinydb import TinyDB

from das.modules.common import Logger


class AddOutputBase(ABC):
	"""Base class for updating DB with parsed portscan output."""

	def __init__(self, db, rm, scanner_name, scanner_args):
		"""
		Constructor.

		:param db: a tinydb database file path
		:type db: tinydb.TinyDB
		:param rm: a flag showing if we need to drop the DB before updating its values
		:type rm: bool
		:param scanner_name: name of the port scanner to run
		:type scanner_name: str
		:param scanner_args: port scanner arguments
		:type scanner_args: str
		:return: base class object
		:rtype: das.modules.add.AddOutputBase
		"""
		self.db = TinyDB(db)
		if rm:
			self.db.truncate()

		self.portscan_out = f'.db/raw/{scanner_name}-{datetime.now().strftime("%Y%m%dT%H%M%S")}.out'
		self.command = f"""sudo {scanner_name} {scanner_args} | tee {self.portscan_out}"""

		Logger.print_cmd(self.command)
		os.system(self.command)

		with open(self.portscan_out, 'r', encoding='utf-8') as fd:
			self.portscan_raw = fd.read().splitlines()

	@abstractmethod
	def parse(self):
		"""Interface for a parsing method."""
		raise NotImplementedError


class AddMasscanOutput(AddOutputBase):
	"""Child class for processing Masscan output."""

	def parse(self):
		"""
		Masscan raw output parser.

		:return: a pair of values (portscan raw output filename, number of hosts added to DB)
		:rtype: tuple
		"""
		hosts = set()
		for line in self.portscan_raw:
			try:
				ip = line.split()[-1]
				port, proto = line.split()[3].split('/')
			except:
				pass
			else:
				if proto == 'tcp':
					item = {'ip': ip, 'port': int(port)}
					if item not in self.db:
						self.db.insert(item)

				hosts.add(ip)

		return (self.portscan_out, len(hosts))


class AddRustscanOutput(AddOutputBase):
	"""Child class for processing RustScan output."""

	def parse(self):
		"""
		RustScan raw output parser.

		:return: a pair of values (portscan raw output filename, number of hosts added to DB)
		:rtype: tuple
		"""
		hosts = set()
		for line in self.portscan_raw:
			try:
				ip, ports = line.split(' -> ')
			except:
				pass
			else:
				for port in ast.literal_eval(ports):
					item = {'ip': ip, 'port': port}
					if item not in self.db:
						self.db.insert(item)

				hosts.add(ip)

		return (self.portscan_out, len(hosts))


class AddNaabuOutput(AddOutputBase):
	"""Child class for processing Naabu output."""

	def parse(self):
		"""
		Naabu raw output parser.

		:return: a pair of values (portscan raw output filename, number of hosts added to DB)
		:rtype: tuple
		"""
		hosts = set()
		for line in self.portscan_raw:
			try:
				ip, port = line.split(':')
			except:
				pass
			else:
				item = {'ip': ip, 'port': int(port)}
				if item not in self.db:
					self.db.insert(item)

				hosts.add(ip)

		return (self.portscan_out, len(hosts))
