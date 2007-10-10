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
#
__version__ = "0.0.1"

from misc import istuple, matches, log, enable_logging, find_regroups, \
    Enumeration, error
from StringIO import StringIO
import re
import sys
import os

# ADD DEBUGGING / STR TO PARSERS ITEMS
# OPTION RESTRICTIONS LIKE IN OPTPARSE


# {{{1 Parser classes
# TODO
# the classes should be more like file-objects
# wich - > they should get file objets and read data from them ]
# until is enough


### {{{2 ParseOptions
# also positional and default options so I can write something like this
# \title[good]
# or \title[good, ok, best]
# or \title[good, type=ok]
# options should work as keyword arguments
# params: position, name, value
class ParseOptions(object):

    # possible options
    String, Enumeration, Integer = range(3)

    # only possible options
    """This class will restrict options to a given set."""
    def __init__(self):
        self.options = {}

    def clear(self):
        pass

    def add_option(self, name, type=None, default=None, values=None):
        # possible types String, Number, Enumeration
        # exlucding options, should exist or not
        # see opt parse syntax and do something like this
        self.options[name] = default

    def has_option(self, name):
        return self.options.has_key(name)

    def set_option(self, name, value):
        """This will check the type and value and existance."""
        assert self.options.has_key(name), "Option not available: " + name
        if value == "":
            value = True
        self.options[name] = value


    def get_option(self, name):
        """This will be overriden in parse object to return option as attribute"""
        assert self.options.has_key(name), "Option not available: " + name
        return self.options[name]
### 2}}} ParseOptions


### {{{2 ParseObject
class ParseObject(object):

    def __init__(self, parent=None, name="", content=""):
        self.parent = parent
        self.name = name
        self.content = content
        self.options = ParseOptions()
        self.children = []
        self.init_options()


    def add_child(self, child):
        """Appends child to parse object children."""
        assert issubclass(child.__class__, ParseObject)
        self.children.append(child)

    def set_option(self, name, value):
        self.options.set_option(name, value)

    def get_option(self, name):
        return self.options.get_option(name)

    def init_options(self):
        # here might register possible options and their types, and default values
        # and required, not required options
        # should just exist or should have a value etc.
        # declarative way of setting possible option values
        # self.add_option
        self.options.clear()
        self.options.add_option('init', ParseOptions.String, default='OK')
        self.options.add_option('sample', ParseOptions.Enumeration, values=['yes', 'no'])


    def __str__(self):
        # TODO print self and all children in a nice tree
        # print self
        # print all trees moved by indent
        pass
        # return "CMD: " + str(self.command) + " OPT: " + str(self.options) + " CONT: "  + str(self.content)
### 2}}} ParseObject


### {{{2 ParseText
class ParseText(ParseObject):
    """This is a simple object consisting of text."""

    # possibility to set a marker
    def __init__(self, parent=None, content='', marker=''):
        ParseObject.__init__(self, parent, content)
        self.content = content
        self.set_option('marker', marker)

    def __str__(self):
        return self.content

    def init_options(self):
        # restrict marker to _ and ^
        self.options.clear()
        self.options.add_option('marker', ParseOptions.Enumeration, values=('^', '_'))
### 2}}} ParseText


### {{{2 ParseCommand
# TODO this will be more elaborate to enable dynamically creating parse classes
# will be a function , register parse command - or not a function
# i will just put this file in plugins and it will read it's name and change it to command class
# will have to provide function for parse_content returning list of child object
ParseCommands = Enumeration("ParseCommands", ["title", "section", "cloze", "set", "subsection", "tabbed",
                                             "subsubsection"])

class ParseCommand(ParseObject):
    def __init__(self, parent=None, name="", options="", content=""):
        log("ParseCommand init.")
        ParseObject.__init__(self, parent, name)
        # check if name is one of given in enumeration
        # if not then raise error
        # set command to the value of enumeration
        self.parse_command(name)
        self.parse_options(options)
        self.parse_content(content)

    def __str__(self):
        pass

    def generate_items(self, options):
        """This will be also have to subclassed if I would have a plugin to write"""
        pass

    def parse_command(self, command):
        """Returns command from ParseCommands enumeration type."""
        log('parse_command for command = $command')
        self.command = ParseCommands.lookup[command]
        # ! enumaration not working !!!!
        # right now it does not do anything
        # TODO command should be enumerations which shall be returned in here

    def parse_content(self, content):
        """Returns content."""
        if len(content) > 2:
            self.content = content[1:-1]
        else:
            self.content = None

    def parse_options(self, options):
        """This will parse options embedded in begin or option statement."""
        log("parsing options $options")
        if options != None:
            options = options[1:-1]       # strip the [] brackets o
            options = options.split(",")

            for o in options:
                name, _, value = o.partition("=")
                name = name.strip()
                value = value.strip()
                if name != "":
                    self.set_option(name, value)

### 2}}} ParseCommand


### {{{2 Parse other custom classes
class ParseTitle(ParseCommand):
    """This is parser for the \\title command."""
    def init_options(self):
        self.options.clear()
        self.options.add_option('big')
        self.options.add_option('a12pt')
        self.options.add_option('title')

class ParseSection(ParseCommand):
    """This is parser for the \\section command."""
    def init_options(self):
        self.options.clear()
        self.options.add_option('sec2')


class ParseSubsection(ParseCommand):
    """This is a parser for the \\subsection command."""
    def init_options(self):
        self.options.clear()
        self.options.add_option('sec2')



class ParseClassCommand(ParseCommand):
    """This is generic class for class commands which process text."""

    def parse_content(self, content):
        """This will parse content and result a list of words with info on marked, unmarked."""
        log("parsing content: $content")
        if len(content) > 2:
            content = content[1:-1] # strip the { } braces
            words = re.split(" +", content)
            for w in words:
                # check for special marking in words
                marker = None
                if w.find('^') >= 0:
                    if w[0] == '^':
                        w = w[1:]
                    w = w.replace('^', ' ')
                    marker = '^'
                elif w.find('_') >= 0:
                    if w[0] == '_':
                        w = w[1:]
                    w = w.replace('_', ' ')
                    marker = '_'

                self.add_child(ParseText(self, w, marker))
            log("parsing contet end. ")



class ParseCloze(ParseClassCommand):
    """This is parser for the \\cloze command."""
    def init_options(self):
        self.options.clear()
        self.options.add_option('simple')
        self.options.add_option('area')
        self.options.add_option('hint')


class ParseSet(ParseClassCommand):
    """This is parser for the \\set class command."""
    def init_options(self):
        self.options.clear()
        self.options.add_option('simple')
        self.options.add_option('area')
        self.options.add_option('hint')


class ParseTabbed(ParseClassCommand):
    """This is parser the the \\tabbed class command."""
    pass


class ParseVerbatim(ParseClassCommand):
    """This is verbatim code parse command."""
    pass


class ParseCode(ParseClassCommand):
    pass


class ParsePythonCode(ParseClassCommand):
    """This is a customized code importer working on Python code."""
    pass


class ParseSentence(ParseCommand):
    """This is a customized importer working on sentences."""
    pass




### 2}}} Parse other custom classes


### {{{2 Main parser class

# Main parser class creates a abstract syntax tree of parse objects
#


class Parser(object):
    """This will be a general class for parsing text files.
    It will read whole files and act according to the probe syntax
    given in the file.
    It will initiate specific import classes and keep track of the
    options.
    TODO currently it uses a set of regexp to find the desired
    command (similarly to how highlighting works now).
    It does not use a full tokenizer yet.
    """

    def __init__(self):
        pass
        # find a command, then, optionally a [] block, and then, optionally a
        # {} block
        # what about maybe the regexp will be used as a start only and then it
        # will be parsed more reguralry
        # what about this { ass{}   } -> this will fail to be found
        # can a regexp make a counting progress? ?


    def parse_file(self, fobject):
        """Returns a tree of parsed objects read from file-like object."""
        # open file , read it line by line
        # if encounters syntax item then interpret it in some way
        # specific environment parsers will be launched
        # depending on the texts given.
        log('parse file begin')

        probe_regexp = re.compile("\\\\(title|section|cloze|set|subsection)(\[[^]]*\])?({[^}]*})?", re.M)


        root = ParseObject(parent=None, name='root') # a list of parse objects
        fcontent = fobject.read()
        patterns = re.findall(probe_regexp, fcontent, re.M)

        for p in patterns:
            if p[0] == "title":
                obj = ParseTitle(parent=root, name=p[0], options=p[1], content=p[2])
            elif p[0] == "section":
                obj = ParseSection(parent=root, name=p[0], options=p[1], content=p[2])
            elif p[0] == "subsection":
                obj = ParseSubsection(parent=root, name=p[0], options=p[1], content=p[2])
            elif p[0] == "subsubsection":
                obj = ParseCloze(parent=root, name=p[0], options=p[1], content=p[2])
            elif p[0] == "cloze":
                obj = ParseCloze(parent=root, name=p[0], options=p[1], content=p[2])
            elif p[0] == "set":
                obj = ParseSet(parent=root, name=p[0], options=p[1], content=p[2])

            root.add_child(obj)
        return root

        log('parse file end')

### 2}}}

# 1}}}


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

    def export_file(self, items, output=None):
        if output is None:
            f = sys.stdout
        else:
            f = open(output, "wt")
        for it in items.contents:
            f.write(str(it))
            f.write("\n")
        if output is not None:
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


# {{{1 Processor classes
# Here are main classes which use parser to get a parse tree of parse objects
# use it to build items
# and then use Exporter objects to export those items

class Processor(object):

    def __init__(self):
        pass
        # initialize options
        #self.use_swap = False
        #self.use_dict = False
        #self.use_other_option = True

    def build_question(self, words, hidenth):
        """Returns question build from given words, replacing hidenth with dots ... """
        words2 = []
        for i in range(len(words)):
            if i <> hidenth:
                words2.append(words[i])
            else:
                words2.append('...')
        return " ".join(words2)


    def build_prefix(self, section, subsection, subsubsection):
        """Returns prefix basing on section settings."""
        result = []
        if section is not None and section.strip() != "":
            result.append(section + ": ")
        if subsection is not None and subsection.strip() != "":
            result.append(subsection + ": ")
        if subsubsection is not None and subsubsection.strip() != "":
            result.append(subsubsection + ": ")
        return "".join(result)


    def process(self, input, output=None):
        """Processes input file and export output file.
        Utilizes input classes like Parser and output like Exporter
        Uses Items objects to build Items
        """
        finput = open(input, "rt")


        # parse tree
        parser = Parser()
        parse_tree = parser.parse_file(finput)
        finput.close()

        log('parse returned ' + str(len(parse_tree.children)) + ' children. ' )

        # process parse tree to create Items structure
        # is this step necessary ??

        # items
        # initialize variables
        title         = ""
        section       = ""
        subsection    = ""
        subsubsection = ""
        prefix        = "" # prefix used
        items         = Items()

        for obj in parse_tree.children:
            log( 'parsing for command: ' + str(obj.command))
            prefix = self.build_prefix(section, subsection, subsubsection)
            if obj.command == ParseCommands.title:#{{{
                title = obj.content
            elif obj.command ==  ParseCommands.section:
                section = obj.content
            elif obj.command == ParseCommands.subsection:
                subsection = obj.content
            elif obj.command == ParseCommands.subsubsection:
                subsubsection = obj.content
            elif obj.command == ParseCommands.set:
                log('processing set command ' )
                words = []
                question_words = []
                # for each word prepare a special item
                # except for marked items
                for i in range(0, len(obj.children)):
                    words.append(obj.children[i].content)
                    if obj.children[i].get_option('marker') != '^': # and not is in ignored words
                        question_words.append(i)

                for i in question_words:
                    question = self.build_question(words, i)
                    answer = words[i]

                    if not prefix.endswith(": "):
                        prefix = prefix + ": "
                    items.add_item(prefix + question, answer)

            elif obj.command == ParseCommands.cloze:
                log( 'processing cloze command. with $len(obj.children) children ' )
                words = []
                question_words = []
                # this will be in contrast to set
                # marked items will be included only
                for i in range(len(obj.children)):
                    words.append(obj.children[i].content)
                    if obj.children[i].get_option('marker') == '_':
                        question_words.append(i)


                log('cloze words: ' + str(words))
                log('cloze question words ' + str(question_words))
                for i in question_words:
                    question = self.build_question(words, i)
                    answer = words[i]

                    if not prefix.endswith(": "):
                        prefix = prefix + ": "
                    items.add_item(prefix + question, answer)#}}}


        # now export items using exporter
        exporter = SuperMemoExporter()
        exporter.export_file(items, output=None)


# 1}}} Processor classes


# {{{1 Main program

def main():
    """This is the main program."""
    from optparse import OptionParser

    parser = OptionParser(version=__version__)
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=True,
                      help="run program in debugged mode" )
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="print output verbosely")
    parser.add_option("-p", "--pretend", action="store_true", dest="pretend", default=False,
                      help="run a a simulation only")

    opts, args = parser.parse_args(sys.argv[1:])

    if opts.debug:
        enable_logging(True)
    else:
        enable_logging(False)


    if len(args) == 0:
        print "No input file specified. "
        sys.exit()

    input = args[0]
    processor = Processor()
    processor.process(input)


if __name__ == "__main__":
    main()

# 1}}}
