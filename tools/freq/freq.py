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
            cur.execute('SELECT WORD, OCCUR, POSITION, POSITION_LVL FROM TFREQ')
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
            # first try to update - if not exist then insert
            cur.execute('UPDATE TFREQ SET OCCUR = OCCUR + ? WHERE WORD = ?', (occur, word))
            if cur.rowcount == 0:
                cur.execute('INSERT INTO TFREQ(WORD, OCCUR) VALUES (?, ?) ', (word, occur))
        finally:
            cur.close()



    def print_rows(self, max=100):
        """Prints rows from database."""
        pos = 1
        cur = self.connection.cursor()
        try:
            for row in cur.execute('SELECT * FROM TFREQ ORDER BY POSITION'):
                print row
                pos += 1
                if pos > max:
                    break
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


# add full usage info
#
def print_usage():
    print "Usage: freq command database [options]"
    print "Commands: "
    print "print     Prints database contents"
    print "import    Imports a file"

def print_db_rows(db):
    pass

def import_text_file(db, fname):
    pass


def import_freq_file(db, fname):
    pass


def main():
    """This is the main program."""
    from optparse import OptionParser

    parser = OptionParser(version=__version__)
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=True,
                      help="run program in debugged mode" )
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="print output verbosely")
    parser.add_option("-f", "--frequency", action="store", dest="frequency",
                      help="specifices a frequency file in format (word, occur). Used with import command")
    parser.add_option("-t", "--text", action="store", dest="text",
                      help="specifies a text file to import. Used with import command")
    parser.add_option("-p", "--print", action="store_true", dest="pretend", default=False,
                      help="run a a simulation only")

    opts, args = parser.parse_args(sys.argv[1:])

    if opts.debug:
        enable_logging(True)
    else:
        enable_logging(False)

    if len(args) < 2:
        print_usage()
        sys.exit()

    command = args[0].upper()
    dbpath = args[1]


    db = FreqDatabase(dbpath)

    if command == 'PRINT':
        db.print_rows()
    elif command == 'IMPORT':
        if opts.text is not None:
            f = open(opts.text)
            content = f.read()
            f.close()
            words = re.split('\W+', content)
            for w in words:
                db.import_word(w)
            db.recalc_positions()
            db.commit_database()
            print "File %s imported. " % opts.text
        else:
            print "No import file specified. Use -f or -t option. "


if __name__ == '__main__':
    main()
