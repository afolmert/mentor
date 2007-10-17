#!/bin/env python
# -*- coding: utf-8 -*-    {{{1 Intro
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
"""
This is the main file for probe tool.
Probe is a tool for incremental reading. It extracts useful fragments of information
from text files, basing on simple markup language.
It is best used in conjunction with repetition learning flash-card programs
like Mentor or SuperMemo.
"""
# 1}}}


# {{{1 interface
__version__ = "0.0.1"

from misc import istuple, matches, log, enable_logging, find_regroups, \
    Enumeration, error
from StringIO import StringIO
import re
import sys
import os

# corpus specific settings
# using this option will make ignore often used words in set class
# TODO move them to user settings file
LANG_CORPUS_USED = 1
LANG_CORPUS_DB = 'd:/Projects/Mentor/Sources/draft/tools/freq/corpus_en.db'
LANG_CORPUS_IGNORE_LVL = 2


# 1}}}


# {{{1 AST classes
# These classes form the abstract syntax tree

### {{{2 ASTOptions
class ASTOptions(object):

    # possible options
    String, Enumeration, Integer, Boolean = range(4)

    # only possible options
    """This class will restrict options to a given set."""
    def __init__(self):
        self.options = {}

    def __str__(self):
        # print only keys which are set
        # if not options is set, then return empty string
        print_options = {}
        for key in self.options.keys():
            if self.options[key] is not None:
                print_options[key] = self.options[key]
        if len(print_options) > 0:
            return ' opt=' + str(print_options)
        else:
            return ''

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
### 2}}} ASTOptions

### {{{2 ASTObject
class ASTObject(object):
    """The root of all AST objects."""

    def __init__(self, parent=None, name="", content=""):
        self.parent = parent
        self.name = name
        self.content = content
        self.options = ASTOptions()
        self.children = []
        self.init_options()


    def calculate_hierarchy_level(self):
        """Calculate it's level in parent-children hierarchy so that I know where to print myself."""
        level = 0
        parent = self.parent
        while parent is not None:
            parent = parent.parent
            level += 1
        return level


    def get_print_indent(self):
        return ' ' * 2 * self.calculate_hierarchy_level()

    def get_print_name(self):
        return self.__class__.__name__.upper().replace('AST', '')


    def add_child(self, child):
        """Appends child to parse object children."""
        assert issubclass(child.__class__, ASTObject)
        child.parent = self
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
        self.options.add_option('init', ASTOptions.String, default='OK')
        self.options.add_option('sample', ASTOptions.Enumeration, values=['yes', 'no'])

    def __str__(self):
        indent = self.get_print_indent()
        name = self.get_print_name()
        # use str_* to get rid of annoying space at the end
        str_content = str(self.content).strip()
        str_options = str(self.options).strip()
        if str_options != "" or str_content != "":
            result = indent + "[%s %s%s]\n " % (name, str(self.content), str(self.options))
        else:
            result = indent + "[%s]\n " % name
        # add all children to result as well
        for c in self.children:
            result += str(c)
        return result
### 2}}} ASTObject

### {{{2 ASTWord
class ASTWord(ASTObject):
    """This is a simple object consisting of text."""

    # possibility to set a marker
    def __init__(self, parent=None, content='', marker=''):
        ASTObject.__init__(self, parent, content)
        self.content = content
        self.set_option('marker', marker)


    def init_options(self):
        # restrict marker to _ and ^
        self.options.clear()
        self.options.add_option('marker', ASTOptions.Enumeration, values=('^', '_'))
### 2}}} ASTWord

### {{{2 ASTBlock
class ASTBlock(ASTObject):
    """ASTBlock is a block of content. It usually consists of ASTWord objects."""

    def init_options(self):
        self.options.clear()
        self.options.add_option('ignored', ASTOptions.Boolean)
### 2}}} ASTBlock

### {{{2 ASTHint
class ASTHint(ASTObject):
    """ASTHint is hint added to other blocks or better understanding."""
    pass
### 2}}} ASTHint

### {{{2 ASTQuestionHint
class ASTQuestionHint(ASTHint):
    """ASTHint which is generated for question."""
    pass
### 2}}} ASTQuestionHint

### {{{2 ASTAnswerHint
class ASTAnswerHint(ASTHint):
    """ASTHint which is generated for answer."""
    pass
### 2}}} ASTAnswerHint

### {{{2 ASTCommand

class ASTCommand(ASTObject):
    """Generic AST command object."""

    def __init__(self, parent=None, name='', content=''):
        ASTObject.__init__(self, parent, name, content)
        self.command = None


class ASTTitle(ASTCommand):
    def init_options(self):
        self.options.clear()
        self.options.add_option('big')
        self.options.add_option('a12pt')
        self.options.add_option('title')

class ASTSection(ASTCommand):
    def init_options(self):
        self.options.clear()
        self.options.add_option('sec2')

class ASTSubsection(ASTCommand):
    def init_options(self):
        self.options.clear()
        self.options.add_option('sec2')

class ASTCloze(ASTCommand):
    def init_options(self):
        self.options.clear()
        self.options.add_option('simple')
        self.options.add_option('area')
        self.options.add_option('hint')

class ASTSet(ASTCommand):
    def init_options(self):
        self.options.clear()
        self.options.add_option('simple')
        self.options.add_option('area')
        self.options.add_option('hint')


class ASTTabbed(ASTCommand):
    pass


class ASTVerbatim(ASTCommand):
    pass


class ASTCode(ASTVerbatim):
    pass


class ASTPythonCode(ASTVerbatim):
    pass


### 2}}}


# 1}}}


# {{{1 Output classes
# These are output classes which generate items for Mentor and SuperMemo

# items is a list of tuples question - answer

class OutputItem(object):
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



class OutputItems(object):
    """This is a basic of collection of items which are question and answers."""
    # todo provide iterator container for these
    def __init__(self):
        self.contents = []

    def add_item(self, question, answer):
        item = OutputItem(question, answer)
        self.contents.append(item)

    def debug_items(self):
        print "OutputItems of length %d" % len(self.contents)
        for it in self.contents:
            print str(it)

    def export_to_file(self, fname):
        f = open(fname, "rt")
        for it in self.contents:
            f.write(str(it))
            f.write("\n")
        f.close()


# 1}}}


# {{{1 Parser classes
# These classes form the parse routines family
# They are more like function object
# with one significant function --> parse which task is to transform
# text to a tree of AST objects
#
#
# TODO this will be more elaborate to enable dynamically creating parse classes
# will be a function , register parse command - or not a function
# i will just put this file in plugins and it will read it's name and change it to command class
# will have to provide function for parse_content returning list of child object
ParseCommands = Enumeration("ParseCommands", ["title", "section", "cloze", "set", "subsection", "tabbed",
                                             "subsubsection", "verbatim", "code", "pythoncode"])
# main regexp used to search for parsed object
ParseRegexp = re.compile("\\\\(title|section|cloze|set|tabbed|subsection|verbatim|code|pythoncode)(\[[^]]*\])?({[^}]*})?", re.M)

### {{{2 ParseObject
# The root of all parse classes

class ParseObject(object):

    def parse(self, text=''):
        """Returns ast object which is the result of the parsing procedure"""
        return self.init_ast_object()

    def init_ast_object(self):
        return ASTObject()

### 2}}}

### {{{2 ParseCommand


class ParseCommand(ParseObject):

    def parse(self, text=''):
        """Parse procedure for commands."""
        ast_obj = self.init_ast_object()

        match = re.match(ParseRegexp, text, re.M)
        if match:
            self.parse_command(ast_obj, match.groups()[0])
            self.parse_options(ast_obj, match.groups()[1])
            self.parse_content(ast_obj, match.groups()[2])
            return ast_obj
        else:
            error("No match found in parsing command for text = " + text)

    def init_ast_object(self):
        """This is to be overriden to return the object to be returned."""
        return ASTCommand()

    def parse_command(self, ast_obj, command):
        """Returns command from ParseCommands enumeration type."""
        log('parse_command for command = $command')
        ast_obj.command = ParseCommands.lookup[command]
        # ! enumaration not working !!!!
        # right now it does not do anything
        # TODO command should be enumerations which shall be returned in here

    def parse_content(self, ast_obj, content):
        """Returns content."""
        if len(content) > 2:
            ast_obj.content = content[1:-1]
        else:
            ast_obj.content = None

    def parse_options(self, ast_obj, options):
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
                    ast_obj.set_option(name, value)

### 2}}} ParseCommand

### {{{2 Parse other custom command classes
class ParseTitle(ParseCommand):
    """This is parser for the \\title command."""
    def init_ast_object(self):
        return ASTTitle()

class ParseSection(ParseCommand):
    """This is parser for the \\section command."""
    def init_ast_object(self):
        return ASTSection()


class ParseSubsection(ParseCommand):
    """This is a parser for the \\subsection command."""
    def init_ast_object(self):
        return ASTSubsection()
### 2}}} Parse other custom command classes

### {{{2 ParseClassCommand

class ParseClassCommand(ParseCommand):
    """This is generic class for class commands which process text."""

    def get_block_split_regex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split content into blocks.
        Function parse_content uses this to parse content."""
        return '[\.!?]+'

    def get_word_split_regex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split words in blocks.
        Function parse_content uses this to parse content."""
        return '[ \t\n]+'

    def get_word_markers(self):
        """Virtual function to be overriden in subclasses.
        This returns a set (string) of markers which may be used on the word.
        """
        return '^_'

    def parse_content(self, ast_obj, content):
        """This will parse content and result a list of words with info on marked, unmarked."""
        log("parsing content: $content")
        # first split text into blocks
        # and then into words
        # using regex as defined in functions get_block_split_regex and
        # get_word_split_regex
        # It also uses get_word_markers to check out what word markers are
        # possible
        if len(content) > 2:
            content = content[1:-1] # strip the { } braces
            blocks = re.split(self.get_block_split_regex(), content)#{{{
            for b in blocks:
                ast_block = ASTBlock(self)

                words = re.split(self.get_word_split_regex(), b)
                for w in words:
                    # check for special marking in words
                    m = None
                    for marker in self.get_word_markers():
                        if w.find(marker) >= 0:
                            if w[0] == marker:
                                w = w[1:]
                            w = w.replace(marker, ' ')
                            m = marker
                    # add word and marker , only if not empty
                    if w.strip() != "":
                        ast_block.add_child(ASTWord(ast_block, w.strip(), m))

                # add block, only if not empty
                if len(ast_block.children) > 0:
                    ast_obj.add_child(ast_block)

#}}}
        log("parsing content end. ")



class ParseCloze(ParseClassCommand):
    """This is parser for the \\cloze command."""

    def init_ast_object(self):
        return ASTCloze()


class ParseSet(ParseClassCommand):
    """This is parser for the \\set class command."""
    def init_ast_object(self):
        return ASTSet()


class ParseTabbed(ParseClassCommand):
    """This is parser the the \\tabbed class command."""

    def init_ast_object(self):
        return ASTSet()

    def get_block_split_regex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split content into blocks.
        Function parse_content uses this to parse content."""
        return '[\n]+'

    def get_word_split_regex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split words in blocks.
        Function parse_content uses this to parse content."""
        return '[\t,]+'
        # but it should format question in another way
        # q
        # a should be below



class ParseVerbatim(ParseClassCommand):
    """This is verbatim code parse command."""
    def init_ast_object(self):
        return ASTVerbatim()

    def get_block_split_regex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split content into blocks.
        Function parse_content uses this to parse content."""
        return ''

    def get_word_split_regex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split words in blocks.
        Function parse_content uses this to parse content."""
        return ' \b'


class ParseCode(ParseVerbatim):
    """This is customized code parse command."""
    def init_ast_object(self):
        return ASTCode()


class ParsePythonCode(ParseCode):
    """This is a customized code importer working on Python code."""
    def init_ast_object(self):
        return ASTPythonCode()


class ParseSentence(ParseCommand):
    """This is a customized importer working on sentences."""
    pass


### 2}}} Parse class command

### {{{2 ParseFile
# whole file parsing
class ParseFile(ParseObject):
    """This class is for parsing the whole file.
    It will read whole files and act according to the probe syntax
    given in the file.
    It will initiate specific import classes and keep track of the
    options.
    TODO currently it uses a set of regexp to find the desired
    command (similarly to how highlighting works now).
    It does not use a full tokenizer yet.
    """

    def parse(self, text=''):

        # preprocess the file
        # remove the comments
        text = re.sub("(?m)(^|[^\\\\])(%.*$)", "", text)
        subtext = ''

        # initialize search#{{{
        root = self.init_ast_object()
        pos = 0

        match = -1
        while match and pos < len(text):
            match = ParseRegexp.search(text, pos)
            if match:
                # if match is after our current position
                # then parse in-between text with default parse class
                if match.start() > pos:
                    subtext = text[pos:match.start()]
                    if re.sub('\s', '', subtext) != '':
                        log('Found non-marked text: $subtext' )
                        parse_obj = ParseCloze()
                        ast_obj = parse_obj.parse(r'\cloze[]{' + subtext + r'}')
                        root.add_child(ast_obj)
                # parse what's in match with
                # corresponding class
                command = match.groups()[0]
                if command == 'title':
                    parse_obj = ParseTitle()
                elif command == 'section':
                    parse_obj = ParseSection()
                elif command == 'subsection':
                    parse_obj = ParseSubsection()
                elif command == 'subsubsection':
                    parse_obj = ParseCloze()
                elif command == 'cloze':
                    parse_obj = ParseCloze()
                elif command == 'set':
                    parse_obj = ParseSet()
                elif command == 'tabbed':
                    parse_obj = ParseTabbed()
                elif command == 'verbatim':
                    parse_obj = ParseVerbatim()
                elif command == 'code':
                    parse_obj = ParseCode()
                elif command == 'pythoncode':
                    parse_obj = ParsePythonCode()
                else:
                    raise "Unknown command '%s' encountered." % command

                subtext = text[match.start():match.end()]
                ast_obj = parse_obj.parse(subtext)
                root.add_child(ast_obj)
                # pos now points after last match
                pos = match.end() + 1

        # surround the last block with default command
        if pos < len(text):
            subtext = text[pos:]
            if re.sub('\s', '', subtext):
                log('Found non-marked text: $subtext' )
                parse_obj = ParseCloze()
                ast_obj = parse_obj.parse(r'\cloze[]{' + subtext + r'}')
                root.add_child(ast_obj)
#}}}
        return root


# 2}}}

# 1}}}


# {{{1 Exporter classes
# These classes export items basing on output classes


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
        # used for lang corpus db
        # in ignored words for set class
        self.corpus_db = None
        self.corpus_db_cache = {}

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


    def build_prefix(self, title, section, subsection, subsubsection):
        """Returns prefix basing on section settings."""
        result = []
        if title is not None and title.strip() != "":
            result.append(title + ": ")
        if section is not None and section.strip() != "":
            result.append(section + ": ")
        if subsection is not None and subsection.strip() != "":
            result.append(subsection + ": ")
        if subsubsection is not None and subsubsection.strip() != "":
            result.append(subsubsection + ": ")
        return "".join(result)

    def is_word_ignored(self, word):
        """Returns true if corpus is used and word is ignored at current level."""
        if LANG_CORPUS_USED: #{{{2
            word = word.strip().lower()
            if self.corpus_db_cache.has_key(word):
                return self.corpus_db_cache[word]
            else:
                import sqlite3
                if self.corpus_db is None:
                    self.corpus_db = sqlite3.connect(LANG_CORPUS_DB)
                # initially set to not-ignored
                self.corpus_db_cache[word] = False
                cursor = self.corpus_db.cursor()
                # if is found under current ignore level then is set to True
                for row in cursor.execute('SELECT WORD FROM TFREQ WHERE POSITION_LVL <= ?', (LANG_CORPUS_IGNORE_LVL,)):
                    self.corpus_db_cache[row[0]] = True
                cursor.close()
                return self.corpus_db_cache[word] #2}}}
        else:
            return False


    def process(self, input, output=None):
        """Processes input file and export output file.
        Utilizes input classes like Parser and output like Exporter
        Uses OutputItems objects to build OutputItems
        """

        # parse tree
        finput = open(input, "rt")
        fcontent = finput.read()
        finput.close()
        parser = ParseFile()
        ast_tree = parser.parse(fcontent)

        # {{{2
        # process parse tree to create OutputItems structure
        # is this step necessary ??

        # items
        # initialize variables
        title         = os.path.basename(os.path.splitext(input)[0])
        section       = ""
        subsection    = ""
        subsubsection = ""
        prefix        = "" # prefix used
        items         = OutputItems()

        print str(ast_tree)

        for obj in ast_tree.children:
            prefix = self.build_prefix(title, section, subsection, subsubsection)
            if obj.command == ParseCommands.title:
                title = obj.content
            elif obj.command ==  ParseCommands.section:
                section = obj.content
            elif obj.command == ParseCommands.subsection:
                subsection = obj.content
            elif obj.command == ParseCommands.subsubsection:
                subsubsection = obj.content
            elif obj.command in (ParseCommands.set, ParseCommands.tabbed):
                for block in obj.children:
                    words = []
                    question_words = []
                    # for each word prepare a special item
                    # except for marked items
                    for i in range(0, len(block.children)):
                        word = block.children[i]
                        words.append(word.content)
                        if word.get_option('marker') != '^' \
                            and not self.is_word_ignored(word.content): # and not is in ignored words
                            question_words.append(i)

                    for i in question_words:
                        question = self.build_question(words, i)
                        answer = words[i]

                        if not prefix.endswith(": "):
                            prefix = prefix + ": "
                        items.add_item(prefix + question, answer)

            elif obj.command == ParseCommands.cloze:
                for block in obj.children:
                    words = []
                    question_words = []
                    # this will be in contrast to set
                    # marked items will be included only
                    for i in range(len(block.children)):
                        words.append(block.children[i].content)
                        if block.children[i].get_option('marker') == '_':
                            question_words.append(i)

                    for i in question_words:
                        question = self.build_question(words, i)
                        answer = words[i]

                        if not prefix.endswith(": "):
                            prefix = prefix + ": "
                        items.add_item(prefix + question, answer)#2}}}

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


