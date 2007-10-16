#!/bin/env python
# -*- coding: utf-8 -*-
#
# This file is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

"""
This is a script for managing word freq database.

It allows import of new text files and freq files. Also displaying of existing files.
The freq database is stored in sqlite file.
"""

__version__ = "0.0.01"

import sqlite3
from misc import enable_logging, log
import sys
import re



class FreqDatabase(object):
    """This is a wrapper on freq sqlite3 database."""
    def __init__(self, dbpath):
        self.connection = sqlite3.connect(dbpath)
        self.init_tables()

    def init_tables(self):
        """Checks if tables exist - if no it generates them."""
        cur = self.connection.cursor()
        try:
            # test
            cur.execute('INSERT INTO TFREQ (WORD, OCCUR, POSITION, POSITION_LVL) VALUES ("test123test", 1, 1, 1)')
            self.connection.rollback()
        except:
            cur.execute('CREATE TABLE TFREQ (WORD TEXT, OCCUR NUMBER, POSITION NUMBER, POSITION_LVL NUMBER)')
            cur.execute('CREATE UNIQUE INDEX XI_TFREQ_WORD ON TFREQ (WORD) ')
            cur.execute('CREATE INDEX XI_TFREQ_LVL ON TFREQ (POSITION_LVL) ')
        finally:
            cur.close()


    def import_word(self, word, occur=1):
        """Import a word to table with given occur value."""
        cur = self.connection.cursor()
        try:
            # clear the invalid chars
            word = word.strip().lower().replace('"', '\'')
            if word != "":
                # first try to update - if not exist then insert
                cur.execute('UPDATE TFREQ SET OCCUR = OCCUR + ? WHERE WORD = ?', (occur, word))
                if cur.rowcount == 0:
                    cur.execute('INSERT INTO TFREQ(WORD, OCCUR) VALUES (?, ?) ', (word, occur))
        finally:
            cur.close()



    def print_rows(self, max=100):
        """Prints rows from database."""
        cur = self.connection.cursor()
        try:
            for row in cur.execute('SELECT WORD, OCCUR, POSITION, POSITION_LVL FROM TFREQ WHERE POSITION < ? ORDER BY POSITION', (max,)):
                print "WORD: %-15s OCCUR: %-8d POS: %-5d POS_LVL: %-5d" % (row[0], row[1], row[2], row[3])
        finally:
            cur.close()


    def recalc_positions(self):
        """Update the position and position_lvl columns in database."""
        pos = 1
        cur = self.connection.cursor()
        cur2 = self.connection.cursor()
        try:
            for row in cur.execute('SELECT WORD FROM TFREQ ORDER BY OCCUR DESC, WORD'):
                cur2.execute('UPDATE TFREQ SET POSITION = ?, POSITION_LVL = ? WHERE WORD = ?',
                    (pos, (pos / 1000)+1, row[0]))
                pos += 1

        finally:
            cur.close()
            cur2.close()


    def commit_database(self):
        self.connection.commit()





# main program

def get_version_info():
    return "freq 0.01  frequency database helper tool"

# add full usage info
#
def get_usage_info():
    return """freq.py command database [options]

Commands:
  print                 prints database contents
  import                import a file (use with -t and -f options)

Options:
  -h, --help            show this help message and exit
  -d, --debug           run program in debugged mode
  -v, --verbose         print output verbosely
  -f FILE, --frequency=FILE
                        specifices a frequency file in format: word occur;
                        used with import command
  -t FILE, --text=FILE  specifies a text file to import; used with import
                        command
  -p, --print           run a a simulation only
  -l LIMIT, --limit=LIMIT
                        limit printing results to count; used with print
                        command.
"""


def print_db_rows(db, limit):
    """Prints database rows."""
    db.print_rows(limit)


def msg(text):
    print text
    sys.stdout.flush()

def import_text_file(db, fname):
    """Imports words from a text file."""
    msg("Importing words from file %s..." % fname)
    f = open(fname)
    content = f.read()
    cnt = 0
    f.close()
    words = re.split('\W+', content)
    for w in words:
        db.import_word(w)
        cnt += 1
    db.recalc_positions()
    db.commit_database()
    print "Imported %d words from file %s. " % (cnt, fname)


def import_freq_file(db, fname):
    """Imports words from a frequency file.
    Frequency file a text file with words and their occurrence count:
        word count
        word count
    """
    msg("Importing words from file %s..." % fname)
    f = open(fname)
    lines = f.readlines()
    f.close()
    cnt = 0
    for l in lines:
        word, occur = l.strip().split(" ")
        try:
            occur = int(occur.strip())
            word = word.strip()
        except:
            raise "Invalid format!"
        db.import_word(word, occur)
        cnt += 1
    db.recalc_positions()
    db.commit_database()
    print "Imported %d words from file %s." % (cnt, fname)


def main():
    """This is the main program."""
    from optparse import OptionParser

    class MyOptionParser(OptionParser):
        def format_option_help(self, formatter=None):
            return ""
    parser = MyOptionParser(version=get_version_info(), usage=get_usage_info())


    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=True,
                      help="run program in debugged mode" )
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="print output verbosely")
    parser.add_option("-f", "--freq", action="store", dest="frequency",
                      metavar="FILE", help="specifices a frequency file in format: word occur; used with import command")
    parser.add_option("-t", "--text", action="store", dest="text",
                      metavar="FILE", help="specifies a text file to import; used with import command")
    parser.add_option("-p", "--print", action="store_true", dest="pretend", default=False,
                      help="run a a simulation only")
    parser.add_option("-l", "--limit", action="store", type="int", dest="limit", default=100,
                      help="limit printing results to count; used with print command.")

    opts, args = parser.parse_args(sys.argv[1:])

    if opts.debug:
        enable_logging(True)
    else:
        enable_logging(False)

    if len(args) < 2:
        print get_usage_info()
        sys.exit()

    command = args[0].upper()
    dbpath = args[1]
    db = FreqDatabase(dbpath)

    # dispatching commands
    if command == 'PRINT':
        print_db_rows(db, opts.limit)
    elif command == 'IMPORT':
        if opts.text:
            import_text_file(db, opts.text)
        elif opts.frequency is not None:
            import_freq_file(db, opts.frequency)
        else:
            print "No import file specified. Use -f or -t option. "
    else:
        print "Unknown command %s " % command




if __name__ == '__main__':
    main()
