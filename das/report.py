#!/usr/bin/env python3

# Based on: https://github.com/CBHue/nMap_Merger
# Original author: Hue B. Solutions LLC, CBHue

import os
import socket
from pathlib import Path
from collections import namedtuple
from xml.etree.ElementTree import SubElement

import defusedxml.ElementTree as ET
from netaddr import IPNetwork
from tinydb import TinyDB, Query

from das.common import Logger


class NmapMerger:
	"""Class for merging separate Nmap outputs into a single report in different formats."""

	def __init__(self, db_path, hosts, ports, output=None):
		"""
		Constructor.

		:param db_path: a TinyDB database file path
		:type db_path: str
		:param hosts: a string with comma-separated Nmap reports (ip-like filenames) to merge ("all" for all the reports in Nmap directory with host-like filenames)
		:type hosts: str
		:param ports: a string with comma-separated Nmap reports (port-like filenames) to merge ("all" for all the reports in Nmap directory with port-like filenames)
		:type ports: str
		:param output: dictionary containing output type information and desired output filename
		:type output: dict
		:return: class object
		:rtype: das.report.NmapMerger
		"""
		if output:
			for fmt, name in output.items():
				if name:
					Report = namedtuple('Report', 'format filename')
					self.output = Report(fmt, name)
		else:
			self.output = None

		self.db = None
		self.db_path = db_path

		db_name = Path(db_path).stem
		P = (Path.home() / '.das' / f'nmap_{db_name}').glob('*.*')
		P = list(P)

		if hosts:
			try:
				if Path(hosts).exists():
					with open(hosts, 'r') as fd:
						hosts = ','.join(i.strip() for i in fd.read().splitlines())
			except OSError:  # catching [Errno 36] File name too long
				pass

			if hosts == 'all':
				self.nmap_reports = {x for x in P if not x.stem.startswith('port')}
			else:
				hosts = hosts.split(',')
				hosts = [IPNetwork(h) for h in hosts]
				hosts = [str(ip).replace('.', '-') for ip_obj in hosts for ip in ip_obj]
				self.nmap_reports = {x for h in hosts for x in P if h == x.stem}

		elif ports:
			try:
				if Path(ports).exists():
					with open(ports, 'r') as fd:
						ports = ','.join(i.strip() for i in fd.read().splitlines())
			except OSError:  # catching [Errno 36] File name too long
				pass

			if ports == 'all':
				self.nmap_reports = {x for x in P if x.stem.startswith('port')}
			else:
				ports = ports.split(',')
				self.nmap_reports = {x for p in ports for x in P if f'port{p}' == x.stem}

	def xml_to_html(self, merged_xml):
		"""
		Convert merged Nmap XML report to HTML report.

		:param merged_xml: merged Nmap XML report filename
		:type merged_xml: str
		"""
		xsltproc = Path('/usr/bin/xsltproc')
		if xsltproc.exists():
			merged_html = f'{self.output.filename}.html'
			command = f'{str(xsltproc)} {merged_xml} -o {merged_html}'
			os.system(command)
			P = Path.cwd() / merged_html
			if P.exists():
				Logger.print_success(f'Merged HTML report -> {P.resolve()}')
		else:
			Logger.print_error(f'{xsltproc}: binary does not exist, install with "sudo apt install xsltproc -y"')

	def show(self):
		"""Print raw Nmap reports in simple text format."""
		text_reports = [r for r in self.nmap_reports if r.suffix == '.nmap']
		total_reports = len(text_reports)
		Logger.print_info(f'Total reports -> {total_reports}')

		try:
			sorted_reports = [str(r) for r in sorted(text_reports, key=lambda x: socket.inet_aton(x.stem.replace('-', '.')))]
		except OSError:
			sorted_reports = [str(r) for r in sorted(text_reports)]

		i = 1
		for report in sorted_reports:
			Logger.print_separator(report, prefix=f'{i}/{total_reports}')
			os.system(f'cat {report}')
			i += 1

	def generate(self):
		"""Perform all the steps needed to generate a single Nmap report."""
		self.db = TinyDB(self.db_path)
		self.Host = Query()

		if self.output.format in ('oX', 'oA'):
			merged_xml = f'{self.output.filename}.xml'
			for report in self.nmap_reports:
				if report.suffix == '.xml':
					d = self.get_header_dict(report)
					self.add_header(merged_xml, d)
					break

			Logger.print_info(f'Merging {len([r for r in self.nmap_reports if r.suffix == ".xml"])} XML reports')

			host_num = 0
			for report in self.nmap_reports:
				if report.suffix == '.xml':
					Logger.print_info(f'Processing XML report -> {report}')
					n = self.merge_nmap(report, merged_xml)
					host_num = host_num + n

			P = Path.cwd() / merged_xml
			if P.exists():
				Logger.print_success(f'Merged XML report -> {P.resolve()}')

			self.add_footer(merged_xml, host_num)
			self.xml_to_html(merged_xml)

		if self.output.format in ('oN', 'oA'):
			text_reports = [r for r in self.nmap_reports if r.suffix == '.nmap']

			try:
				sorted_reports = ' '.join(str(r) for r in sorted(text_reports, key=lambda x: socket.inet_aton(x.stem.replace('-', '.'))))
			except OSError:
				sorted_reports = ' '.join(str(r) for r in sorted(text_reports))

			if sorted_reports:
				merged_text = f'{self.output.filename}.nmap'
				os.system(f'cat {sorted_reports} > {merged_text}')
				P = Path.cwd() / merged_text
				if P.exists():
					Logger.print_success(f'Merged simple text report -> {P.resolve()}')
			else:
				Logger.print_error('No reports that meet the search criteria')

		if self.output.format in ('oG', 'oA'):
			grepable_reports = [r for r in self.nmap_reports if r.suffix == '.gnmap']

			try:
				sorted_reports = ' '.join(str(r) for r in sorted(grepable_reports, key=lambda x: socket.inet_aton(x.stem.replace('-', '.'))))
			except OSError:
				sorted_reports = ' '.join(str(r) for r in sorted(grepable_reports))

			if sorted_reports:
				merged_grepable = f'{self.output.filename}.gnmap'
				os.system(f'cat {sorted_reports} > {merged_grepable}')
				P = Path.cwd() / merged_grepable
				if P.exists():
					Logger.print_success(f'Merged grepable report -> {P.resolve()}')
			else:
				Logger.print_error('No reports that meet the search criteria')

	@staticmethod
	def get_header_dict(xml_report):
		"""
		Extract metadata from XML header of a raw Nmap XML report.

		:param xml_report: raw Nmap XML report filename
		:type xml_report: pathlib.PosixPath
		:return: a dictionary containing XML metadata
		:rtype: dict
		"""
		tree = ET.parse(xml_report)
		root = tree.getroot()
		nmaprun = root.attrib
		scaninfo = root.find('scaninfo').attrib
		merged = {**nmaprun, **scaninfo}

		d = {}
		for key, value in merged.items():
			d[key] = value.replace('"', '&quot;')

		return d

	@staticmethod
	def add_header(merged_xml, d):
		"""
		Add XML header to the intermediate merged Nmap XML report.

		:param merged_xml: intermediate merged Nmap XML report filename
		:type merged_xml: str
		:param d: dictionary containing XML metadata
		:type d: dict
		"""
		nmap_header = '<?xml version="1.0" encoding="UTF-8"?>'
		nmap_header += '<!DOCTYPE nmaprun>'
		nmap_header += '<?xml-stylesheet href="file:///usr/share/nmap/nmap.xsl" type="text/xsl"?>'
		nmap_header += '<!-- Nmap scan initiated by DivideAndScan: https://github.com/snovvcrash/DivideAndScan -->'
		nmap_header += '<!-- Nmap reports merged with nMap_Merger: https://github.com/CBHue/nMap_Merger -->'
		nmap_header += f'''<nmaprun scanner="{d['scanner']}" args="(Example) {d['args']}" start="0" startstr="Thu Jan  1 00:00:00 1970" version="{d['version']}" xmloutputversion="{d['xmloutputversion']}">'''
		nmap_header += f'''<scaninfo type="{d['type']}" protocol="{d['protocol']}" numservices="0" services="0"/>'''
		nmap_header += '<verbose level="0"/>'
		nmap_header += '<debugging level="0"/>'

		with open(merged_xml, 'w') as fd:
			fd.write(nmap_header)

	@staticmethod
	def add_footer(merged_xml, n):
		"""
		Add XML footer to the merged Nmap XML report.

		:param merged_xml: merged Nmap XML report filename
		:type merged_xml: str
		:param n: number of hosts in merged Nmap XML report
		:type n: int
		"""
		nmap_footer = f'<runstats><finished time="0" timestr="Thu Jan  1 00:00:00 1970" elapsed="0" summary="Nmap done at Thu Jan  1 00:00:00 1970; {str(n)} IP address scanned in 0.0 seconds" exit="success"/>'
		nmap_footer += '</runstats>'
		nmap_footer += '</nmaprun>'

		with open(merged_xml, 'a') as mfd:
			mfd.write(nmap_footer)

	def merge_nmap(self, xml_file, merged_xml):
		"""
		Add another Nmap XML report contents to the intermediate merged XML report.

		:param xml_file: current Nmap XML report filename to be merged
		:type xml_file: pathlib.PosixPath
		:param merged_xml: intermediate merged Nmap XML report filename
		:type merged_xml: str
		:return: the number of hosts in current Nmap XML report
		:rtype: int
		"""
		with open(merged_xml, mode='a', encoding='utf-8') as mfd:
			with open(xml_file) as fd:
				nmap_xml, n = ET.parse(fd), 0
				for host in nmap_xml.findall('host'):
					hostnames = host.find('hostnames')
					if hostnames is not None:
						ip = host.find('address').attrib['addr']
						try:
							domains = self.db.search(self.Host.ip == ip)[0]['domains']
						except:
							pass
						else:
							if domains:
								for domain in domains:
									hostname = SubElement(hostnames, 'hostname')
									hostname.set('name', domain)
									hostname.set('type', 'A')

					chost = ET.tostring(host, encoding='unicode', method='xml')
					mfd.write(chost)
					mfd.flush()
					n += 1

		return n
