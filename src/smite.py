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

class Tokenizer(object):
    """This will take care of reading tokens from file.
    Currently it just reads lines from file.
    It will be wrapper around file-like object.
    You can pass it a file name or file like object
    - it will work only on text file objects.
    """

    def __init__(self, fname):
        self.fname = fname
        self.fobject = open(self.fname, "rt")
        self.lines = self.fobject.readlines()
        self.counter = 0
        self.fobject.close()

    def get_next_line(self):
        """Returns next line or raises an exception."""
        if self.counter < len(self.lines):
            return self.lines[self.counter]

    def push_back_line(self):
        """Pushes last read line to stack. Raises exception if line was not
        """
        if self.counter > 0:
            self.counter -= 1
        else:
            raise TokenizerError, "Cannot push back one last line."

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
        f = open(fname)

        for l in f.readlines():
            print "Read one line : "
            print l
            # remove multiple tabs
            groups = find_regroups(l, "(.*)\t+(.*)")
            if groups and len(groups) == 3:
                log("line $l matches tabulation.")
                question = groups[1]
                answer = groups[2]
                items.add_item(question, answer)
            else:
                log("no tabs found in $l")

        for l in f.readlines():
            print "Do something I don't like:"
            print 20




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

class MainParser(Parser):
    """This will be a general class for parsing text files.
    It will read whole files and act according to the SML syntax
    given in the file.
    It will initiate specific import classes and keep track of the
    options.
    """

    def __init__(self):
        # initialize options
        self.use_swap = False
        self.use_dict = False
        self.use_other_option = True


    # TODO maybe put these options into general parser class
    def parse_options(self, options):
        """This will parse options embedded in begin or option statement."""
        pass

    def parse_begin(self, statement):
        """This will parse the begin statement.
        The begin statement is in form \begin{class} where
        the class denotes how to parse the incoming content."""
        groups =
        pass

    def parse_end(self, statement):
        """Returns result of parsed end statement."""
        pass

    def parse_options(self, statement):
        """Returns result of parsed options statement."""
        pass

    def parse_file(self, fname):
        # open file , read it line by line
        # if encounters syntax item then interpret it in some way
        # specific environment parsers will be launched
        # depending on the texts given.
        f = open(fname, 'rt')
        contents = []
        using_parser = False
        for l in f.readlines():
            print l
            # if in string is \begin statement then it is the beginning
            if l.startswith('\\begin'):
                using_parser = True
                class = self.parse_begin(l)
            # if there is end
            if l.startswith('\\end'):
                using_parser = False
                # depending on the text, create a specific parser
#
            # here find the tag
            # and use it if it's good
            # find the proper class to begin with
        f.close()


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
    importer.parse_file("d:/temp/SMITE/input.txt", items)

    items.debug_items()


    export = SuperMemoExporter()
    export.export_file("d:/temp/SMITE/output.txt", items)



def main():
    enable_logging()
    log("testing this name..")
    a = 123
    log("this is $a great.")
    demo_fill_items()




if __name__ == "__main__":
    main()

# 1}}}

