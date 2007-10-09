#!/bin/env python
#
# this script  translated smite markup language text to supermemo
# items
#
#
from misc import istuple, matches, log, enable_logging, find_regroups
from StringIO import StringIO
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
    def __init__(self, command="", options="", content=""):
        self.command = command
        self.options = options
        self.content = content
        #self.command        =  ""
        #self.options        =  []
        #self.text           =  []  # group of words or 2-words
        #self.marked_text    =  [] # indicating which are marked specially

    def __str__(self):
        return "CMD: " + str(self.command) + " OPT: " + str(self.options) + " CONT: "  + str(self.content)




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

        # find a command, then, optionally a [] block, and then, optionally a
        # {} block
        # what about maybe the regexp will be used as a start only and then it
        # will be parsed more reguralry
        # what about this { ass{}   } -> this will fail to be found
        # can a regexp make a counting progress? ?
        self.probe_regexp = re.compile("\\\\(title|section|cloze|set|subsection)(\[[^]]*\])?({[^}]*})?", re.M)

    def parse_command(self, command):
        if command == None:
            return None
        return command
        # right now it does not do anything
        # TODO command should be enumerations which shall be returned in here


    # TODO maybe put these options into general parser class
    def parse_options(self, options):
        """This will parse options embedded in begin or option statement."""
        log("parsing options $options")
        if options == None:
            return []
        options = options[1:-1]       # strip the [] brackets o
        options = options.split(",")

        result = []
        for o in options:
            name, _, value = o.partition("=")
            result.append((name, value))
        return result


    def parse_content(self, content):
        """This will parse content and result a list of words with info on marked, unmarked."""
        log("parsing content: $content")
        if content == None:
            return []
        content = content[1:-1] # strip the { } braces
        words = re.split(" +", content)
        result = []
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

            result.append((w, marker))
        return result


    def parse_file(self, fobject):
        """Returns a tree of parsed objects read from file-like object."""
        # open file , read it line by line
        # if encounters syntax item then interpret it in some way
        # specific environment parsers will be launched
        # depending on the texts given.

        command = ""
        options = ""
        content = ""

        result = [] # a list of parse objects
        fcontent = fobject.read()
        patterns = re.findall(self.probe_regexp, fcontent, re.M)

        for p in patterns:
            command = self.parse_command(p[0])
            options = self.parse_options(p[1])
            content = self.parse_content(p[2])
            log("parsed content $content")

            obj = ParseObject(command, options, content)
            result.append(obj)

        return result


### 2}}}

# 1}}}


# {{{1 Processor classes
# Here are main classes which use parser to get a parse tree of parse objects
# use it to build items
# and then use Exporter objects to export those items

class Processor(object):

    def __init__(self):
        pass

    def build_set_question(self, words, question):
        """Returns question build from the SET class words, excluding questioned item."""
        words2 = []
        for i in range(len(words)):
            if i <> question:
                words2.append(words[i][0])
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


    def process(self, input, output):
        """Processes input file and export output file.
        Utilizes input classes like Parser and output like Exporter
        Uses Items objects to build Items
        """
        finput = open(input, "rt")

        # parse tree
        parser = MainParser()
        parse_tree = parser.parse_file(finput)
        finput.close()

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

        # TODO section prefixes
        for obj in parse_tree:
            prefix = self.build_prefix(section, subsection, subsubsection)
            if obj.command == "title":#{{{
                title = obj.content
            elif obj.command == "section":
                section = obj.content[0][0]
            elif obj.command == "subsection":
                subsection = obj.content[0][0]
            elif obj.command == "subsubsection":
                subsubsection = obj.content[0][0]
            elif obj.command == "set":
                question_words = []
                # for each word prepare a special item
                # except for marked items
                for i in range(0, len(obj.content)):
                    log("checking in set obj.content[$i]: " + str(obj.content[i]))
                    if obj.content[i][1] != '^': # and not is in ignored words
                        question_words.append(i)

                for i in question_words:
                    question = self.build_set_question(obj.content, i)
                    answer = obj.content[i][0]

                    if not prefix.endswith(": "):
                        prefix = prefix + ": "
                    items.add_item(question, answer)

            elif obj.command == "cloze":
                question_words = []
                # this will be in contrast to set
                # marked items will be included only
                for i in range(len(obj.content)):
                    if obj.content[i][1] == '_':
                        question_words.append(i)

                for i in question_words:
                    question = self.build_set_question(obj.content, i)
                    answer = obj.content[i][0]

                    if not prefix.endswith(": "):
                        prefix = prefix + ": "
                    items.add_item(prefix + question, answer)#}}}


        # now export items using exporter
        exporter = SuperMemoExporter()
        exporter.export_file(output, items)





# }}}



# {{{1 Main program

def processor_demo():
    log("processor demo begin...")
    processor = Processor()
    processor.process("d:/temp/input.txt", "d:/temp/output.txt")

    log("processor demo end...")




def parser_demo():
    log("parser demo begin..")
    parser = MainParser()
    input = StringIO(
"""
 running parse on this file directly:
 for example:
 \\title[big,a12pt,title='Geez']{Title1}
 \\section{Section1}
 \\cloze[simple,area]{This is _first_question I will ask}
 \\subsection[sec2]{Section2}
 \\set[hint="Dupa"]{Here I will ^ask some more^questions}
 this run by tokenizer should return:
""")
    tree = parser.parse_file(input)
    for t in tree:
        print str(t)
    print str(tree)
    log("parser demo end")

# {{{2 Demo fill items
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


# 2}}}

def main():
    enable_logging()
    processor = Processor()
    processor.process(sys.argv[1], "d:/temp/output.txt")
    print "Written result to d:/temp/output.txt"




if __name__ == "__main__":
    main()

# 1}}}

