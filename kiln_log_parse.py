import optparse
import subprocess
import re


def main():
    USER = "root"
    PASSWORD = "root"

    parser = optparse.OptionParser(usage = "%prog migrate_from migrate_to [options]")
    parser.add_option("--user", default = USER, dest = "user",
                      help = "database user (default: " + USER + ")")
    parser.add_option("--password", default = PASSWORD, dest = "password",
                      help = "database password (default: " + USER + ")")
    parser.add_option("--drop", default = False, dest = "drop",
                      help = "include drop table statements (default: False )")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    parser.add_option("-s", "--skip",
                      action="store_true", dest="skip", default=False,
                      help="use pre-existing to.sql and from.sql files")
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        return -1
    global VERBOSE
    VERBOSE=options.verbose
    global DROP_TABLES
    DROP_TABLES=options.drop
    if not options.skip:
        get_schema(args[0], args[1], options.user, options.password)
    make_migration()

if __name__ == "__main__":
    main()