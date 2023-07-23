from das.parsers import IAddPortscanOutput


class AddPortscanOutput(IAddPortscanOutput):
	"""Child class for processing Naabu output."""

	def parse(self):
		"""
		Naabu raw output parser.

		:return: a pair of values (portscan raw output filename, number of hosts added to DB)
		:rtype: tuple
		"""
		items, hosts = [], set()
		for line in self.portscan_raw:
			try:
				ip, port = line.split(':')
			except Exception:
				pass
			else:
				items.append({'ip': ip, 'port': int(port), 'domains': []})
				hosts.add(ip)

		self.db.insert_multiple(items)

		return (self.portscan_out, len(hosts))
