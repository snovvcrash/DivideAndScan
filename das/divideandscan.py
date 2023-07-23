#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from importlib import import_module
from collections import namedtuple
from argparse import ArgumentParser, RawTextHelpFormatter, RawDescriptionHelpFormatter

import das.common
from das.db import DB
from das.scan import ScanShow, ScanRun
from das.dns import DNS
from das.report import NmapMerger
from das.parsenmap import NmapParser
from das.common import BANNER, Logger


def parse_args():
	"""
	Process arguments.

	:return: arguments namespace
	:rtype: argparse.ArgumentParser.Namespace
	"""
	parser = ArgumentParser(description=BANNER, formatter_class=RawTextHelpFormatter, epilog='Psst, hey buddy... Wanna do some organized p0r7 5c4nn1n6?')
	parser.add_argument('-db', action='store', type=str, default='main', help='DB name to work with')

	subparser = parser.add_subparsers(dest='subparser')

	db_epilog = """
	examples:
	  das -db testdb db scan.txt [-d domains.txt] [--create]
	""".replace('\t', '')
	db_parser = subparser.add_parser('db', formatter_class=RawDescriptionHelpFormatter, epilog=db_epilog, help='utilities for manual DB manipulations')
	db_parser.add_argument('scan_output', action='store', type=str, help='path to a newline-separated text file with scan output to fill the DB with')
	db_parser.add_argument('-d', '--domains', action='store', type=str, help='path to a newline-separated text file with with domain names to fill the DB with')
	group_action = db_parser.add_mutually_exclusive_group(required=True)
	group_action.add_argument('--create', action='store_true', default=False, help='create TinyDB from a generic scan output and (optionally) a list of domain names')

	add_epilog = """
	examples:
	  das add nmap '-v -n -Pn -e eth0 --min-rate 1000 -T4 -iL hosts.txt -p1-49151 --open'
	  das -db testdb add masscan '-e eth0 --rate 1000 -iL hosts.txt -p1-65535 --open'
	  das add rustscan '-b 1000 -t 2000 -u 5000 -a hosts.txt -r 1-65535 -g --no-config --scan-order "Random"'
	  das -db testdb add naabu '-interface eth0 -rate 1000 -iL hosts.txt -p - -silent -s s'
	  das add -rm nimscan '192.168.1.0/24 -vi -p:1-65535 -f:500'
	  das -db testdb add sx 'tcp syn -a arp.cache -i eth0 --rate 1000/s 192.168.1.0/24 -p 445,3389'
	  das add nmap nmap-20221025T004453.out  # import from ~/.das/db/raw
	""".replace('\t', '')
	add_parser = subparser.add_parser('add', formatter_class=RawDescriptionHelpFormatter, epilog=add_epilog, help='run a full port scan and add the output to DB')
	add_parser.add_argument('scanner_name', action='store', type=str, help='port scanner name or path')
	add_parser.add_argument('scanner_args', action='store', type=str, help='port scanner switches and options or text file with scan results to import')
	add_parser.add_argument('-rm', action='store_true', default=False, help='drop the DB before updating its values')

	scan_epilog = """
	examples:
	  das scan -hosts all -show
	  das scan -ports 22 -show -raw
	  das scan -hosts 192.168.1.0/24,10.10.13.37 -oA report1 -nmap '-Pn -sVC -O'
	  das -db testdb scan -ports 22,80,443,445 -oA report2 -parallel
	  das -db testdb scan -ports ports.txt -oA report2 -parallel -proc 4
	""".replace('\t', '')
	scan_parser = subparser.add_parser('scan', formatter_class=RawDescriptionHelpFormatter, epilog=scan_epilog, help='run targeted Nmap scans against hosts and ports from DB')
	scan_parser.add_argument('-nmap', action='store', type=str, default=None, help='custom Nmap options, so the final command will be "sudo nmap <OPTIONS> -oA scan/$output $ip -p$ports" (default is "sudo nmap -Pn -sV --version-intensity 6 -O -oA scan/$output $ip -p$ports")')
	scan_parser.add_argument('-limit', action='store', type=int, default=None, help='do NOT include hosts whose port list length is less than <LIMIT>')
	scan_parser.add_argument('-raw', action='store_true', default=False, help='when -show is used, print the results in a raw list (no decorations or colors)')
	scan_parser.add_argument('-dns', action='store_true', default=False, help='when -hosts and -show are used, include domain names associated with corresponding IP addresses')
	group_parallel = scan_parser.add_argument_group('parallelism')
	group_parallel.add_argument('-parallel', action='store_true', default=False, help='run Nmap in multiple processes, number of processes is set with -p (-processes) argument')
	group_parallel.add_argument('-proc', action='store', type=int, default=None, help='number of parallel Nmap processes (if no value is provided, it will default to the number of processors on the machine)')
	group_action = scan_parser.add_mutually_exclusive_group(required=True)
	group_action.add_argument('-show', action='store_true', default=False, help='only show DB data, do not launch Nmap')
	group_action.add_argument('-oA', action='store', type=str, default=None, help='final report filename without extension (all formats: HTML, XML, simple text, grepable)')
	group_action.add_argument('-oX', action='store', type=str, default=None, help='final report filename without extension (XML+HTML formats)')
	group_action.add_argument('-oN', action='store', type=str, default=None, help='final report filename without extension (simple text format)')
	group_action.add_argument('-oG', action='store', type=str, default=None, help='final report filename without extension (grepable format)')
	group_criteria = scan_parser.add_mutually_exclusive_group(required=True)
	group_criteria.add_argument('-hosts', action='store', type=str, default=None, help='hosts to scan all their ports which were considered as open (a comma-separated string of IPs and/or CIDRs or a filename; "all" for all hosts in DB)')
	group_criteria.add_argument('-ports', action='store', type=str, default=None, help='ports to scan on every host where it was considered as open (a comma-separated string of ports or a filename; "all" for all ports in DB)')

	dns_epilog = """
	examples:
	  das dns domains.txt [--resolve|--update]
	""".replace('\t', '')
	dns_parser = subparser.add_parser('dns', formatter_class=RawDescriptionHelpFormatter, epilog=dns_epilog, help='map domain names from an input file to corresponding IP addresses from the DB')
	dns_parser.add_argument('domains', action='store', type=str, help='path to a newline-separated text file with domain names to resolve')
	group_action = dns_parser.add_mutually_exclusive_group(required=True)
	group_action.add_argument('--resolve', action='store_true', default=False, help='resolve "A" domain names into IP addresses and update DB items with them')
	group_action.add_argument('--update', action='store_true', default=False, help='update existing DB with new domains names from an input file')

	report_epilog = """
	examples:
	  das report -hosts all -show
	  das report -hosts 192.168.1.0/24,10.10.13.37 -oA report1
	  das report -ports 22,80,443,445 -oA report2
	  das report -ports ports.txt -oA report2
	""".replace('\t', '')
	report_parser = subparser.add_parser('report', formatter_class=RawDescriptionHelpFormatter, epilog=report_epilog, help='merge separate Nmap outputs into a single report (https://github.com/CBHue/nMap_Merger)')
	group_action = report_parser.add_mutually_exclusive_group(required=True)
	group_action.add_argument('-show', action='store_true', default=False, help='only show Nmap raw reports, do not merge into a file')
	group_action.add_argument('-oA', action='store', type=str, default=None, help='final report filename without extension (all formats: HTML, XML, simple text, grepable)')
	group_action.add_argument('-oX', action='store', type=str, default=None, help='final report filename without extension (XML+HTML formats)')
	group_action.add_argument('-oN', action='store', type=str, default=None, help='final report filename without extension (simple text format)')
	group_action.add_argument('-oG', action='store', type=str, default=None, help='final report filename without extension (grepable format)')
	group_criteria = report_parser.add_mutually_exclusive_group(required=True)
	group_criteria.add_argument('-hosts', action='store', type=str, help='hosts to add to report by IP (a comma-separated string of IPs and/or CIDRs or a filename; "all" for all host reports in Nmap directory)')
	group_criteria.add_argument('-ports', action='store', type=str, help='hosts to add to report by port (a comma-separated string of ports or a filename; "all" for all port reports in Nmap directory)')

	parse_parser_epilog = """
	examples:
	  das parse http
	  das -db testdb parse http,https -dns -raw
	""".replace('\t', '')
	parse_parser = subparser.add_parser('parse', formatter_class=RawDescriptionHelpFormatter, epilog=parse_parser_epilog, help='parse raw Nmap XML reports by service names and print entries in format {service}://{host}:{port}}')
	parse_parser.add_argument('services', action='store', type=str, default=None, help='service names to search for (a comma-separated string of services)')
	parse_parser.add_argument('-dns', action='store_true', default=False, help='if a domain name is present in the DB for a specific host, then use it instead of an IP address when printing the output')
	parse_parser.add_argument('-raw', action='store_true', default=False, help='print the results in a raw list (no decorations or colors)')

	draw_epilog = """
	examples:
	  das draw report1.xml
	  das draw *.xml -listen 0.0.0.0
	""".replace('\t', '')
	draw_parser = subparser.add_parser('draw', formatter_class=RawDescriptionHelpFormatter, epilog=draw_epilog, help='visualize Nmap XML reports (https://github.com/jor6PS/DrawNmap)')
	draw_parser.add_argument('xml_reports', action='store', type=str, nargs='+', default=[], help='Nmap XML reports to visualize')
	draw_parser.add_argument('-l', '--listen', action='store', type=str, default='localhost', help='IP address to listen on for the visualization app (use "0.0.0.0" if ran in Docker)')

	tree_parser = subparser.add_parser('tree', help='show contents of the ~/.das/ directory using tree')

	helper_parser = subparser.add_parser('help', help='show builtin --help dialog of a selected port scanner')
	helper_parser.add_argument('scanner_name', action='store', type=str, help='port scanner name')

	return parser.parse_args()


def main():
	"""
	Main function.
	"""
	args = parse_args()

	if len(sys.argv) == 1:
		print('usage: __main__.py [-h] {db,add,scan,dns,report,parse,draw,tree,help} ...\n')
		print(BANNER)
		sys.exit(0)

	logger = Logger()

	if (args.subparser == 'add' and not Path(args.scanner_args).is_file) or args.subparser == 'scan' and not args.show:
		logger.start_timer()

	if args.subparser == 'db':
		(Path.home() / '.das' / 'db' / 'raw').mkdir(parents=True, exist_ok=True)
		P = Path.home() / '.das' / 'db' / f'{args.db}.json'

		db = DB(str(P))
		if args.create:
			logger.print_info(f'Creating DB -> {P.resolve()}')
			num_created = db.create_generic(Path(args.scan_output), Path(args.domains))
			logger.print_success(f'Successfully created DB with {num_created} hosts')

	elif args.subparser == 'add':
		(Path.home() / '.das' / 'db' / 'raw').mkdir(parents=True, exist_ok=True)

		module_name = Path(args.scanner_name).name
		try:
			AddPortscanOutput = import_module(f'das.parsers.{module_name}', 'AddPortscanOutput').AddPortscanOutput
		except ModuleNotFoundError:
			logger.print_error(f"Unsupported port scanner '{module_name}'")
			sys.exit(1)
		except Exception as e:
			logger.print_error(f"Unknown error while loading '{module_name}' parser: {str(e)}")
			sys.exit(1)

		P = Path.home() / '.das' / 'db' / f'{args.db}.json'

		apo = AddPortscanOutput(str(P), args.rm, args.scanner_name, args.scanner_args)
		portscan_out, num_hosts = apo.parse()

		if P.exists():
			logger.print_info(f'Using DB -> {P.resolve()}')

		P = Path.home() / '.das' / portscan_out
		if P.exists():
			logger.print_info(f'Raw port scanner output -> {P.resolve()}')

		logger.print_success(f'Successfully updated DB with {num_hosts} hosts')

	elif args.subparser == 'scan':
		if not args.show:
			(Path.home() / '.das' / f'nmap_{args.db}').mkdir(parents=True, exist_ok=True)

		output = {'oA': args.oA, 'oX': args.oX, 'oN': args.oN, 'oG': args.oG}

		P = Path.home() / '.das' / 'db' / f'{args.db}.json'
		if P.exists() and not args.raw:
			logger.print_info(f'Using DB -> {P.resolve()}')

		if args.show:
			ss = ScanShow(str(P), args.hosts, args.ports, args.limit, args.raw)
			if args.hosts:
				ss.nmap_by_hosts(args.dns)
			elif args.ports:
				ss.nmap_by_ports()

		elif any(o for o in output.values()):
			Parallelism = namedtuple('Parallelism', 'enabled processes')
			parallel = Parallelism(args.parallel, args.proc)

			sr = ScanRun(str(P), args.hosts, args.ports, args.limit)
			if args.hosts:
				sr.nmap_by_hosts(args.nmap, parallel)
			elif args.ports:
				sr.nmap_by_ports(args.nmap, parallel)

			nm = NmapMerger(str(P), args.hosts, args.ports, output)
			nm.generate()

	elif args.subparser == 'dns':
		P = Path.home() / '.das' / 'db' / f'{args.db}.json'
		if P.exists():
			logger.print_info(f'Using DB -> {P.resolve()}')

		dns = DNS(str(P), Path(args.domains))
		if args.resolve:
			dns.resolve()
		elif args.update:
			num_updated = dns.update()
			logger.print_success(f'Successfully updated {num_updated} hosts from DB with domain names')

	elif args.subparser == 'report':
		output = {'oA': args.oA, 'oX': args.oX, 'oN': args.oN, 'oG': args.oG}

		if args.show:
			nm = NmapMerger(args.db, args.hosts, args.ports)
			nm.show()

		elif any(o for o in output.values()):
			P = Path.home() / '.das' / 'db' / f'{args.db}.json'
			if P.exists():
				logger.print_info(f'Using DB -> {P.resolve()}')

			nm = NmapMerger(str(P), args.hosts, args.ports, output)
			nm.generate()

	elif args.subparser == 'parse':
		P = Path.home() / '.das' / 'db' / f'{args.db}.json'
		if args.dns and P.exists() and not args.raw:
			logger.print_info(f'Using DB -> {P.resolve()}')

		np = NmapParser(str(P), args.services, args.dns, args.raw)
		np.parse()

	elif args.subparser == 'draw':
		das.common.XML_REPORTS = args.xml_reports
		from das.drawnmap import run_server
		run_server(host=args.listen)

	elif args.subparser == 'tree':
		os.system(f'tree {Path.home() / ".das"}')

	elif args.subparser == 'help':
		os.system(f'{args.scanner_name} --help')

	if (args.subparser == 'add' and not Path(args.scanner_args).is_file) or args.subparser == 'scan' and not args.show:
		logger.stop_timer()


if __name__ == '__main__':
	main()
