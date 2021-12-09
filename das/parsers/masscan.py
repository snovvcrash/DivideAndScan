from das.parsers import IAddPortscanOutput


class AddPortscanOutput(IAddPortscanOutput):
	"""Child class for processing Masscan output."""

	def parse(self):
		"""
		Masscan raw output parser.

		:return: a pair of values (portscan raw output filename, number of hosts added to DB)
		:rtype: tuple
		"""
		hosts = set()
		for line in self.portscan_raw:
			try:
				ip = line.split()[-1]
				port, proto = line.split()[3].split('/')
			except:
				pass
			else:
				if proto == 'tcp':
					item = {'ip': ip, 'port': int(port)}
					if item not in self.db:
						self.db.insert(item)

				hosts.add(ip)

		return (self.portscan_out, len(hosts))
