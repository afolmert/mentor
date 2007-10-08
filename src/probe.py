#!/bin/env python
#
# this script  translated smite markup language text to supermemo
# items
#
#
from misc import istuple, matches, log, enable_logging, find_regroups
import re
import sys
import os

# TODO
# check out how parsers are written html/xml parsers??!
#

# TODO right now it may be a simple line-based parser in future version I may
# use pyparsing or write the parser myself

# {{{1 Item storage classes
# items is a list of tuples question - answer

class Item(object):
    """This is basic item for storing questions and answers."""
    def __init__(self, question="", answer=""):
        self.question = question
        self.answer = answer

    def get_question(self):
        return self.question

    def set_question(self, question):
        self.question = question

    def get_answer(self):
        return self.answer

    def set_answer(self, answer):
        self.answer = answer

    def __str__(self):
        return "q: %s\na: %s\n" % (self.question, self.answer)



class Items(object):
    """This is a basic of collection of items which are question and answers."""
    # todo provide iterator container for these
    def __init__(self):
        self.contents = []

    def add_item(self, question, answer):
        item = Item(question, answer)
        self.contents.append(item)

    def debug_items(self):
        print "Items of length %d" % len(self.contents)
        for it in self.contents:
            print str(it)

    def export_to_file(self, fname):
        f = open(fname, "rt")
        for it in self.contents:
            f.write(str(it))
            f.write("\n")
        f.close()


# 1}}}


# {{{1 Exporter classes


class Exporter(object):
    """This is a generic base exporter class for exporting all items.
    It can be overriden to export to supermemo or to other programs like mentor."""

    def __init__(self):
        pass

    def export_file(fname, items):
        """This is a procedure to export files to a file by given algorithm.
        It get's customized in lower algorithms.
        """
        pass

class SuperMemoExporter(Exporter):
    def __init__(self):
        Exporter.__init__(self)

    def export_file(self, fname, items):
        f = open(fname, "wt")
        for it in items.contents:
            f.write(str(it))
            f.write("\n")

        f.close()

class MentorExporter(Exporter):
    """This will be exporting to my custom Mentor program."""
    def __init__(self):
        Exporter.__init__(self)

    def export_file(self, fname, items):
        f = open(fname, "wt")
        for it in items.contents:
            f.write(str(it))
            f.write("\n")

# 1}}}


# {{{1 Tokenizer classes
# TODO in future versions it will be returning tokens like \tab spaces and \n
# Remove comments
# replace special chars

# tokenizer should work
# for example:
# \title[big,a12pt,title='Geez']{Title1}
# \section{Section1}
# \cloze{This is _first_question I will ask}
# \subsection{Section2}
# \set{Here I will ^ask some more^questions}
# this run by tokenizer should return:
#
#
# COMMAND \title
# CONTROL openbracket
# WORD big
# CONTROL comma
# WORD a12pt
# NUMBER
#
#
#
# CONTROL{BS}  WORD
#
#

class Token(object):
    """This will be a token returned by tokenizer object.
    It has the possibility to include all information from about given text:
    It may be one of the following:
    control
    specialchar
    whitespace
    text word
    comments will be ignored .

    """
    def __init__(self, type, value):
        self.type = type
        self.value = value



class Tokenizer(object):
    """This will take care of reading tokens from file.
    Currently it just reads lines from file.
    It will be wrapper around file-like object.
    You can pass it a file name or file like object
    - it will work only on text file objects.

    It should work either with file objects or with file name
    in that case it should open a file and have it converted to file object.

    It should work as a generator ie generating items only on demand.
    Or maybe it would work as DOM in that it will parse the whole file
    and build a tree itself
    Ok but tokenizer should not work like that.
    Read all contents in one go and look for tokens.


    I should raise errors in case of some basic syntatic errors occurring.
    """

    def __init__(self, fname):
        self.fname = fname
        self.fobject = open(self.fname, "rt")
        self.lines = self.fobject.readlines()
        self.counter = 0
        self.fobject.close()

        # initially stack of tokens is empty
        self.stack = []

    def open(self, fname):
        self.file = open(fname)


    def get_next_line(self):
        """Returns next line or raises an exception."""
        if self.counter < len(self.lines):
            return self.lines[self.counter]


    def get_next_token(self):
        """Returns next token from file. """
        # it will use regexps to find the next control char
        # and will prepare it accordingly
        # regexp will be used to omit comments which may exist
        # profusely
        # in default , whole file is a comment

        pass

    def push_back_line(self):
        """Pushes last read line to stack. Raises exception if line was not
        """
        if self.counter > 0:
            self.counter -= 1
        else:
            raise TokenizerError, "Cannot push back one last line."

    def push_back_token(self, token):
        """Pushes back token on stack. """
        pass

# 1}}}



# {{{1 Parser classes
# TODO
# the classes should be more like file-objects
# wich - > they should get file objets and read data from them ]
# until is enough


### {{{2 Generic parser class
class Parser(object):
    """This is the base for all importer classes."""
    def __init__(self):
        pass

    def parse_file(self, tokenizer, items):
        """This procedure is run on files to import items.
        It is customized in objects which inherit from this class."""
        pass

### 2}}}

### {{{2 Custom parser classes

class TabbedParser(Parser):
    """This is a customized importer of tabbed file class.
    It imports text from file seperated by tabs putting stuff on the left as
    question and stuff on the right as answer."""
    def __init__(self):
        Parser.__init__(self)


    def parse_file(self, tokenizer, items):
        """Override parents import file"""
        pass




class SentenceParser(Parser):
    """This is a customized importer working on sentences."""

    def __init__(self):
        Parser.__init__(self)

    def parse_file(self, tokenizer, items):
        pass



class CodeParser(Parser):
    """This is a customized importer working on source code."""

    def __init__(self):
        Parser.__init__(self)

    def parse_file(self, tokenizer, items):
        pass


class PythonCodeParser(CodeParser):
    """This is a customized code importer working on Python code."""

    def __init__(self):
        CodeParser.__init__(self)

    def parse_file(self, tokenizer, items):
        pass

### 2}}}

### {{{2 Main parser class

# running parse on this file directly:
# for example:
# \title[big,a12pt,title='Geez']{Title1}
# \section{Section1}
# \cloze{This is _first_question I will ask}
# \subsection{Section2}
# \set{Here I will ^ask some more^questions}
# this run by tokenizer should return:

# 1. search for title
# 2. search for section, cloze, set or subsection regexp
# 3. if found then parse words looking for ^ or _ chars in case of set or cloze
# split words build words structure and asked words structure
#
# it will return: COMMAND


class ParseObject(object):
    def __init__(self):
        self.command        =  ""
        self.options        =  []
        self.text           =  []  # group of words or 2-words
        self.marked_text    =  [] # indicating which are marked specially


class MainParser(Parser):
    """This will be a general class for parsing text files.
    It will read whole files and act according to the probe syntax
    given in the file.
    It will initiate specific import classes and keep track of the
    options.
    TODO currently it uses a set of regexp to find the desired
    command (similarly to how highlighting works now).
    """

    def __init__(self):
        # initialize options
        self.use_swap = False
        self.use_dict = False
        self.use_other_option = True

        self.probe_regexp = re.compile("title\|cloze\|set\|section|\subsection")


    # TODO maybe put these options into general parser class
    def parse_options(self, options):
        """This will parse options embedded in begin or option statement."""
        pass

    def parse_begin(self, statement):
        """This will parse the begin statement.
        The begin statement is in form \begin{class} where
        the class denotes how to parse the incoming content."""
        # groups = ??
        pass

    def parse_end(self, statement):
        """Returns result of parsed end statement."""
        pass

    def parse_options(self, statement):
        """Returns result of parsed options statement."""
        pass

    def find_probe_regexp(self, text, start_from):
        # first compile a regexp which would include all the commands
        # title, section, subsection set and cloze

        # return tuple of Found/NotFound, Command, OptionsText, GroupText (if
        # exist) and EndPosition
        # re.find( text, start_from, self.probe_regexp )
        pass

    def parse_file(self, fobject):
        # open file , read it line by line
        # if encounters syntax item then interpret it in some way
        # specific environment parsers will be launched
        # depending on the texts given.

        result = [] # a list of parse objects
        contents = fobject.read()
        start_from = 0
        regexp = self.find_probe_regexp(contents, start_from)
        while regexp[0]:
            pass
            # assign options
            # create a parse object
            # and add it to result
            #
            # increase start_from by position start_from



### 2}}}

# 1}}}





# {{{1 Main program

items = Items()



def demo_fill_items():
    """This is sample demo procedure which will test input and output generation."""
    items.add_item("question 1", "answer 1")
    items.add_item("question 2", "answer 2")
    items.add_item("question 3", "answer 3")
    items.add_item("question 4", "answer 4")
    items.add_item("question 4", "answer 4")
    items.add_item("question 5", "answer 5")
    items.add_item("question 6", "answer 6")
    items.add_item("question 7", "answer 7")
    items.add_item("question 5", "answer 5")
    items.add_item("question 6", "answer 6")
    items.add_item("question 7", "answer 7")

    items.debug_items()

    importer = TabbedParser()
    importer.parse_file("d:/temp/input.txt", items)

    items.debug_items()


    export = SuperMemoExporter()
    export.export_file("d:/temp/output.txt", items)



def main():
    enable_logging()
    log("testing this name..")
    a = 123
    log("this is $a great.")
    demo_fill_items()




if __name__ == "__main__":
    main()

# 1}}}

