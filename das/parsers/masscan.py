from das.parsers import IAddPortscanOutput


class AddPortscanOutput(IAddPortscanOutput):
	"""Child class for processing Masscan output."""

	def parse(self):
		"""
		Masscan raw output parser.

		:return: a pair of values (portscan raw output filename, number of hosts added to DB)
		:rtype: tuple
		"""
		items, hosts = [], set()
		for line in self.portscan_raw:
			try:
				ip = line.split()[-1]
				port, proto = line.split()[3].split('/')
			except Exception:
				pass
			else:
				if proto == 'tcp':
					items.append({'ip': ip, 'port': int(port), 'domains': []})
					hosts.add(ip)

		self.db.insert_multiple(items)

		return (self.portscan_out, len(hosts))
