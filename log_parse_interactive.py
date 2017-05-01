#!/usr/bin/python

import optparse
import re
from dateutil.parser import parse as parse_date
from datetime import datetime,timedelta
from math import floor


def get_content(line, delimiter):
	content = {}
	content["date"] = parse_date(line.split(delimiter)[1])
	content.update(field.split("=", 1) for field in line.split(delimiter)[3].split(','))
	return content

def get_events(log_files, start_event, end_event, delimiter):
	for file_name in log_files.split(','):
		log = open(file_name, 'r').readlines()
		for line in log:
			try:
				yield get_content(line, delimiter)
			except:
				continue

def print_stats(stats):
	print("   total requests    :   {}".format(stats["total_requests"]))
	print("   unique requests   :   {}".format(stats["unique_requests"]))
	print("   total successess  :   {}".format(stats["successes"]))
	print("   total failures    :   {}".format(stats["failures"]))
	print("   repeated requests :   {}".format(stats["duplicate_requests"]))
	if stats["successes"] > 1:
		print("   success rate      :   {}%".format(int(((stats["successes"]*100.0)/(stats["unique_requests"])))))
	else:
				print("   success rate      :   0%")

def main():
	parser = optparse.OptionParser(usage = "%prog log_file start_event end_event identifier [options]")
	parser.add_option("--delimiter", default = ' | ', dest = "delimiter")

	(options, args) = parser.parse_args()
	if len(args) != 4:
		parser.print_help()
		return -1

	log_files = args[0]
	start_event = args[1]
	end_event = args[2]
	identifier = args[3]

	print args

	stats = {"total_requests":0, "unique_requests":0, "duplicate_requests":0, "successes":0, "failures":0}
	events = {}
	for event in get_events(log_files, start_event, end_event, options.delimiter):

	import pdb; pdb.set_trace()
	stats["failures"]=len(requests)

	print_stats(stats)

if __name__ == "__main__":
	main()