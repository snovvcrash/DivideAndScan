#!/usr/bin/env python3

import os
import shutil
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

from tinydb import TinyDB

from das.common import Logger


class IAddPortscanOutput(ABC):
	"""Base class for updating DB with parsed portscan output."""

	def __init__(self, db_path, rm, scanner_name, scanner_args):
		"""
		Constructor.

		:param db_path: a TinyDB database file path
		:type db_path: str
		:param rm: a flag showing if we need to drop the DB before updating its values
		:type rm: bool
		:param scanner_name: name of the port scanner to run
		:type scanner_name: str
		:param scanner_args: port scanner arguments
		:type scanner_args: str
		:return: base class object
		:rtype: das.parsers.IAddPortscanOutput
		"""
		self.db = TinyDB(db_path)
		if rm:
			self.db.truncate()

		raw_directory_path = Path.home() / '.das' / 'db' / 'raw'
		scanner_path = Path(scanner_args)

		is_import = False
		if len(str(scanner_path)) < 255 and scanner_path.is_file():
			self.portscan_out = raw_directory_path / scanner_path.name
			shutil.copy2(scanner_path, self.portscan_out)
			is_import = True
		else:
			self.portscan_out = raw_directory_path / f'{scanner_name}-{datetime.now().strftime("%Y%m%dT%H%M%S")}.out'
			self.command = f"""sudo {scanner_name} {scanner_args} | tee {self.portscan_out}"""

			Logger.print_cmd(self.command)
			os.system(self.command)

		with open(self.portscan_out, 'r+', encoding='utf-8') as fd:
			content = fd.read()
			if not is_import:
				fd.seek(0)
				fd.write(f'# {self.command}\n\n{content}')
			self.portscan_raw = content.splitlines()

	@abstractmethod
	def parse(self):
		"""Interface for a parsing method."""
		raise NotImplementedError
