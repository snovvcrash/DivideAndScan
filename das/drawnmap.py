#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Shamelessly copy-pasted from: https://github.com/jor6PS/DrawNmap/blob/main/DrawNmap.py
# All credits to: https://github.com/jor6PS

import os
import sys
import subprocess
from uuid import uuid4
from pathlib import Path

import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from dash import dash, html, dcc, Input, Output, callback_context

from das.common import XML_REPORTS, Logger

logger = Logger()

######################### PASS THE CSS INTO DASH ########################
app = dash.Dash(
	__name__,
	external_stylesheets=[
		'https://codepen.io/chriddyp/pen/bWLwgP.css'
	]
)

################### CONVERT XML TO CSV ###################
filename = f'/tmp/{uuid4()}.csv'
for xml in XML_REPORTS:
	if subprocess.call([sys.executable, (Path(__file__) / '../Nmap-XML-to-CSV/nmap_xml_parser.py').resolve(), '-f', xml, '-csv', filename], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0:
		logger.print_success(f'Updated {filename} with {xml} data')
	else:
		logger.print_error(f'Failed processing {xml}')

with open(filename, 'r') as f:
	data = f.read().splitlines()

header = data[0]
data = data[1:]
commas_count = header.count(',')

valid = []
for line in data:
	if line.count(',') == commas_count-1 and any(pat in line for pat in ('tcp,', 'udp,')):
		line = line.replace('"', '')
		valid.append(line)
	else:
		#logger.print_warning(f'Removed broken line from CSV: "{line}"')
		continue

with open(filename, 'w') as f:
	f.write(header + '\n')
	for line in valid:
		f.write(line + '\n')

################### CREATE DATAFRAME FROM CSV ###################

df = pd.read_csv(filename, delimiter=',')
df['Port'] = df['Port'].astype(int)

# Remove duplicated in second loop
df = df.drop_duplicates(subset=['IP', 'Port'])

# Extract all ports in a list
all_ports =  df['Port'].tolist()
all_ports = sorted(set(all_ports))


################### PREPARE GRAPH ###################
def network_graph(dataframe):
	# Group repeated IPs and common elements as ports, services....
	groupby_column = 'IP'
	aggregate_port = 'Port'
	aggregate_service = 'Service'
	aggregate_host = 'Host'
	aggregate_os = 'OS'
	aggregate_product = 'Product'

	agg_df = dataframe.groupby('IP').aggregate({aggregate_port: list, aggregate_service: list,aggregate_host: list, aggregate_os: list, aggregate_product: list})
	df_alias = dataframe.drop(columns=[aggregate_port,aggregate_service,aggregate_host,aggregate_os,aggregate_product]).set_index(groupby_column)

	df = agg_df.join(df_alias).reset_index(groupby_column).drop_duplicates(groupby_column).reset_index(drop=True)

	# Create a column with the subnet, structure 192.168.1.X 
	subnet_ips = []
	for ip in df['IP']:
		subnet_ips.append(ip[:ip.rfind('.')])
	df['Subnet'] = subnet_ips

	# EXTRACT NODES AND EDGES FROM DATAFRAME
	G = nx.from_pandas_edgelist(df, 'Subnet', 'IP', ['Host','OS','Proto','Port','Service','Product','Service FP','NSE Script ID','NSE Script Output','Notes'])
	nx.set_node_attributes(G, df.set_index('IP')['Port'].to_dict(), 'Port')
	nx.set_node_attributes(G, df.set_index('IP')['Service'].to_dict(), 'Service')

	# get a x,y position for each node
	pos = nx.layout.spring_layout(G)

	for node in G.nodes:
		G.nodes[node]['pos'] = list(pos[node])

	pos=nx.get_node_attributes(G,'pos')

	dmin=1
	ncenter=0
	for n in pos:
		x,y=pos[n]
		d=(x-0.5)**2+(y-0.5)**2
		if d<dmin:
			ncenter=n
			dmin=d

	# Create Edges
	edge_trace = go.Scatter(
		x=[],
		y=[],
		line=dict(width=0.5,color='#888'),
		hoverinfo='none',
		mode='lines')

	for edge in G.edges():
		x0, y0 = G.nodes[edge[0]]['pos']
		x1, y1 = G.nodes[edge[1]]['pos']
		edge_trace['x'] += tuple([x0, x1, None])
		edge_trace['y'] += tuple([y0, y1, None])

	# Create nodes with info (IP, Ports, Color, Size...)
	node_trace = go.Scatter(
		x=[],
		y=[],
		text=[],
		mode='markers+text',
		textposition='bottom center',
		hoverinfo='text',
		hovertext=[],
		marker=dict(
			showscale=True,
			# 'aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance',
			# 'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
			# 'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl',
			# 'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
			# 'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys',
			# 'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
			# 'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
			# 'orrd', 'oryel', 'oxy', 'peach', 'phase', 'picnic', 'pinkyl',
			# 'piyg', 'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn',
			# 'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu',
			# 'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar',
			# 'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn',
			# 'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid',
			# 'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr',
			# 'yylorrd'
			colorscale='redor',
			color=[],
			size=13,
			colorbar=dict(
				thickness=10,
				title='Port Number',
				xanchor='left',
				titleside='right'
			),
			line_width=2)
		)

	index = 0
	len_nports = []
	len_nports_excp = []
	for node in G.nodes():
		x, y = G.nodes[node]['pos']
		node_trace['x'] += tuple([x])
		node_trace['y'] += tuple([y])
		if G.nodes[node].get('Port') != None:
			hovertext = str(G.nodes[node]['Port']) + '<br>' + str(G.nodes[node]['Service'])
			node_trace['hovertext'] += tuple([hovertext])
			len_nports.append(len(G.nodes[node]['Port']))
			len_nports_excp.append(len(G.nodes[node]['Port']))
		else:
			hovertext = ''
			node_trace['hovertext'] += tuple([hovertext])
			len_nports.append(0)
			len_nports_excp.append(3)
		text = node
		node_trace['text'] += tuple([text])
		index = index + 1

	node_trace.marker.color = len_nports
	# node_trace.marker.size = [i * 10 for i in len_nports_excp]

	# Create the figure values
	fig = go.Figure(data=[edge_trace, node_trace],
				 layout=go.Layout(
					title='<br>Network Graph',
					titlefont=dict(size=16),
					showlegend=False,
					hovermode='closest',
					margin=dict(b=20,l=5,r=5,t=40),
					annotations=[ dict(
						showarrow=False,
						xref='paper', yref='paper',
						x=0.005, y=-0.002 ) ],
					xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
					yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

	return(fig)


app.layout = html.Div(children=[
	html.Div(children=[
		html.H3('OPEN PORTS'),
		dcc.Checklist(['All'], [], id='all-checklist'),
		dcc.Checklist(all_ports, value=[],id='port-checklist'),
		html.Br(),
	], className='one columns'),
	html.Div(children=[
		html.H3('NETWORK DIAGRAM'),
		dcc.Graph(id='Graph',figure=network_graph(df)),
		html.Br(),
	], className='ten columns'),
], className='row')


# Callback for adding the all check
@app.callback(
	Output('port-checklist', 'value'),
	Output('all-checklist', 'value'),
	Input('port-checklist', 'value'),
	Input('all-checklist', 'value'),
)
def sync_checklists(ports_selected, all_selected):
	ctx = callback_context
	input_id = ctx.triggered[0]['prop_id'].split('.')[0]
	if input_id == 'port-checklist':
		all_selected = ['All'] if set(ports_selected) == set(all_ports) else []    
	else:
		ports_selected = all_ports if all_selected else []
	return ports_selected, all_selected


# Callback to update the graph according to the checklist
@app.callback(
	Output('Graph', 'figure'),
	Input('port-checklist', 'value')
)
def update_figure(value):
	ctx = callback_context
	filter_df = pd.DataFrame()
	if not value:
		return network_graph(df)
	else:
		for port in ctx.triggered[0]['value']:
				filter_df = pd.concat([filter_df, pd.DataFrame.from_records(df[df['Port'] == port])])
		return network_graph(filter_df)


def run_server(host):
	app.run_server(host=host, debug=False)
	logger.print_info(f'Deleting {filename}')
	os.remove(filename)
