#!/usr/bin/python

import optparse
import re
from dateutil.parser import parse
from datetime import datetime,timedelta
from math import floor

def get_timestamp(line):
	if "|" in line:
		return parse(line.split("|")[1])
	else:
		return None

def get_mdn(line):
	return re.findall(r"\D(\d{10})\D", line).pop()

def parse_line(line, index):
	if "LPSRequestService" in line:
		return {"timestamp":get_timestamp(line), 
				"type":"request", 
				"mdn":get_mdn(line),
				"index":index}
	elif "LocationResponse" in line:
		return {"timestamp":get_timestamp(line), 
				"type":"response", 
				"mdn":get_mdn(line),
				"success": "isError=false" in line}
	else:
		return None

def get_events(log_file, start_date, end_date):
	log = open(log_file, 'r').readlines()
	for line in log:
		timestamp = get_timestamp(line)
		if timestamp is None:
			continue
		if timestamp<start_date:
			continue
		if timestamp>end_date:
			break
		if "LPSRequestService" in line or "LocationResponse" in line:
			yield line

def parse_start_date(log, start):
	log_start = get_timestamp( open(log, 'r').readline() )
	return log_start.replace(hour=int(start), minute=0, second=0, microsecond=0)

def add_stats_window(stats, timestamp):
	stats.append({"start_time": timestamp, "total_requests":0, "total_successes":0, "total_time_successes":0, "orphaned_responses":0,"orphaned_requests":0, "total_failures":0,"total_time_failures":0,})
	return stats

def calculate_latencey(request, response):
	return (response["timestamp"]-request["timestamp"]).total_seconds()

def print_stats(stats):
	for stats_window in stats:
		print(stats_window["start_time"])
		print("   total requests    :   {}".format(stats_window["total_requests"]))
		print("   total successess  :   {}".format(stats_window["total_successes"]))
		print("   total failures    :   {}".format(stats_window["total_failures"]))
		print("   repeated requests :   {}".format(stats_window["orphaned_requests"]))
		print("   response rate     :   {}%".format(int((stats_window["total_successes"]+stats_window["total_failures"])*100.0
													/(stats_window["total_requests"]))))
		if stats_window["total_successes"] > 1:
			print("   success rate      :   {}%".format(int(((stats_window["total_successes"]*100.0)/(stats_window["total_requests"])))))
			print("   success latency   :   {}s".format(int(((stats_window["total_time_successes"]+1.0)/(stats_window["total_successes"])))))

		if stats_window["total_failures"] > 1:
			print("   failure latency   :   {}s".format(int(((stats_window["total_time_failures"]+1.0)/(stats_window["total_failures"])))))

		print("")

def main():
	parser = optparse.OptionParser(usage = "%prog log_file [options]")
	parser.add_option("--start", default = 0, dest = "start")
	parser.add_option("--stop", default = 24, dest = "stop")
	parser.add_option("--window", default = 60, dest = "window")

	(options, args) = parser.parse_args()
	if len(args) != 1:
		parser.print_help()
		return -1

	log = open(args[0], 'r').readlines()
	if len(log)<1:
		return

	START_DATE = parse_start_date(args[0], options.start)
	END_DATE = START_DATE + timedelta(hours=int(options.stop))
	window = START_DATE + timedelta(minutes=int(options.window))
	stats = []
	stats = add_stats_window(stats, START_DATE)
	requests = {}
	index = 0
	for line in get_events(args[0], START_DATE,END_DATE):
		parsed_line = parse_line(line, index)
		if not parsed_line:
			continue
		while parsed_line["timestamp"]>window:
			stats = add_stats_window(stats, window)
			window = window+timedelta(minutes=int(options.window))
			index += 1
		mdn = parsed_line["mdn"]
		request = requests.pop(mdn, False)
		if parsed_line["type"] == "request":
			if request:
				stats[index]["orphaned_requests"] += 1
			requests[mdn] = parsed_line
			stats[index]["total_requests"] += 1
		else:
			if request:
				if parsed_line["success"]:
					stats[request["index"]]["total_successes"] += 1
					stats[request["index"]]["total_time_successes"] += calculate_latencey(request, parsed_line)
				else:
					stats[request["index"]]["total_failures"] += 1
					stats[request["index"]]["total_time_failures"] += calculate_latencey(request, parsed_line)
			else:
				stats[index]["orphaned_responses"] += 1

	print_stats(stats)

if __name__ == "__main__":
	main()