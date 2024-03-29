from das.parsers import IAddPortscanOutput


class AddPortscanOutput(IAddPortscanOutput):
	"""Child class for processing generic scan output."""

	def parse(self):
		"""
		Generic scan raw output parser.

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
