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
"""This is module for managing cards: storage, management, repetition algorithms,
scheduling etc."""

import release
import sqlite3
from config import gui_config as config
import sys
from utils import nvl, log

__version__ = release.version


# TODO write Qt Model  using my cards object (cached?)
# mode lcaching result ?
# create index - create for first record
  # for nth record in database
  # what about filters and sorting
  # refresh
  # get index get next basing on current sorting criteria

  # I think i will have to read all and refresh on demand ?
  # display name and id and the rest will be read on demand
  #
  # how the model works
  # how many doe it reads?
  #
  # what if I had 1000 in database
  # i would read in chunks
  # read 1000 and if asked then fetch more
  #
  # first try to do one without model just ismple load to list
  # see how qt model works !!!





# Each card will have unique id generated from database
#

class Card(object):
    """Basic in-memory card object. """
    def __init__(self, id=None, question='', answer='', question_hint='', answer_hint='', score=None):
        self.id            = int(id) if id is not None else None
        self.question      = str(question)
        self.answer        = str(answer)
        self.question_hint = str(question_hint)
        self.answer_hint   = str(answer_hint)
        self.score         = str(score)


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

    def isEmpty(self):
        return self.question == '' and self.answer == ''



# Cards will be stored in sqlite database
# Once opened, each operation will make a commit on the database, so in case of
# a crash, the data is always safe.
#
#
class Cards(object):
    """Cards storage. This is an interface for sqlite database keeping cards."""

    class CardsError(Exception) : pass
    class CannotOpenDatabaseError(CardsError) : pass
    class DataNotFoundError(CardsError) : pass


    def __init__(self):
        self.db_path = None
        self.db = None

    def open(self, dbpath):
        """Opens or creates Card database. Use :memory: to open database in memory. """
        # close if currently open
        if self.db:
            self.db.close()
        # try to open
        try:
            self.db_path = dbpath
            self.db = sqlite3.connect(dbpath)
            self.initDb()
        except:
            log(sys.exc_info())
            self.db_path = None
            self.db = None
            raise Cards.CannotOpenDatabaseError, "Cannot open database: %s" % dbpath

    def close(self):
        if self.db:
            self.db.close()
        self.db_path = None
        self.db = None


    def isOpen(self):
        return self.db is not None

    def checkDbOpen(self):
        assert self.db is not None, "Database not open."

    def initDb(self):
        self.checkDbOpen()
        cur = self.db.cursor()
        # check if tables exist
        try:
            result = cur.execute('SELECT VERSION FROM TVERSION')
            row = result.fetchone()
            assert row[0] == config.DB_VERSION, "Unknown database format."
        except:
            # if not supported version then we recreate the database
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


    def commit(self):
        self.checkDbOpen()
        self.db.commit()


    def addCard(self, card, commit=True):
        """Adds a card object to database and returns it's id object."""
        self.checkDbOpen()
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
        # move it to tests :
        # add a record, check max(ID) and compare if it's the id
        # returned actually by it's
        lastrowid = cur.lastrowid
        result = cur.execute('SELECT MAX(ID) FROM TCARDS').fetchone()[0]
        assert lastrowid == result, "Internal error: Lastrowid does not return MaxID!"
        cur.close()
        if commit:
            self.db.commit()
        return result


    def getCard(self, card_id):
        """Retrieves a card from database given it's id or None if it does not exist."""
        # TODO
        self.checkDbOpen()
        cur = self.db.cursor()
        rows = cur.execute(r'''SELECT ID, QUESTION, ANSWER, QUESTION_HINT, ANSWER_HINT, SCORE
                                 FROM TCARDS
                                WHERE ID = ?
                            ''', (card_id,))
        row = rows.fetchone()
        if row:
            card = Card(*row)
            cur.close()
            return card
        else:
            raise Cards.DataNotFoundError, "Card not found = %d " % card_id

    def getCardHeaders(self, sqlwhere='', minrow=None, maxrow=None):
        """Returns card ids using sqlwhere and minrow, maxrow range
        Params: minrow and maxrows are both counted from 0.
        Params: minrow is inclusive and maxrows is exclusive - this is similar to
        how range works:
        e.g.  getCardHeaders('', 1, 3) will return rows: 1 and 2
        """
        # using sqlite-only LIMIT clause for getting the result
        # from http://sqlite.org/lang_select.html:
        # "The LIMIT clause places an upper bound on the number of rows
        # returned in the result. A negative LIMIT indicates no upper bound.
        # The optional OFFSET following LIMIT specifies how many rows to skip
        # at the beginning of the result set. In a compound query, the LIMIT
        # clause may only appear on the final SELECT statement. The limit is
        # applied to the entire query not to the individual SELECT statement to
        # which it is attached."
        # in other words:
        # it firsts skips OFFSET records and then the rest is limited to max
        # LIMIT records
        self.checkDbOpen()
        cur = self.db.cursor()
        if sqlwhere.strip():
            sqlwhere = 'WHERE ' + sqlwhere
        sqllimit = ''
        if minrow is not None or maxrow is not None:
            if minrow is not None and maxrow is not None:
                assert minrow >= 0 and maxrow >= 0 and maxrow >= minrow, \
                    "Invalid minrow %s maxrow %s params" % (str(minrow), str(maxrow))
            maxrow = nvl(maxrow, -1)
            minrow = nvl(minrow, 0)
            limit = max(maxrow - minrow, -1) # if maxrow is -1 then we want all anyway
            offset = max(minrow, 0)
            sqllimit = 'LIMIT %d OFFSET %d' % (limit, offset)
        query = r'''SELECT ID, QUESTION FROM TCARDS %s %s''' % (sqlwhere, sqllimit)
        rows = cur.execute(query)
        result = rows.fetchall()
        cur.close()
        return result


    def existsCard(self, card_id):
        """Returns True if given card_id exists in database."""
        self.checkDbOpen()
        cur = self.db.cursor()
        rows = cur.execute('SELECT ID FROM TCARDS WHERE ID = ?', (card_id,))
        row = rows.fetchone()
        exists = row is not None
        cur.close()
        return exists


    def deleteCard(self, card_id):
        """Deletes a card from database given it's id"""
        self.checkDbOpen()
        cur = self.db.cursor()

        cur.execute(r'''DELETE FROM TCARDS WHERE ID = ? ''', (card_id,))
        assert cur.rowcount == 1, "Problem when updating card = %s" % card_id
        cur.close()
        self.db.commit()


    def deleteAllCards(self):
        """Deletes all cards from database"""
        self.checkDbOpen()
        cur = self.db.cursor()

        cur.execute(r'''DELETE FROM TCARDS''')
        cur.close()
        self.db.commit()



    def updateCard(self, card):
        """Updates a card in database using it's id and other fields. """
        self.checkDbOpen()
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


    def getCardsCount(self):
        """Returns number of cards in the database."""
        self.checkDbOpen()
        cur = self.db.cursor()

        rows = cur.execute('''SELECT COUNT(*) FROM TCARDS''')
        result = rows.fetchone()[0]
        cur.close()
        return result


    def logCards(self, sqlwhere='', max=None):
        """Helper function for logging cards with given sqlwhere condition."""
        self.checkDbOpen()
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
