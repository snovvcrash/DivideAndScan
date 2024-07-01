#!/usr/bin/env python3

# Fix wrongly merged XMLs into separate files from `cat *.xml > wrongly_merged_xmls.xml`

import re
from pathlib import Path

with open('wrongly_merged_xmls.xml') as f:
    text = f.read()

xml_regex = r'(?<=<\?xml version="1.0" encoding="UTF-8"\?>)(.*?)(?=<\?xml version="1.0" encoding="UTF-8"\?>)'
matches = re.findall(xml_regex, text, re.DOTALL)

ip_regex = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')

for match in matches:
    xml_contents = match.strip()
    ip = ip_regex.search(xml_contents).group()

    xml_path = Path.home() / '.das' / 'nmap_default' / f'{ip}.xml'
    with open(xml_path, 'w') as f:
        f.write(xml_contents)

    print(f'{ip} -> {xml_path}')
