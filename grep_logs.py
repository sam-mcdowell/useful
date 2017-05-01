from dateutil.parser import parse
from datetime import datetime, timedelta
import optparse
import re
import tempfile
from multiprocessing import Pool


ENVS = {
"afm": ["root@web{}.afm.sfdc.wavemarket.com".format(i) for i in range(1, 9)],
}


def get_timestamp(line):
    if "|" in line:
        return parse(line.split("|")[1])
    else:
        return None

def get_mdn(line):
    return re.findall(r"\D(\d{10})\D", line).pop()

def capture_stack_trace(lines):
   stack_trace = []
   while: 


def main():
    parser = optparse.OptionParser(usage="%prog search_term [options]")
    parser.add_option("--product", default="afm", dest="product",
       help="date to start at, leave blank for today only")
    parser.add_option("--start_date", default=None, dest="start_date",
        help="date to start at, leave blank for today only")
    parser.add_option("--end_date", default=None, dest="end_date")
    parser.add_option("-c", action="store_true", dest="capture_stack", default=False,
       help="attempt to store stack traces for any Exceptions found")

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        return -1

    worker_pool = Pool(8)
    log_results = worker_pool.map(get_logs, ENVS[options.product])