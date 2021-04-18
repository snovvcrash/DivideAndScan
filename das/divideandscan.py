#!/usr/bin/env python3

import sys
from pathlib import Path
from collections import namedtuple
from argparse import ArgumentParser, RawTextHelpFormatter, RawDescriptionHelpFormatter

from das.modules.add import AddMasscanOutput, AddRustscanOutput, AddNaabuOutput
from das.modules.scan import ScanShow, ScanRun
from das.modules.report import NmapMerger
from das.modules.common import BANNER, Logger


def parse_args():
	"""
	Process arguments.

	:return: arguments namespace
	:rtype: argparse.ArgumentParser.Namespace
	"""
	parser = ArgumentParser(description=BANNER, formatter_class=RawTextHelpFormatter, epilog='Psst, hey buddy... Wanna do some organized p0r7 5c4nn1n6?')

	subparser = parser.add_subparsers(dest='subparser')

	add_epilog = """
	examples:

	  das add masscan '-e eth0 --rate 1000 -iL hosts.txt --open -p1-65535'
	  das add rustscan '-b 1000 -t 2000 -u 5000 -a hosts.txt -r 1-65535 -g --no-config --scan-order "Random"'
	  das add -db testdb -rm naabu '-interface eth0 -rate 1000 -iL hosts.txt -p - -silent -s s'
	""".replace('\t', '')
	add_parser = subparser.add_parser('add', formatter_class=RawDescriptionHelpFormatter, epilog=add_epilog, help='run a full port scan {masscan,rustscan,naabu} and add the output to DB')
	add_parser.add_argument('scanner_name', action='store', type=str, help='port scanner name')
	add_parser.add_argument('scanner_args', action='store', type=str, help='port scanner switches and options')
	add_parser.add_argument('-db', action='store', type=str, default='das', help='DB name to save the output into')
	add_parser.add_argument('-rm', action='store_true', default=False, help='drop the DB before updating its values')

	scan_epilog = """
	examples:

	  das scan -hosts all -show
	  das scan -hosts 192.168.1.0/24,10.10.13.37 -oA report1 -nmap '-Pn -sVC -O'
	  das scan -db testdb -ports 22,80,443,445 -oA report2 -parallel
	  das scan -db testdb -ports ports.txt -oA report2 -parallel -proc 4
	""".replace('\t', '')
	scan_parser = subparser.add_parser('scan', formatter_class=RawDescriptionHelpFormatter, epilog=scan_epilog, help='run targeted Nmap scans against hosts and ports from DB')
	scan_parser.add_argument('-db', action='store', type=str, default='das', help='DB name to retrieve the input from')
	scan_parser.add_argument('-nmap', action='store', type=str, default=None, help='custom Nmap options, so the final command will be "sudo nmap <OPTIONS> -oA scan/$output $ip -p$ports" (default is "sudo nmap -Pn -sV --version-intensity 6 -O -oA scan/$output $ip -p$ports")')
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

	report_epilog = """
	examples:

	  das report -hosts all -show
	  das report -hosts 192.168.1.0/24,10.10.13.37 -oA report1
	  das report -ports 22,80,443,445 -oA report2
	  das report -ports ports.txt -oA report2
	""".replace('\t', '')
	report_parser = subparser.add_parser('report', formatter_class=RawDescriptionHelpFormatter, epilog=report_epilog, help='merge separate Nmap outputs into a single report in different formats')
	group_action = report_parser.add_mutually_exclusive_group(required=True)
	group_action.add_argument('-show', action='store_true', default=False, help='only show Nmap raw reports, do not merge into a file')
	group_action.add_argument('-oA', action='store', type=str, default=None, help='final report filename without extension (all formats: HTML, XML, simple text, grepable)')
	group_action.add_argument('-oX', action='store', type=str, default=None, help='final report filename without extension (XML+HTML formats)')
	group_action.add_argument('-oN', action='store', type=str, default=None, help='final report filename without extension (simple text format)')
	group_action.add_argument('-oG', action='store', type=str, default=None, help='final report filename without extension (grepable format)')
	group_criteria = report_parser.add_mutually_exclusive_group(required=True)
	group_criteria.add_argument('-hosts', action='store', type=str, help='hosts to add to report by IP (a comma-separated string of IPs and/or CIDRs or a filename; "all" for all host reports in Nmap directory)')
	group_criteria.add_argument('-ports', action='store', type=str, help='hosts to add to report by port (a comma-separated string of ports or a filename; "all" for all port reports in Nmap directory)')

	return parser.parse_args()


def main():
	"""
	Main function.
	"""
	args = parse_args()

	if len(sys.argv) == 1:
		print('usage: __main__.py [-h] {add,scan,report} ...\n')
		print(BANNER)
		sys.exit(0)

	logger = Logger()

	if args.subparser == 'add' or args.subparser == 'scan' and not args.show:
		logger.start_timer()

	if args.subparser == 'add':
		(Path.cwd() / '.db' / 'raw').mkdir(parents=True, exist_ok=True)

		if args.scanner_name == 'masscan':
			AddPortscanOutput = AddMasscanOutput
		elif args.scanner_name == 'rustscan':
			AddPortscanOutput = AddRustscanOutput
		elif args.scanner_name == 'naabu':
			AddPortscanOutput = AddNaabuOutput
		else:
			logger.print_error(f'{args.scanner_name}: Unsupported port scanner')
			sys.exit(1)

		P = Path.cwd() / '.db' / f'{args.db}.json'

		apo = AddPortscanOutput(str(P), args.rm, args.scanner_name, args.scanner_args)
		portscan_out, num_of_hosts = apo.parse()

		if P.exists():
			logger.print_info(f'Using DB -> {P.resolve()}')

		P = Path.cwd() / portscan_out
		if P.exists():
			logger.print_info(f'Raw port scanner output -> {P.resolve()}')

		logger.print_success(f'Successfully updated DB with {num_of_hosts} hosts')

	elif args.subparser == 'scan':
		(Path.cwd() / '.nmap').mkdir(exist_ok=True)

		output = {'oA': args.oA, 'oX': args.oX, 'oN': args.oN, 'oG': args.oG}

		P = Path.cwd() / '.db' / f'{args.db}.json'
		if P.exists():
			logger.print_info(f'Using DB -> {P.resolve()}')

		if args.show:
			ss = ScanShow(str(P), args.hosts, args.ports)
			if args.hosts:
				ss.nmap_by_hosts()
			elif args.ports:
				ss.nmap_by_ports()

		elif any(o for o in output.values()):
			Parallelism = namedtuple('Parallelism', 'enabled processes')
			parallel = Parallelism(args.parallel, args.proc)

			sr = ScanRun(str(P), args.hosts, args.ports)
			if args.hosts:
				sr.nmap_by_hosts(args.nmap, parallel)
			elif args.ports:
				sr.nmap_by_ports(args.nmap, parallel)

			nm = NmapMerger(args.hosts, args.ports, output)
			nm.generate()

	elif args.subparser == 'report':
		output = {'oA': args.oA, 'oX': args.oX, 'oN': args.oN, 'oG': args.oG}

		if args.show:
			nm = NmapMerger(args.hosts, args.ports)
			nm.show()

		elif any(o for o in output.values()):
			nm = NmapMerger(args.hosts, args.ports, output)
			nm.generate()

	if args.subparser == 'add' or args.subparser == 'scan' and not args.show:
		logger.stop_timer()


if __name__ == '__main__':
	main()
