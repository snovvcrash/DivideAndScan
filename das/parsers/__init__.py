#!/usr/bin/env python3

import os
from datetime import datetime
from abc import ABC, abstractmethod

from tinydb import TinyDB

from das.common import Logger


class IAddPortscanOutput(ABC):
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
		:rtype: das.parsers.IAddPortscanOutput
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
