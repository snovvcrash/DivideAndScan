from das.parsers import IAddPortscanOutput


class AddPortscanOutput(IAddPortscanOutput):
	"""Child class for processing NimScan output."""

	def parse(self):
		"""
		NimScan raw output parser.

		:return: a pair of values (portscan raw output filename, number of hosts added to DB)
		:rtype: tuple
		"""
		items, hosts = [], set()
		for line in self.portscan_raw:
			try:
				ip, port = line.split('==>')[1].split()[0].split(':')
				# Get rid of ANSII color symbols
				ip = ''.join([i if 48 <= ord(i) <= 57 or ord(i) == 46 else '' for i in ip])
				ip = ip.strip('0')
				port = port.split('[')[0]
				port = ''.join([i if 48 <= ord(i) <= 57 else '' for i in port])
			except Exception:
				pass
			else:
				items.append({'ip': ip, 'port': int(port), 'domains': []})
				hosts.add(ip)

		self.db.insert_multiple(items)

		return (self.portscan_out, len(hosts))
