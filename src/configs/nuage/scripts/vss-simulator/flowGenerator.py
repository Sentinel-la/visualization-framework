#!/usr/bin/env python

import copy
from elasticsearch import Elasticsearch, helpers
import random
import time
import uuid
import yaml

CONFIG_DICT = {}
PGS = []
VPORTS = []
ACL_ACTION = ["ALLOW", "DENY", "OTHER"]
PROTOCOL = ["TCP", "UDP", "ICMP"]

def populatePGs():
	global PGS
	for i in range(CONFIG_DICT["no_of_pgs"]):
		PGS.append("PG" + str(i+1))

def populateVPorts():
	global PGS, VPORTS
	vport_prop = {}
	for PG in PGS:
		for i in range(CONFIG_DICT["no_of_vports_per_pgs"]):
			vport_prop['name'] = PG + "-VPort" + str(i+1)
			vport_prop['ip'] = "10.10.0." + str(i+1)
			vport_prop['mac'] = "DE:AD:BE:EF:00:" + (("0" + str(i+1)) if i<10 else str(i+1))
			vport_prop['uuid'] = str(uuid.uuid4())
			vport_prop['port'] = i+1
			vport_prop['pg'] = PG
			VPORTS.append(vport_prop)
			vport_prop = {}

def generateFlowStats(domain_id):
	for i in range(len(VPORTS)):
		es_data = {}
		flow_data = random.sample(VPORTS, 2)
		# Always write it in specific index in specific doc_type
		es_data['_index'] = "nuage_flow"
		es_data['_type'] = "nuage_doc_type"

		# Filling in packet-level data
		es_data['sourceip'] = flow_data[0]['ip']
		es_data['destinationip'] = flow_data[1]['ip']
		es_data['sourcemac'] = flow_data[0]['mac']
		es_data['destinationmac'] = flow_data[1]['mac']
		es_data['sourceport'] = flow_data[0]['port']
		es_data['destinationport'] = flow_data[1]['port']

		# may change later
		es_data['protocol'] = random.sample(PROTOCOL, 1)[0]
		es_data['tcpflag'] = 0
		es_data['messageType'] = 2
		es_data['type'] =  random.sample(ACL_ACTION, 1)[0]

		es_data['nuage_metadata'] ={
			'inport': random.randint(1,5), 
			'flowid': random.randint(10000,15000),
			'outport': random.randint(1,5),
			'domainName': CONFIG_DICT['domain.name'] + "-" + str(domain_id),
			'dpgName': flow_data[1]['pg'],
			'enterpriseName': CONFIG_DICT['enterprise.name'], 
			'sourcevport': flow_data[0]['uuid'],
			'destinationvport': flow_data[1]['uuid'],
			'spgName': flow_data[0]['pg'],
                        'subnetName': CONFIG_DICT['domain.name'] + "-" + str(domain_id) + "-sub",
                        'zoneName': CONFIG_DICT['domain.name'] + "-" + str(domain_id) + "-zone",
                        'aclId': flow_data[0]['uuid']
		}
		print ("Writing flow information between " + flow_data[0]['name'] + " and " + flow_data[1]['name'])
		writeToES(es_data)

def writeToES(es_data):
	es = Elasticsearch("192.168.100.200")
	write_data = []
	# Create counters on the fly everytime
	# Write data for a day every minute
	# Start with 24 hours a go
	startTime = int(time.time()) * 1000 - (24 * 60 * 60 * 1000)
	for i in range(1440):
		es_data['bytes'] = random.randint(10000, 20000)
		es_data['packets'] = random.randint(500, 1000)
		es_data['timestamp'] = startTime + (i * 60000)
		write_data.append(copy.deepcopy(es_data))
		#es1.index(index="flowindex", doc_type="flow", body=es_data)
	helpers.bulk(es, iter(write_data), request_timeout=50)

def populateData():
	populatePGs()	
	populateVPorts()

def configRead():
	global CONFIG_DICT
	with open("insight.yml", "r") as fileread:
		try:
			CONFIG_DICT = yaml.load(fileread)
		except yaml.YAMLError as exc:
			print(exc)

if __name__ == "__main__":
	configRead()
        for i in range(1, CONFIG_DICT['no_of_domains']+1):
            populateData()
	    #print PGS
	    #print VPORTS
	    generateFlowStats(i)