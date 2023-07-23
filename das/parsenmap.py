#!/usr/bin/env python3

import socket
from pathlib import Path

import nmap
from tinydb import TinyDB, Query

from das.common import Logger


class NmapParser:
	"""Class for parsing Nmap XML reports by service names and print entries in format {service}://{host}:{port}}."""

	def __init__(self, db_path, services, dns, raw_output=False):
		"""
		Constructor.

		:param db_path: a TinyDB database file path
		:type db_path: str
		:param services: a string with comma-separated service names
		:type services: str
		:param dns: a boolean flag which, when presented, indicates that domain names associated with corresponding IPs must be printed
		:type dns: bool
		:param raw_output: a boolean flag which, when presented, indicates that results must be printed in a raw list (no decorations or colors)
		:type raw_output: bool
		:return: class object
		:rtype: das.report.NmapParser
		"""
		self.services = services.split(',')
		self.dns = dns

		if dns:
			self.db = TinyDB(db_path)
			self.ip_domains_dict = {}
			for item in self.db.all():
				self.ip_domains_dict[item['ip']] = item['domains']

		self.raw_output = raw_output

		db_name = Path(db_path).stem
		P = (Path.home() / '.das' / f'nmap_{db_name}').glob('*.xml')
		P = list(P)

		xml_reports = {x for x in P if not x.stem.startswith('port')}
		self.xml_reports = [str(r) for r in sorted(xml_reports, key=lambda x: socket.inet_aton(x.stem.replace('-', '.')))]

	def parse(self):
		"""Print raw Nmap reports in simple text format."""
		nm = nmap.PortScanner()

		for xml_report in self.xml_reports:
			with open(xml_report, 'r') as f:
				nm.analyse_nmap_xml_scan(f.read())
			
			for ip in nm.all_hosts():
				if 'tcp' in nm[ip]:
					for port in nm[ip]['tcp']:
						if nm[ip]['tcp'][port]['state'] == 'open':
							service = nm[ip]['tcp'][port]['name']
							if service in self.services:
								if self.dns:
									domains = self.ip_domains_dict[ip]
									if domains:
										for domain in domains:
											if not self.raw_output:
												Logger.print_success(f'IP {ip} -> {service}://{domain}:{port}')
											else:
												print(f'{service}://{domain}:{port}')
										continue
								if not self.raw_output:
									Logger.print_success(f'{service}://{ip}:{port}')
								else:
									print(f'{service}://{ip}:{port}')
