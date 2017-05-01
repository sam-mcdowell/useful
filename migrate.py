#!/usr/bin/python

import optparse
import subprocess
import re

DROP_TABLES=False
VERBOSE=True

def convert_camel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def mutation(a,b):
    if a == convert_camel(b):
        return True
    if b == convert_camel(a):
        return True
    if a == b+"_id":
        return True
    if b == a+"_id":
        return True
    if a == b+"Id":
        return True
    if b == a+"Id":
        return True
    return False

def get_schema(from_db, to_db, user, pw):
    subprocess.call("mysqldump -u%s -p%s %s --no-data=true --add-drop-table=false > from.sql" % (user, pw, from_db)
                    , shell=True)
    subprocess.call("mysqldump -u%s -p%s %s --no-data=true --add-drop-table=false > to.sql" % (user, pw, to_db)
                    , shell=True)

def make_migration():
    global DROP_TABLES
    global VERBOSE
    from_schema = open("from.sql", 'r')
    to_schema = open("to.sql", 'r')
    tables={}
    from_lines=from_schema.readlines()
    to_lines=to_schema.readlines()
    from_schema.close()
    to_schema.close()

    i=0
    while i<len(from_lines):
        if from_lines[i].find("CREATE TABLE") != -1:
            table_name = from_lines[i].split("`")[1]
            START = i
            i+=1
            while from_lines[i].find(") ENGINE=") == -1:
                i+=1
            END = i
            tables[table_name]=[[START,END],[]]
        i+=1

    i=0
    while i<len(to_lines):
        if to_lines[i].find("CREATE TABLE") != -1:
            table_name = to_lines[i].split("`")[1]
            START = i
            i+=1
            while to_lines[i].find(") ENGINE=") == -1:
                i+=1
            END = i
            tables.setdefault(table_name,[[],[]])
            tables[table_name][1]=[START,END]
        i+=1
    subprocess.call("rm migrate.log",shell=True)
    subprocess.call("rm migrate.sql",shell=True)
    log=open("migrate.log", 'w')
    migration=open("migrate.sql", 'w')
    migration.write("set foreign_key_checks=0; \n")
    dropped_tables = False
    dropped_columns = False
    for key in tables.iterkeys():
        _from=len(tables[key][0])>0
        _to=len(tables[key][1])>0
        if not _from:
            log.write("adding full new table %s \n" % key)
            i=tables[key][1][0]
            while i < (tables[key][1][1] + 1):
                migration.write(to_lines[i])
                i+=1
            migration.write(" \n")
        else:
            if not _to:
                dropped_tables = True
                if DROP_TABLES:
                    log.write("found table %s which is no longer being used, adding DROP TABLE statment \n"% key)
                    migration.write("DROP TABLE %s; \n" % key)
                else:
                    log.write("found table %s which is no longer being used, but DROP_TABLES is false \n" % key)
            else:
                lines={}
                statement=[]
                constraints=[]
                keys=[]
                i=tables[key][0][0]+1
                while i<tables[key][0][1]:
                    column_name = from_lines[i].split("`")[1]
                    lines.setdefault(column_name,[None,None])
                    if lines[column_name][0] is not None:
                        lines.setdefault(from_lines[i].strip(' ,\t\n\r'),[None,None])
                        lines[from_lines[i].strip(' ,\t\n\r')][0] = from_lines[i].strip(' ,\t\n\r') + ",\n"
                    else:
                        lines[column_name][0] = from_lines[i].strip(' ,\t\n\r') + ",\n"
                    i+=1
                i=tables[key][1][0]+1
                while i<tables[key][1][1]:
                    column_name = to_lines[i].split("`")[1]
                    lines.setdefault(column_name,[None,None])
                    if lines[column_name][1] is not None:
                        lines.setdefault(to_lines[i].strip(' ,\t\n\r'),[None,None])
                        lines[to_lines[i].strip(' ,\t\n\r')][1] = to_lines[i].strip(' ,\t\n\r') + ",\n"
                    else:
                        lines[column_name][1] = to_lines[i].strip(' ,\t\n\r') + ",\n"
                    i+=1
                differ = False
                dropped_column = False
                for col in lines.iterkeys():
                    inFrom = lines[col][0] is not None
                    inTo = lines[col][1] is not None
                    if not inFrom:
                        changed = False
                        for check_col in lines.iterkeys():
                            if col != check_col and mutation(col,check_col):
                                changed = True
                        if not changed:
                            if not differ:
                                log.write("table %s differed by at least one column \n" % key)
                                differ = True
                            add_line = "  ADD " + lines[col][1]
                            if add_line.find("CONSTRAINT") != -1:
                                constraints.append(add_line)
                            elif add_line.find("KEY") != -1:
                                keys.append(add_line)
                            else:
                                statement.append(add_line)
                    else:
                        if not inTo:
                            changed = False
                            column_name = col
                            if col.find("KEY")!=-1: #this is slightly hacky, relies the the fact that mysql formats all create tables such that primary keys will come after column declarations. It works, but makes me slightly uncomforatble
                                column_name = col.split("`")[1]
                            for check_col in lines.iterkeys():
                                if col != check_col and mutation(col,check_col):
                                    change_line = "  CHANGE " + col + " " + lines[check_col][1]
                                    statement.append(change_line)
                                    changed = True
                                    log.write("CAUTION: changing column name in %s from %s to %s \n" % (key,column_name,check_col))
                            if not changed:
                                if not differ:
                                    log.write("table %s differed by at least one column \n" % key)
                                    differ = True
                                log.write("CAUTION: dropping column %s from table %s, make sure this is correct! \n" % (col,key))
                                dropped_columns = True
                                drop_line = "  DROP %s, \n" % column_name
                                statement.append(drop_line)
                        else:
                            if lines[col][0] != lines[col][1]:
                                if not differ:
                                    log.write("table %s differed by at least one column \n" % key)
                                    differ = True
                                modify_line = "  MODIFY " + lines[col][1]
                                if modify_line.find("CONSTRAINT") != -1:
                                    constraints.append(modify_line)
                                elif modify_line.find("KEY") != -1:
                                    keys.append(modify_line)
                                else:
                                    statement.append(modify_line)
                if differ:
                    migration.write("ALTER TABLE %s \n" % key)
                    for i in statement:
                        migration.write(i)
                    for i in keys:
                        migration.write(i)
                    for i in constraints:
                        migration.write(i)
                    engine = " " + to_lines[tables[key][1][1]].split(")")[1] + " \n"
                    migration.write(engine)
    migration.write("set foreign_key_checks=1;")
    log.close()
    migration.close()
    if dropped_tables:
        print("drop table statements are required for this migration to be complete, \n please check the log file and final migration to ensure this is done correctly")
    if dropped_columns:
        print("CAUTION: at least one table is dropped by this migration, please check \n the log and migration to ensure this isn't a mistake")

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