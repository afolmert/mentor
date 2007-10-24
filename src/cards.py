#!/usr/bin/env python
# -*- coding: iso-8859-2 -*-
#
# Copyright (C) 2007 Adam Folmert <afolmert@gmail.com>
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
#
#
"""This is module for managing cards: storage, management, reptition algorithms,
scheduling etc."""

import release
import sqlite3
from config import config
from misc import log

__version__ = release.version


# TODO write Qt Model  using my cards object (cached?)



# Each card will have unique id generated from database
#

class Card(object):
    """Basic in-memory card object. """
    def __init__(self, id=None, question='', answer='', question_hint='', answer_hint='', score=None):
        self.id            = id
        self.question      = question
        self.answer        = answer
        self.question_hint = question_hint
        self.answer_hint   = answer_hint
        self.score         = score


    def __eq__(self, other):
        return self.id         == other.id \
        and self.question      == other.question \
        and self.answer        == other.answer \
        and self.question_hint == other.question_hint \
        and self.answer_hint   == other.answer_hint \
        and self.score         == other.score

    def __str__(self):
        return str((self.id,
                  self.question,
                  self.answer,
                  self.question_hint,
                  self.answer_hint,
                  self.score))


    def clear(self):
        self.id            = None
        self.question      = ''
        self.answer        = ''
        self.question_hint = ''
        self.answer_hint   = ''
        self.score         = None



# Cards will be stored in sqlite database
# Once opened, each operation will make a commit on the database, so in case of
# a crash, the data is always safe.
#
#
class Cards(object):
    """Cards storage. This is an interface for sqlite database keeping cards."""
    def __init__(self):
        self.db = None
        pass

    def open(self, dbpath):
        """Opens or creates Card database. Use :memory: to open database in memory. """
        self.db = sqlite3.connect(dbpath)
        self.init_database()

    def check_db(self):
        assert self.db is not None, "Database not open."

    def init_database(self):
        self.check_db()
        cur = self.db.cursor()
        # check if tables exist
        try:
            result = cur.execute('SELECT VERSION FROM TVERSION')
            row = result.fetchone()
            assert row[0] == config.DB_VERSION, "Unknown database format."
            db.rollback()
        except:
            # if not exist
            cur.execute(r'''CREATE TABLE TCARDS (
                              ID             INTEGER PRIMARY KEY,
                              QUESTION       TEXT,
                              ANSWER         TEXT,
                              QUESTION_HINT  TEXT,
                              ANSWER_HINT    TEXT,
                              SCORE          NUMERIC
                              )
                          ''')
            cur.execute(r'''CREATE TABLE TVERSION (
                              VERSION        TEXT
                            )''' )
            cur.execute('INSERT INTO TVERSION ( VERSION ) VALUES ( ? ) ', (config.DB_VERSION,))
            self.db.commit()
            cur.close()


    def close(self):
        self.check_db()
        assert self.db is not None, "Database not open."
        if self.db:
            self.db.close()
            self.db = None


    def add_card(self, card):
        """Adds a card object to database and returns it's id object."""
        self.check_db()
        cur = self.db.cursor()
        cur.execute(r'''INSERT INTO TCARDS ( QUESTION, ANSWER, QUESTION_HINT, ANSWER_HINT, SCORE )
                          VALUES ( ? , ? , ? , ?, ? ) ''', \
                          (card.question,
                           card.answer,
                           card.question_hint,
                           card.answer_hint,
                           card.score))
        # TODO how to retrieve information about last without running
        # additional query ?
        # TODO remove the query if lastrowid is ok
        lastrowid = cur.lastrowid
        result = cur.execute('SELECT MAX(ID) FROM TCARDS').fetchone()[0]
        assert lastrowid == result, "Internal error: Lastrowid does not return MaxID!"
        cur.close()
        self.db.commit()
        return result


    def get_card(self, card_id):
        """Retrieves a card from database given it's id or None if it does not exist."""
        # TODO
        self.check_db()
        cur = self.db.cursor()
        rows = cur.execute(r'''SELECT ID, QUESTION, ANSWER, QUESTION_HINT, ANSWER_HINT, SCORE
                                 FROM TCARDS
                                WHERE ID = ?
                            ''', (card_id,))
        row = rows.fetchone()
        card = Card(*row)
        cur.close()
        return card

    def exists_card(self, card_id):
        """Returns True if given card_id exists in database."""
        self.check_db()
        cur = self.db.cursor()
        rows = cur.execute('SELECT ID FROM TCARDS WHERE ID = ?', (card_id,))
        row = rows.fetchone()
        exists = row is not None
        cur.close()
        return exists


    def delete_card(self, card_id):
        """Deletes a card from database given it's id"""
        self.check_db()
        cur = self.db.cursor()

        cur.execute(r'''DELETE FROM TCARDS WHERE ID = ? ''', (card_id,))
        assert cur.rowcount == 1, "Problem when updating card = %s" % card_id
        cur.close()
        self.db.commit()


    def update_card(self, card):
        """Updates a card in database using it's id and other fields. """
        self.check_db()
        cur = self.db.cursor()
        cur.execute(r'''UPDATE TCARDS
                          SET QUESTION    =  ?
                          , ANSWER        =  ?
                          , QUESTION_HINT =  ?
                          , ANSWER_HINT   =  ?
                          , SCORE         =  ?
                          WHERE ID        =  ?
                    ''', (card.question,
                          card.answer,
                          card.question_hint,
                          card.answer_hint,
                          card.score,
                          card.id))
        assert cur.rowcount == 1, "Problem when updating card %s" % card.id
        cur.close()
        self.db.commit()


    def get_cards_count(self):
        """Returns number of cards in the database."""
        self.check_db()
        cur = self.db.cursor()

        rows = cur.execute('''SELECT COUNT(*) FROM TCARDS''')
        result = rows.fetchone()[0]
        cur.close()
        return result


    def log_cards(self, sqlwhere='', max=None):
        """Helper function for logging cards with given sqlwhere condition."""
        self.check_db()
        cur = self.db.cursor()
        if sqlwhere.strip() != '':
            sqlwhere = 'WHERE %s' % sqlwhere
        rows = cur.execute(r'''SELECT ID, QUESTION, ANSWER, QUESTION_HINT, ANSWER_HINT, SCORE
                              FROM TCARDS %s''' % sqlwhere)
        try:
            i = 0
            row = -1
            while row is not None and (max is None or i < max):
                row = rows.fetchone()
                if row:
                    log('id:%-10s q:%-10s a:%-10s qh:%-10s ah:%-10s sc:%-10s' % row)
                i += 1
        except:
            raise
        cur.close()
