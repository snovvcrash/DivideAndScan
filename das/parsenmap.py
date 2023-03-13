#!/usr/bin/env python3

import socket
from pathlib import Path

import nmap
from tinydb import TinyDB, Query

from das.common import Logger

class NmapParser:

	def __init__(self, db_path, ports, dns, raw_output=False):
		self.ports = [int(port) for port in ports.split(',')]
		
		self.db = None
		if dns:
			self.db = TinyDB(db_path)
			self.Host = Query()

		self.raw_output = raw_output

		db_name = Path(db_path).stem
		P = (Path.home() / '.das' / f'nmap_{db_name}').glob('*.xml')
		P = list(P)

		xml_reports = {x for x in P if not x.stem.startswith('port')}
		self.xml_reports = [str(r) for r in sorted(xml_reports, key=lambda x: socket.inet_aton(x.stem.replace('-', '.')))]

	def parse(self):
		nm = nmap.PortScanner()

		for xml_report in self.xml_reports:
			with open(xml_report, 'r') as f:
				nm.analyse_nmap_xml_scan(f.read())
			
			for ip in nm.all_hosts():
				if 'tcp' in nm[ip]:
					for port in nm[ip]['tcp']:
						if nm[ip]['tcp'][port]['state'] == 'open':
							if port in self.ports:
								service = nm[ip]['tcp'][port]['name']
								if self.db:
									domains = self.db.search(self.Host.ip == ip)[0]['domains']
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
