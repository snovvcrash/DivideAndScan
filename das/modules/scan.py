#!/usr/bin/env python3

import os
import socket
from pathlib import Path
from abc import abstractmethod
from collections import defaultdict
from tempfile import NamedTemporaryFile
from multiprocessing import current_process
from concurrent.futures import ProcessPoolExecutor

from tinydb import TinyDB, Query
from netaddr import IPNetwork

from das.modules.common import Logger


class ScanBase:
	"""Base class for searching DB and/or initiating Nmap scans."""

	def __init__(self, db, hosts, ports):
		"""
		Constructor.

		:param db: a tinydb database file path
		:type db: tinydb.TinyDB
		:param hosts: a list of hosts to interact with ("all" for all the hosts in DB)
		:type hosts: list
		:param ports: a list of ports to interact with ("all" for all the ports in DB)
		:type ports: list
		:return: base class object
		:rtype: das.modules.scan.ScanBase
		"""
		self.db = TinyDB(db)
		self.Host = Query()
		self.total_scans = 0

		if hosts:
			if Path(hosts).exists():
				with open(hosts, 'r') as fd:
					hosts = ','.join(i.strip() for i in fd.read().splitlines())

			if hosts == 'all':
				result = self.db.all()
			else:
				hosts = hosts.split(',')
				hosts = [IPNetwork(h) for h in hosts]
				hosts = [str(ip) for ip_obj in hosts for ip in ip_obj]
				result = self.db.search(self.Host.ip.one_of(hosts))

			self.ip_dict = defaultdict(set)
			for item in result:
				self.ip_dict[item['ip']].add(item['port'])

			self.total_scans += len(self.ip_dict)

		elif ports:
			if Path(ports).exists():
				with open(ports, 'r') as fd:
					ports = ','.join(i.strip() for i in fd.read().splitlines())

			if ports == 'all':
				result = self.db.all()
			else:
				ports = [int(p) for p in ports.split(',')]
				result = self.db.search(self.Host.port.one_of(ports))

			self.port_dict = defaultdict(set)
			for item in result:
				self.port_dict[item['port']].add(item['ip'])

			self.total_scans += len(self.port_dict)

		Logger.print_info(f'Total scans -> {self.total_scans}')

	@abstractmethod
	def nmap_by_hosts(self):
		"""Interface for a DB host searching method."""
		raise NotImplementedError

	@abstractmethod
	def nmap_by_ports(self):
		"""Interface for a DB port searching method."""
		raise NotImplementedError


class ScanShow(ScanBase):
	"""Child class for searching through DB and printing the results."""

	def nmap_by_hosts(self):
		"""Search DB by hosts and print mapping "live_host -> [open_ports]". No Nmap scan is launched."""
		for ip, ports in sorted(self.ip_dict.items(), key=lambda x: socket.inet_aton(x[0])):
			sorted_ports = ','.join([str(p) for p in sorted(ports)])
			Logger.print_success(f'IP {ip} ({len(ports)}) -> [{sorted_ports}]')

	def nmap_by_ports(self):
		"""Search DB by ports and print mapping "open_port -> [live_hosts]". No Nmap scan is launched."""
		for port, ip_list in sorted(self.port_dict.items()):
			sorted_ip_list = ','.join(sorted(ip_list, key=socket.inet_aton))
			Logger.print_success(f'Port {port} ({len(ip_list)}) -> [{sorted_ip_list}]')


class ScanRun(ScanBase):
	"""Child class for initiating Nmap scans."""

	def nmap_by_hosts(self, nmap_opts, parallel):
		"""
		Search DB by hosts and launch Nmap scans for mappings "live_host -> [open_ports]".

		:param nmap_opts: custom Nmap options that will replace the default ones
		:type nmap_opts: str
		:param parallel: namedtuple('Parallelism', 'enabled processes')
		:type parallel: collections.namedtuple
		"""
		nmap_commands, i = [], 1
		for ip, ports in sorted(self.ip_dict.items(), key=lambda x: socket.inet_aton(x[0])):
			if not parallel.enabled:
				Logger.print_separator(f'IP: {ip}', prefix=f'{i}/{self.total_scans}')

			nmap_out = ip.replace('.', '-')
			sorted_ports = ','.join([str(p) for p in sorted(ports)])

			if nmap_opts is None:
				cmd = f"""sudo nmap -Pn -sV --version-intensity 6 -O -oA .nmap/{nmap_out} {ip} -p{sorted_ports}"""
			else:
				cmd = f"""sudo nmap {nmap_opts} -oA .nmap/{nmap_out} {ip} -p{sorted_ports}"""

			if parallel.enabled:
				cmd += ' > /dev/null 2>&1'
				nmap_commands.append(cmd)
			else:
				Logger.print_cmd(cmd)
				os.system(cmd)

			i += 1

		if parallel.enabled:
			with ProcessPoolExecutor(max_workers=parallel.processes) as executor:
				executor.map(nmap, nmap_commands)

	def nmap_by_ports(self, nmap_opts, parallel):
		"""
		Search DB by ports and launch Nmap scans for mappings "open_port -> [live_hosts]".

		:param nmap_opts: custom Nmap options that will replace the default ones
		:type nmap_opts: str
		:param parallel: namedtuple('Parallelism', 'enabled processes')
		:type parallel: collections.namedtuple
		"""
		nmap_commands, i = [], 1
		for port, ip_list in sorted(self.port_dict.items()):
			if not parallel.enabled:
				Logger.print_separator(f'Port: {port}', prefix=f'{i}/{self.total_scans}')

			nmap_out = f'port{port}'
			with NamedTemporaryFile('w+') as tmp:
				tmp.writelines(f'{i}\n' for i in ip_list)
				tmp.seek(0)

				if nmap_opts is None:
					cmd = f"""sudo nmap -Pn -sV --version-intensity 6 -O -oA .nmap/{nmap_out} -iL {tmp.name} -p{port}"""
				else:
					cmd = f"""sudo nmap {nmap_opts} -oA .nmap/{nmap_out} -iL {tmp.name} -p{port}"""

				sorted_ip_list = ','.join(sorted(ip_list, key=socket.inet_aton))
				Logger.print_cmd(f'{tmp.name}: {sorted_ip_list}')

				if parallel.enabled:
					cmd += ' > /dev/null 2>&1'
					nmap_commands.append(cmd)
				else:
					Logger.print_cmd(cmd)
					os.system(cmd)

				i += 1

		if parallel.enabled:
			with ProcessPoolExecutor(max_workers=parallel.processes) as executor:
				executor.map(nmap, nmap_commands)


def nmap(command):
	"""
	Helper function to run multiple Nmap processes in parallel.

	:param command: Nmap command to execute
	:type command: str
	"""
	Logger.print_cmd(command, parallel=current_process().name)
	os.system(command)
