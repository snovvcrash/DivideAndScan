from das.parsers import IAddPortscanOutput


class AddPortscanOutput(IAddPortscanOutput):
	"""Child class for processing Masscan output (import)."""

	def parse(self):
		"""
		Masscan (import) raw output parser.

		:return: a pair of values (portscan raw output filename, number of hosts added to DB)
		:rtype: tuple
		"""
		items, hosts = [], set()
		for line in self.portscan_raw:
			try:
				ip = line.split()[3]
				port, _, proto = line.split()[-1].split('/')[0:3]
			except Exception:
				pass
			else:
				if proto == 'tcp':
					items.append({'ip': ip, 'port': int(port), 'domains': []})
					hosts.add(ip)

		self.db.insert_multiple(items)

		return (self.portscan_out, len(hosts))
