#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
"""
This is the main file for probe tool.
Probe is a tool for incremental reading. It extracts useful fragments of information
from text files, basing on simple markup language.
It is best used in conjunction with repetition learning flash-card programs
like Mentor or SuperMemo.
"""



from utils import log, info, enable_logging, Enumeration, error, ensure_endswith
from config import config
from StringIO import StringIO
import re
import sys
import os
import release


__version__ = release.version

# special functions
EscapeChars = [(r'\|', '#&prbbar;'),
               (r'\\', '#&prbbsp;'),
               (r'\/', '#&prbslash;'),
               (r'\{', '#&prbbrcleft;'),
               (r'\}', '#&prbbrcright;'),
               (r'\?', '#&prbquest;'),
               (r'\!', '#&prbexclam;')]
EscapePattern = r'#&prbbar;|#&prbbsp;|#&prbslash;|#&prbbrcleft;|#&prbbrcright;|#&prbquest;|#&prbexclam;'




def escapeSpecialChars(text):
    """Escapes special chars with custom codes.
    This prepares text for processing.
    """
    # TODO This is very primite escaping and very time consuming because I read the
    # text many times
    # I should escape the text as I read it online in a tokenizer - whenever I
    # encounter \ backslash, I should check the next char and return normal char
    # instead of control char
    for sequence, escape in EscapeChars:
        text = text.replace(sequence, escape)
    return text


def unescapeSpecialChars(text):
    """Unescapes special chars with custom codes.
    This fixes text after processing.
    """
    # see escapeSpecialChars on comment how to do it the right way
    # currently, this is symmetric to escapeSpecialChars
    for sequence, escape in EscapeChars:
    # obviously, I have to omit the backslash in output text
        text = text.replace(escape, sequence[1:])
    return text




# handling of options :
# TODO this must be handled differently !!!
# options may be parse specific and ast specific
# the default parse option right now sets / passes the options to ast object



# AST classes {{{
# These classes form the abstract syntax tree

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

    def addOption(self, name, type=None, default=None, values=None):
        # possible types String, Number, Enumeration
        # exlucding options, should exist or not
        # see opt parse syntax and do something like this
        self.options[name] = default

    def hasOption(self, name):
        return self.options.has_key(name)

    def setOption(self, name, value):
        """This will check the type and value and existance."""
        assert self.options.has_key(name), "Option not available: " + name
        if value == "":
            value = True
        self.options[name] = value


    def getOption(self, name):
        """This will be overriden in parse object to return option as attribute"""
        assert self.options.has_key(name), "Option not available: " + name
        return self.options[name]


class ASTObject(object):
    """The root of all AST objects."""

    def __init__(self, parent=None, name="", content=""):
        self.parent = parent
        self.name = name
        self.content = content
        self.options = ASTOptions()
        self.children = []
        self.initOptions()


    def calculateHierarchyLevel(self):
        """Calculate it's level in parent-children hierarchy so that I know where to print myself."""
        level = 0
        parent = self.parent
        while parent is not None:
            parent = parent.parent
            level += 1
        return level


    def getPrintIndent(self):
        return ' ' * 2 * self.calculateHierarchyLevel()

    def getPrintName(self):
        return self.__class__.__name__.upper().replace('AST', '')


    def addChild(self, child):
        """Appends child to parse object children."""
        assert issubclass(child.__class__, ASTObject)
        child.parent = self
        self.children.append(child)

    def setOption(self, name, value):
        self.options.setOption(name, value)

    def getOption(self, name):
        return self.options.getOption(name)

    def initOptions(self):
        # here might register possible options and their types, and default values
        # and required, not required options
        # should just exist or should have a value etc.
        # declarative way of setting possible option values
        # self.addOption
        self.options.clear()
        self.options.addOption('init', ASTOptions.String, default='OK')
        self.options.addOption('sample', ASTOptions.Enumeration, values=['yes', 'no'])

    def __str__(self):
        indent = self.getPrintIndent()
        name = self.getPrintName()
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


class ASTWord(ASTObject):
    """This is a simple object consisting of text."""

    def __init__(self, parent=None, content=''):
        ASTObject.__init__(self, parent, content)
        self.content = content


    def initOptions(self):
        self.options.clear()
        # should the word be included in questioning
        self.options.addOption('marked', ASTOptions.Boolean, default=False)
        # should the word be ignored from questioning
        self.options.addOption('ignored', ASTOptions.Boolean, default=False)
        # question and answer hint connected with the word
        self.options.addOption('question_hint', ASTOptions.String, default='')
        self.options.addOption('answer_hint', ASTOptions.String, default='')


class ASTSeparatorWord(ASTWord):
    """This is a separator class used in verbatim mode."""
    def __init__(self, parent=None, content=''):
        ASTObject.__init__(self, parent, content)
        self.content = content

class ASTIdentWord(ASTWord):
    """This is a identifier word class used in verbatim mode."""
    def __init__(self, parent=None, content=''):
        ASTObject.__init__(self, parent, content)
        self.content = content

class ASTPunctationWord(ASTWord):
    """This is a punctation word class used in verbatim mode."""
    def __init__(self, parent=None, content=''):
        ASTObject.__init__(self, parent, content)
        self.content = content



class ASTBlock(ASTObject):
    """ASTBlock is a block of content. It usually consists of ASTWord objects."""

    def initOptions(self):
        self.options.clear()
        self.options.addOption('ignored', ASTOptions.Boolean)


class ASTHint(ASTObject):
    """ASTHint is hint added to other blocks or better understanding."""
    pass


class ASTQuestionHint(ASTHint):
    """ASTHint which is generated for question."""
    pass



class ASTAnswerHint(ASTHint):
    """ASTHint which is generated for answer."""
    pass


class ASTCommand(ASTObject):
    """Generic AST command object."""

    def __init__(self, parent=None, name='', content=''):
        ASTObject.__init__(self, parent, name, content)
        self.command = None

    def initOptions(self):
        self.options.addOption('ask', ASTOptions.Enumeration, values=('all', 'marked', 'corpus'))




class ASTTitle(ASTCommand):
    """AST object for titles."""
    def initOptions(self):
        self.options.clear()
        self.options.addOption('big')
        self.options.addOption('a12pt')
        self.options.addOption('title')


class ASTSection(ASTCommand):
    def initOptions(self):
        self.options.clear()
        self.options.addOption('sec2')


class ASTSubsection(ASTCommand):
    def initOptions(self):
        self.options.clear()
        self.options.addOption('sec2')


class ASTSubsubsection(ASTCommand):
    def initOptions(self):
        self.options.clear()
        self.options.addOption('sec2')


class ASTClassCommand(ASTCommand):
    pass


class ASTSentence(ASTClassCommand):
    pass


class ASTDefinition(ASTClassCommand):
    pass


class ASTParagraph(ASTClassCommand):
    pass


class ASTTabbed(ASTClassCommand):
    pass


class ASTVerbatim(ASTClassCommand):
    pass


class ASTCode(ASTVerbatim):
    pass


class ASTPythonCode(ASTVerbatim):
    pass

# }}} ASTClasses
#


#  Output classes {{{
# These are output classes which generate items for Mentor and SuperMemo
# items is a list of tuples question - answer

class OutputItem(object):
    """This is basic item for storing questions and answers."""
    def __init__(self, prefix='', question='', answer='', question_hint='', answer_hint=''):
        self.prefix        = prefix
        self.question      = question
        self.answer        = answer
        self.question_hint = question_hint
        self.answer_hint   = answer_hint

    def getPrefix(self):
        return self.prefix

    def setPrefix(self, prefix):
        self.prefix = prefix

    def getQuestion(self):
        return self.question

    def setQuestion(self, question):
        self.question = question

    def getQuestionHint(self):
        return self.question_hint

    def setQuestionHint(self, question_hint):
        self.question_hint = question_hint

    def getAnswer(self):
        return self.answer

    def setAnswer(self, answer):
        self.answer = answer

    def getAnswerHint(self):
        return self.answer_hint

    def setAnswerHint(self, answer_hint):
        self.answer_hint = answer_hint

    def __str__(self):
        return "PREFIX: [%s] QUESTION: [%s] ANSWER:[%s]" % (self.prefix, self.question, self.answer)



class OutputItems(object):
    """This is a basic of collection of items which are question and answers."""
    # todo provide iterator container for these
    def __init__(self):
        self.items = []

    def addItem(self, item):
        self.items.append(item)

    def debugItems(self):
        print "OutputItems of length %d" % len(self.items)
        for it in self.items:
            print str(it)

# Output classes }}}



# Parser classes {{{
# These classes form the parse routines family
# They are more like function object
# with one significant function --> parse which task is to transform
# text to a tree of AST objects
#
#
# TODO this will be more elaborate to enable dynamically creating parse classes
# will be a function , register parse command - or not a function
# i will just put this file in plugins and it will read it's name and change it to command class
# will have to provide function for parseContent returning list of child object
ParseCommands = Enumeration('ParseCommands', ['title', 'section', 'subsection', 'tabbed', 'sentence', 'paragraph', 'definition'
                                             'subsubsection', 'verbatim', 'code', 'pythoncode'])
# main regexp used to search for parsed object
ParseRegexp = re.compile("\\\\(title|section|tabbed|sentence|paragraph|definition|subsection|verbatim|code|pythoncode)(\[[^]]*\])?({[^}]*})?", re.M)


class ParseObject(object):

    def parse(self, text=''):
        """Returns ast object which is the result of the parsing procedure"""
        return self.initAstObject()

    def initAstObject(self):
        return ASTObject()



class ParseCommand(ParseObject):

    def parse(self, text=''):
        """Parse procedure for commands."""
        ast_obj = self.initAstObject()

        match = re.match(ParseRegexp, text, re.M)
        if match:
            self.parseCommand(ast_obj, match.groups()[0])
            self.parseOptions(ast_obj, match.groups()[1])
            self.parseContent(ast_obj, match.groups()[2])
            return ast_obj
        else:
            error("No match found in parsing command for text = " + text)

    def initAstObject(self):
        """This is to be overriden to return the object to be returned."""
        return ASTCommand()

    def parseCommand(self, ast_obj, command):
        """Returns command from ParseCommands enumeration type."""
        log('parseCommand for command = $command')
        ast_obj.command = ParseCommands.lookup[command]
        # ! enumaration not working !!!!
        # right now it does not do anything
        # TODO command should be enumerations which shall be returned in here

    def parseContent(self, ast_obj, content):
        """Returns content."""
        if len(content) > 2:
            ast_obj.content = unescapeSpecialChars(content[1:-1])
        else:
            ast_obj.content = None

    def parseOptions(self, ast_obj, options):
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
                    ast_obj.setOption(name, value)


class ParseTitle(ParseCommand):
    """This is parser for the \\title command."""
    def initAstObject(self):
        return ASTTitle()



class ParseSection(ParseCommand):
    """This is parser for the \\section command."""
    def initAstObject(self):
        return ASTSection()



class ParseSubsection(ParseCommand):
    """This is a parser for the \\subsection command."""
    def initAstObject(self):
        return ASTSubsection()


class ParseClassCommand(ParseCommand):
    """This is generic class for class commands which process text."""

    def getBlockSplitRegex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split content into blocks.
        Function parseContent uses this to parse content."""
        return '[\.]+|#&prbquest;|#&prbexclam;'

    def getWordSplitRegex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split words in blocks.
        Function parseContent uses this to parse content."""
        return '[ \t\n]+'


    def parseMarkedContent(self, ast_block, content):
        """Parses a group of words | | which should be included in repetition.
        This group is treated as single entity.
        Optionally it may contain question and answer hints.
        """
        log('parseMarkedContent for block $content')
        # strip off | | chars
        if len(content) > 1:
            content = content[1:-1]
        # include block may be in format:
        # |question hint? answer hint! text|
        regexp = r'([^\?\!]*\?)?([^\?\!]*\!)?(.*)'
        match = re.match(regexp, content)
        log('parseMarkedContent match groups $match.groups()')
        if match:
            # add word with content
            ast_word = ASTWord(ast_block, unescapeSpecialChars(match.groups()[2]))
            # add hints if they exist
            # question hint (?)
            if match.groups()[0]:
                hint = match.groups()[0].strip()
                hint = unescapeSpecialChars(hint)[:-1].strip() # remove the question mark ?
                ast_word.setOption('question_hint', hint)
            if match.groups()[1]:
                hint = match.groups()[1].strip()
                hint = unescapeSpecialChars(hint)[:-1].strip() # remove the exclamation !
                ast_word.setOption('answer_hint', hint)
        else:
            raise "Invalid include block - not matched! %s " % content
        ast_word.setOption('marked', True)
        ast_block.addChild(ast_word)


    def parseIgnoredContent(self, ast_block, content):
        """Parses group of words / /  which should be excluded from repetition.
        The group is treated as a single entity.
        """
        log('parseIgnoredContent $content')
        # strip ending and beginning / /
        if len(content) > 1:
            content = content[1:-1]
        ast_word = ASTWord(ast_block, unescapeSpecialChars(content))
        ast_word.setOption('ignored', True)
        ast_block.addChild(ast_word)



    def parseContent(self, ast_obj, content):
        """Parses content to ast syntax tree."""
        log('parseContent for content $content')
        if len(content) > 2:
            content = content[1:-1]

            # split to blocks using block seperators
            blocks = re.split(self.getBlockSplitRegex(), content)
            # for each block :
            # split content looking for content groups
            for block in blocks:
                log('parseContent processing block: $block')
                ast_block = ASTBlock()
                # go through text finding
                # find |   |    /    /    and unmarked blocks
                # and each block process seperately
                # unmarked blocks are between | | and / / blocks
                marked_pattern = r'\|[^\|]*\|'
                ignored_pattern = r'/[^/]*/'
                regexp = re.compile('(%s)|(%s)' % (marked_pattern, ignored_pattern), re.M)
                pos = 0
                match = -1
                while pos < len(block) and match:
                    match = regexp.search(block, pos)
                    if match:
                        log('parseContent matches: $match.groups()')
                        # process unmarked block between
                        if match.start() > pos:
                            self.parseUnmarkedContent(ast_block, block[pos:match.start()])
                        # process include block | |
                        if match.groups()[0]:
                            self.parseMarkedContent(ast_block, block[match.start():match.end()])
                        # process ignored block / /
                        elif match.groups()[1]:
                            self.parseIgnoredContent(ast_block, block[match.start():match.end()])
                        else:
                            raise "Unknown group!"
                        pos = match.end()

                if pos < len(block):
                    self.parseUnmarkedContent(ast_block, block[pos:])

                # add block to parent
                ast_obj.addChild(ast_block)


    def parseUnmarkedContent(self, ast_block, content):
        """This will parse content and result a list of words with info on marked, unmarked."""
        log("parsing unmarked content: $content")
        # first split text into blocks
        # and then into words
        # using regex as defined in functions getBlockSplitRegex and
        words = re.split(self.getWordSplitRegex(), content)
        for w in words:
            if w.strip() != "":
                ast_word = ASTWord(ast_block, unescapeSpecialChars(w.strip()))
                ast_block.addChild(ast_word)




class ParseSentence(ParseClassCommand):
    """This is a customized importer working on sentences.
    By sentence I mean a set words characters, seperated by dot .
    """
    def initAstObject(self):
        return ASTSentence()

    def getBlockSplitRegex(self):
        return '[\.]+|#&prbquest;|#&prbexclam;'


class ParseParagraph(ParseClassCommand):
    """This is a customized importer working on paragraphs.
    By paragraph I mean a block of text seperated by double \n chars.
    """
    def initAstObject(self):
        return ASTParagraph()


class ParseDefinition(ParseClassCommand):
    """This is a customized parsers working on definitions
    Definitions is defined as:
    question?
    answer
    The while answer is taken as question.
    """
    def initAstObject(self):
        return ASTDefinition()



class ParseTabbed(ParseClassCommand):
    """This is parser the the \\tabbed class command."""

    def initAstObject(self):
        return ASTSet()

    def getBlockSplitRegex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split content into blocks.
        Function parseContent uses this to parse content."""
        return '[\n]+'

    def getWordSplitRegex(self):
        """Virtual function to be overriden in subclasses.
        This regex will be used to split words in blocks.
        Function parseContent uses this to parse content."""
        return '[\t,]+'
        # but it should format question in another way
        # q
        # a should be below



class ParseVerbatim(ParseCommand):
    # it does not inherit from ParseClassCommand because it parses contents in
    # it's own way

    """This is verbatim code parse command."""
    def initAstObject(self):
        return ASTVerbatim()


    def parseUnmarkedContent(self, ast_block, content):
        """Parses block which is not in any group || or //
        All text is split to ident , punct , whitespace and entity patterns
        """
        # I can unescape them now, because this parsing does not need special markup
        log('parse_unmarked_block $content ' )
        content = unescapeSpecialChars(content)
        ident_pattern = r'[\w]+'
        punct_pattern = r'[^\w\s]+'
        whitespace_pattern = r'\s+'
        regexp = re.compile(r'(%s)|(%s)|(%s)' % \
                    (ident_pattern, punct_pattern, whitespace_pattern), re.M)
        # TODO how to ensure EscapePattern has higher priority than all other patterns
        # is it enough that it's on first position?
        # maybe exclude the following punctation in the next patterns ??!
        matches = re.findall(regexp, content, re.M)
        for match in matches:
            if match[0]:
                ast_word = ASTIdentWord(ast_block, match[0])
            elif match[1]:
                ast_word = ASTPunctationWord(ast_block, match[1])
            elif match[2]:
                ast_word = ASTSeparatorWord(ast_block, match[2])
            else:
                raise "Match not found for content: %s" % content

            log('adding word $str(ast_word)')
            ast_block.addChild(ast_word)



class ParseCode(ParseVerbatim):
    """This is general class for parsing code.
    It uses knowledge about given programming language to include/exclude specific words from questioning.
    It is used by many other class as parent class.
    """
    def initAstObject(self):
        return ASTCode()


class ParsePythonCode(ParseCode):
    """This is a customized code importer working on Python code."""
    def initAstObject(self):
        return ASTPythonCode()


class ParsePascalSignatureCode(ParseCode):
    """Class for parsing Pascal language signature code."""
    pass


class ParseCSignatureCode(ParseCode):
    """Class for parsing C language signature code."""
    pass




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



    def removeComments(self, text=''):
        """Preprocesses given text, removes comments """
        # remove lines beginning with $ or after not-escaped $
        return re.sub("(?m)(^|[^\\\\])(%.*$)", "", text)


    def parse(self, text=''):

        # preprocess the file
        # remove the comments
        text = self.removeComments(text)
        text = escapeSpecialChars(text)

        # initialize search#
        root = self.initAstObject()
        pos = 0

        match = -1
        while match and pos < len(text):
            match = ParseRegexp.search(text, pos)
            if match:
                # text which is not enclosed by any class will be processed with a
                # default class
                # if match is after our current position
                # then parse in-between text with default parse class
                if match.start() > pos:
                    subtext = text[pos:match.start()]
                    if re.sub('\s', '', subtext) != '':
                        parse_obj = ParseSentence()
                        ast_obj = parse_obj.parse(r'\[]{' + subtext + r'}')
                        root.addChild(ast_obj)
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
                    parse_obj = ParseSubsubsection()
                elif command == 'tabbed':
                    parse_obj = ParseTabbed()
                elif command == 'sentence':
                    parse_obj = ParseSentence()
                elif command == 'definition':
                    parse_obj = ParseDefinition()
                elif command == 'paragraph':
                    parse_obj = ParseParagraph()
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
                root.addChild(ast_obj)
                # pos now points after last match
                pos = match.end() + 1

        # surround the last block with default command
        if pos < len(text):
            subtext = text[pos:]
            if re.sub('\s', '', subtext):
                log('Found non-marked text: $subtext' )
                parse_obj = ParseSentence()
                ast_obj = parse_obj.parse(r'\sentence[]{' + subtext + r'}')
                root.addChild(ast_obj)
#
        return root

# Parser classes }}}


#  Exporter classes {{{
# These classes export items basing on output classes


class Exporter(object):
    """This is a generic base exporter class for exporting all items.
    It can be overriden to export to supermemo or to other programs like mentor."""

    def __init__(self):
        pass

    def exportFile(fname, items):
        """This is a procedure to export files to a file by given algorithm.
        It get's customized in lower algorithms.
        """
        pass


class QAExporter(Exporter):
    def __init__(self):
        Exporter.__init__(self)

    def exportFile(self, items, output=None):
        """Exports given items to output in 'question and answer' style."""
        if output is None:
            f = sys.stdout
        else:
            f = open(output, "wt")
        # print items
        for item in items.items:
            # print question
            if item.question.count('\n') == 0:
                # if one line then just prefix item and print as item is
                f.write('q: %s %s\n' % (item.prefix, item.question))
            else:
                # if more lines then prefix to first line and each line printed with q: or a:
                f.write('q: %s\n' % item.prefix)
                lines = item.question.split('\n')
                for i in range(len(lines)):
                    line = lines[i]
                    # first and last line is skipped if empty
                    if not ((i == 0 or i == len(lines) - 1) and line.strip() == ''):
                        f.write('q: %s\n' % line)
            if item.question_hint:
                f.write('q:\n')
                f.write('q: %s?\n' % item.question_hint)

            # print answer
            if item.question.count('\n') == 0:
                f.write('a: %s\n' % item.answer)
            else:
                lines = item.answer.split('\n')
                for line in lines:
                    f.write('a: %s\n' % line)

            if item.answer_hint:
                f.write('a:\n')
                f.write('a: %s!\n' % item.answer_hint)

            f.write('\n')
        if output is not None:
            f.close()


class MentorExporter(Exporter):
    """This will be exporting to my custom Mentor program."""
    def __init__(self):
        Exporter.__init__(self)

    def exportFile(self, fname, items):
        pass
        # TODO to be implemented


# }}} Exporter classes

#  Processor classes {{{
# Here are main classes which use parser to get a parse tree of parse objects
# use it to build items
# and then use Exporter objects to export those items

class Processor(object):

    def __init__(self):
        # used for lang corpus db
        # in ignored words for set class
        self.corpus_db = None
        self.corpus_db_cache = {}


    def buildQuestion(self, words, hidenth, verbatim=False):
        """Builds question from words but constructing them in intact way.
        It is used with verbatim style questions. """
        result = []
        for i in range(len(words)):
            if i == hidenth:
                word = '[...]'
            else:
                word = words[i].content
            result.append(word if verbatim else word.strip())
        if verbatim:
            return ''.join(result)
        else:
            return ' '.join(result)


    def buildPrefix(self, title, section, subsection, subsubsection):
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


    def isWordIgnored(self, word):
        """Returns true if corpus is used and word is ignored at current level."""
        if config.LANG_CORPUS_USED:
            word = word.strip().lower()
            if self.corpus_db_cache.has_key(word):
                return self.corpus_db_cache[word]
            else:
                import sqlite3
                if self.corpus_db is None:
                    self.corpus_db = sqlite3.connect(config.LANG_CORPUS_DB)
                # initially set to not-ignored
                self.corpus_db_cache[word] = False
                cursor = self.corpus_db.cursor()
                # if is found under current ignore level then is set to True
                for row in cursor.execute('SELECT WORD FROM TFREQ WHERE POSITION_LVL <= ?', (config.LANG_CORPUS_IGNORE_LVL,)):
                    self.corpus_db_cache[row[0]] = True
                cursor.close()
                return self.corpus_db_cache[word] #
        else:
            return False


    def process(self, input, output=None):
        """Processes input file and export output file.

        Utilizes input classes like Parser and output like Exporter
        Uses OutputItems objects to build OutputItems
        """

        # parse tree
        finput = open(input, 'rt')
        fcontent = finput.read()
        finput.close()
        parser = ParseFile()
        ast_tree = parser.parse(fcontent)

        # process parse tree to create OutputItems structure
        # is this step necessary ??

        # items
        # initialize variables
        title         = os.path.basename(os.path.splitext(input)[0])
        section       = ''
        subsection    = ''
        subsubsection = ''
        prefix        = '' # prefix used
        items         = OutputItems()

        if config.DEBUG:
            print str(ast_tree)

        for obj in ast_tree.children:
            prefix = self.buildPrefix(title, section, subsection, subsubsection)
            if type(obj) is ASTTitle:
                title = obj.content
            elif type(obj) is ASTSection:
                section = obj.content
            elif type(obj) is ASTSubsection:
                subsection = obj.content
            elif type(obj) is ASTSubsubsection:
                subsubsection = obj.content
            # process each class command
            # by generating output items from its ast child items
            elif isinstance(obj, ASTClassCommand):
                for block in obj.children:
                    words = block.children
                    # which words it should ask for?
                    if obj.getOption('ask') == 'marked' or obj.get_option('ask') == '':
                        hide_words_idx = [i for i in range(len(block.children)) \
                                            if words[i].getOption('marked')]
                    else: # default option is set asking for all words
                        hide_words_idx =  [i for i in range(len(block.children)) \
                                            if not words[i].getOption('ignored') and \
                                                type(words[i]) != ASTSeparatorWord]

                    # build question (output item) for each hidden words
                    for hide_idx in hide_words_idx:
                        question = self.buildQuestion(words, hide_idx, isinstance(obj, ASTVerbatim))
                        answer = words[hide_idx].content.strip()

                        question_hint = words[hide_idx].getOption('question_hint')
                        answer_hint = words[hide_idx].getOption('answer_hint')

                        item = OutputItem(ensure_endswith(prefix, ': '), question, answer, question_hint, answer_hint)
                        items.addItem(item)


        # now export items using exporter
        exporter = QAExporter()
        exporter.exportFile(items, output=None)


        # now export items using exporter
        exporter = QAExporter()



# }}} Processor classes


#  Main program {{{

def main():
    """This is the main program."""
    from optparse import OptionParser

    # TODO I might move this to config but there is problem of mentor and probe
    # being different apps !
    parser = OptionParser(version='Mentor Probe version ' + __version__)
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=config.DEBUG,
                      help="run program in debugged mode" )
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=config.VERBOSE,
                      help="print output verbosely")
    parser.add_option("-p", "--pretend", action="store_true", dest="pretend", default=config.PRETEND,
                      help="run a a simulation only")
    parser.add_option("-t", "--test", action="store_true", dest="test", default=config.TEST,
                      help="runs a series of tests")

    opts, args = parser.parse_args(sys.argv[1:])
    # apply to config
    config.TEST    =  opts.test
    config.VERBOSE =  opts.verbose
    config.PRETEND =  opts.pretend
    config.DEBUG   =  opts.debug


    if config.TEST:
        # import path from tests
        # sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests"))
        from tests import test_utils, test_probe, test_cards, test_models
        import unittest
        # do I need it?
        suite = unittest.TestSuite([test_utils.suite(),
                                    test_probe.suite(),
                                    test_cards.suite(),
                                    test_models.suite()])
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
        sys.exit()


    if config.DEBUG:
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
