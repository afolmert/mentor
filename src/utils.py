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
"""General utility functions.

This is a grab-bag for all useful general-purpose functions I use in the mentor
project.
These function may be well used in another project.
"""

import exceptions
import logging
import os
import release
import sys
import time
import types
import string

__version__ = release.version



#----------------------------------------------------------
# String utils

# Here are main classes which use parser to get a parse tree of parse objects
# use it to build items
# and then use Exporter objects to export those items

def ensure_endswith(string, suffix):
    """Returns string with suffix added. Nothing is added if suffix already exists."""
    if not string.endswith(suffix):
        return string + suffix
    else:
        return string


#----------------------------------------------------------
# Enumeration type


class EnumException(exceptions.Exception):
    """Exception used in Enum."""
    pass

class Enumeration:
    """Enumeration class object Python."""
    def __init__(self, name, enumList):
        self.__doc__ = name
        lookup = { }
        reverseLookup = { }
        i = 0
        uniqueNames = [ ]
        uniqueValues = [ ]
        for x in enumList:
            if type(x) == types.TupleType:
                x, i = x
            if type(x) != types.StringType:
                raise EnumException, "enum name is not a string: " + x
            if type(i) != types.IntType:
                raise EnumException, "enum value is not an integer: " + i
            if x in uniqueNames:
                raise EnumException, "enum name is not unique: " + x
            if i in uniqueValues:
                raise EnumException, "enum value is not unique for " + x
            uniqueNames.append(x)
            uniqueValues.append(i)
            lookup[x] = i
            reverseLookup[i] = x
            i = i + 1
        self.lookup = lookup
        self.reverseLookup = reverseLookup
    def __getattr__(self, attr):
        if not self.lookup.has_key(attr):
            raise AttributeError
        return self.lookup[attr]
    def whatis(self, value):
        """Does reverse lookup on value."""
        return self.reverseLookup[value]


def test_Enumeration():
    """Test of enumeration function."""
    Volkswagen = Enumeration("Volkswagen",
                             ["JETTA",
                              "RABBIT",
                              "BEETLE",
                              ("THING", 400),
                              "PASSAT",
                              "GOLF",
                              ("CABRIO", 700),
                              "EURO_VAN",
                              "CLASSIC_BEETLE",
                              "CLASSIC_VAN"
                              ])

    Insect = Enumeration("Insect",
                         ["ANT",
                          "APHID",
                          "BEE",
                          "BEETLE",
                          "BUTTERFLY",
                          "MOTH",
                          "HOUSEFLY",
                          "WASP",
                          "CICADA",
                          "GRASSHOPPER",
                          "COCKROACH",
                          "DRAGONFLY"
                          ])

    def whatkind(value, enum):
        """Returns what kind is value."""
        return enum.__doc__ + "." + enum.whatis(value)

    class ThingWithType:
        """ThingWithType"""
        def __init__(self, type):
            self.type = type


    car = ThingWithType(Volkswagen.BEETLE)
    print whatkind(car.type, Volkswagen)
    bug = ThingWithType(Insect.BEETLE)
    print whatkind(bug.type, Insect)

    # Notice that car's and bug's attributes don't include any of the
    # enum machinery, because that machinery is all CLASS attributes and
    # not INSTANCE attributes. So you can generate thousands of cars and
    # bugs with reckless abandon, never worrying that time or memory will
    # be wasted on redundant copies of the enum stuff.

    print car.__dict__
    print bug.__dict__
    pprint.pprint(Volkswagen.__dict__)
    pprint.pprint(Insect.__dict__)



#----------------------------------------------------------
# String interpolation object
# String interpolation for Python (by Ka-Ping Yee, 14 Feb 2000).
# Credits: these classes were stolen from IPython sources

# This module lets you quickly and conveniently interpolate values into
# strings (in the flavour of Perl or Tcl, but with less extraneous
# punctuation).  You get a bit more power than in the other languages,
# because this module allows subscripting, slicing, function calls,
# attribute lookup, or arbitrary expressions.  Variables and expressions
# are evaluated in the namespace of the caller.

# The itpl() function returns the result of interpolating a string, and
# printpl() prints out an interpolated string.  Here are some examples:

#     from Itpl import printpl
#     printpl("Here is a $string.")
#     printpl("Here is a $module.member.")
#     printpl("Here is an $object.member.")
#     printpl("Here is a $functioncall(with, arguments).")
#     printpl("Here is an ${arbitrary + expression}.")
#     printpl("Here is an $array[3] member.")
#     printpl("Here is a $dictionary['member'].")

# The filter() function filters a file object so that output through it
# is interpolated.  This lets you produce the illusion that Python knows
# how to do interpolation:

#     import Itpl
#     sys.stdout = Itpl.filter()
#     f = "fancy"
#     print "Isn't this $f?"
#     print "Standard output has been replaced with a $sys.stdout object."
#     sys.stdout = Itpl.unfilter()
#     print "Okay, back $to $normal."

# Under the hood, the Itpl class represents a string that knows how to
# interpolate values.  An instance of the class parses the string once
# upon initialization; the evaluation and substitution can then be done
# each time the instance is evaluated with str(instance).  For example:

#     from Itpl import Itpl
#     s = Itpl("Here is $foo.")
#     foo = 5
#     print str(s)
#     foo = "bar"
#     print str(s)


from tokenize import tokenprog


class ItplError(ValueError):
    """Exception defined for Itpl class."""
    def __init__(self, text, pos):
        self.text = text
        self.pos = pos
    def __str__(self):
        return "unfinished expression in %s at char %d" % (
            repr(self.text), self.pos)

def match_or_fail(text, pos):
    """match_or_fail(text, pos)"""
    match = tokenprog.match(text, pos)
    if match is None:
        raise ItplError(text, pos)
    return match, match.end()

class Itpl:
    """
    Class representing a string with interpolation abilities.

    Upon creation, an instance works out what parts of the format
    string are literal and what parts need to be evaluated.  The
    evaluation and substitution happens in the namespace of the
    caller when str(instance) is called."""

    def __init__(self, format, codec='utf_8', encoding_errors='backslashreplace'):
        """The single mandatory argument to this constructor is a format
        string.

        The format string is parsed according to the following rules:

        1.  A dollar sign and a name, possibly followed by any of:
              - an open-paren, and anything up to the matching paren
              - an open-bracket, and anything up to the matching bracket
              - a period and a name
            any number of times, is evaluated as a Python expression.

        2.  A dollar sign immediately followed by an open-brace, and
            anything up to the matching close-brace, is evaluated as
            a Python expression.

        3.  Outside of the expressions described in the above two rules,
            two dollar signs in a row give you one literal dollar sign.

        Optional arguments:

        - codec('utf_8'): a string containing the name of a valid Python
        codec.

        - encoding_errors('backslashreplace'): a string with a valid error handling
        policy.  See the codecs module documentation for details.

        These are used to encode the format string if a call to str() fails on
        the expanded result."""

        if not isinstance(format, basestring):
            raise TypeError, "needs string initializer"
        self.format = format
        self.codec = codec
        self.encoding_errors = encoding_errors

        namechars = "abcdefghijklmnopqrstuvwxyz" \
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        chunks = []
        pos = 0

        while 1:
            dollar = string.find(format, "$", pos)
            if dollar < 0:
                break
            nextchar = format[dollar+1]

            if nextchar == "{":
                chunks.append((0, format[pos:dollar]))
                pos, level = dollar+2, 1
                while level:
                    match, pos = match_or_fail(format, pos)
                    tstart, tend = match.regs[3]
                    token = format[tstart:tend]
                    if token == "{":
                        level = level+1
                    elif token == "}":
                        level = level-1
                chunks.append((1, format[dollar+2:pos-1]))

            elif nextchar in namechars:
                chunks.append((0, format[pos:dollar]))
                match, pos = match_or_fail(format, dollar+1)
                while pos < len(format):
                    if format[pos] == "." and \
                        pos+1 < len(format) and format[pos+1] in namechars:
                        match, pos = match_or_fail(format, pos+1)
                    elif format[pos] in "([":
                        pos, level = pos+1, 1
                        while level:
                            match, pos = match_or_fail(format, pos)
                            tstart, tend = match.regs[3]
                            token = format[tstart:tend]
                            if token[0] in "([":
                                level = level+1
                            elif token[0] in ")]":
                                level = level-1
                    else:
                        break
                chunks.append((1, format[dollar+1:pos]))

            else:
                chunks.append((0, format[pos:dollar+1]))
                pos = dollar + 1 + (nextchar == "$")

        if pos < len(format):
            chunks.append((0, format[pos:]))
        self.chunks = chunks

    def __repr__(self):
        return "<Itpl %s >" % repr(self.format)

    def _str(self, glob, loc):
        """Evaluate to a string in the given globals/locals.

        The final output is built by calling str(), but if this fails, the
        result is encoded with the instance's codec and error handling policy,
        via a call to out.encode(self.codec, self.encoding_errors)"""
        result = []
        app = result.append
        for live, chunk in self.chunks:
            if live:
                app(str(eval(chunk, glob, loc)))
            else: app(chunk)
        out = ''.join(result)
        try:
            return str(out)
        except UnicodeError:
            return out.encode(self.codec, self.encoding_errors)

    def __str__(self):
        """Evaluate and substitute the appropriate parts of the string."""

        # We need to skip enough frames to get to the actual caller outside of
        # Itpl.
        frame = sys._getframe(1)
        while frame.f_globals.has_key("__name__") and frame.f_globals["__name__"] == __name__:
            frame = frame.f_back
        loc, glob = frame.f_locals, frame.f_globals

        return self._str(glob, loc)


class ItplNS(Itpl):
    """Class representing a string with interpolation abilities.

    This inherits from Itpl, but at creation time a namespace is provided
    where the evaluation will occur.  The interpolation becomes a bit more
    efficient, as no traceback needs to be extracte.  It also allows the
    caller to supply a different namespace for the interpolation to occur than
    its own."""

    def __init__(self, format, globals, locals=None,
                 codec='utf_8', encoding_errors='backslashreplace'):
        """ItplNS(format, globals[, locals]) -> interpolating string instance.

        This constructor, besides a format string, takes a globals dictionary
        and optionally a locals (which defaults to globals if not provided).

        For further details, see the Itpl constructor."""

        if locals is None:
            locals = globals
        self.globals = globals
        self.locals = locals
        Itpl.__init__(self, format, codec, encoding_errors)

    def __str__(self):
        """Evaluate and substitute the appropriate parts of the string."""
        return self._str(self.globals, self.locals)

    def __repr__(self):
        return "<ItplNS %s >" % repr(self.format)

# utilities for fast printing
def itpl(text):
    """Returns interpolated text."""
    return str(Itpl(text))

def printpl(text):
    """Prints interpolated text."""
    print itpl(text)

# versions with namespace
def itplns(text, globals, locals=None):
    """Returns interpolated text (namespace version)."""
    return str(ItplNS(text, globals, locals))

def printplns(text, globals, locals=None):
    """Prints interpolated text (namespace version)."""
    print itplns(text, globals, locals)

class ItplFile:
    """A file object that filters each write() through an interpolator."""
    def __init__(self, file):
        self.file = file
    def __repr__(self):
        return "<interpolated " + repr(self.file) + ">"
    def __getattr__(self, attr):
        return getattr(self.file, attr)
    def write(self, text):
        """Overriden write function."""
        self.file.write(str(Itpl(text)))


def itpl_filter(file=sys.stdout):
    """Return an ItplFile that filters writes to the given file object.

    'file = filter(file)' replaces 'file' with a filtered object that
    has a write() method.  When called with no argument, this creates
    a filter to sys.stdout."""
    return ItplFile(file)

def itpl_unfilter(ifile=None):
    """Return the original file that corresponds to the given ItplFile.

    'file = unfilter(file)' undoes the effect of 'file = filter(file)'.
    'sys.stdout = unfilter()' undoes the effect of 'sys.stdout = filter()'."""
    return ifile and ifile.file or sys.stdout.file



class NLprinter:
    """Print an arbitrarily nested list, indicating index numbers.

    An instance of this class called nlprint is available and callable as a
    function.

    nlprint(list, indent=' ', sep=': ') -> prints indenting each level by 'indent'
    and using 'sep' to separate the index from the value. """

    def __init__(self):
        self.depth = 0

    def __call__(self, lst, pos='', **kw):
        """Prints the nested list numbering levels."""
        kw.setdefault('indent', ' ')
        kw.setdefault('sep', ': ')
        kw.setdefault('start', 0)
        kw.setdefault('stop', len(lst))
        # we need to remove start and stop from kw so they don't propagate
        # into a recursive call for a nested list.
        start = kw['start']
        del kw['start']
        stop = kw['stop']
        del kw['stop']
        if self.depth == 0 and 'header' in kw.keys():
            print kw['header']

        for idx in range(start, stop):
            elem = lst[idx]
            if type(elem)==type([]):
                self.depth += 1
                self.__call__(elem, itpl('$pos$idx, '), **kw)
                self.depth -= 1
            else:
                printpl(kw['indent']*self.depth+'$pos$idx$kw["sep"]$elem')

nlprint = NLprinter()



#----------------------------------------------------------
# Logging simplified interface
# TODO  rewrite this basing on Bazaar debugging facilities

# logging interface

INITIAL_LEVEL = logging.DEBUG
# INITIAL_LEVEL = logging.INFO

logging.basicConfig(level=INITIAL_LEVEL,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S'
                   )


# TODO change to some windows temp value
def set_file_debug(fname = "D:\\Temp\\py.log"):
    """
    Sets debuglevel of message going to file.
    """
    l = logging.getLogger()
    fh = logging.FileHandler(fname)
    fh.setLevel(INITIAL_LEVEL)

    fmt = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    fh.setFormatter(fmt)

    l.addHandler(fh)

# this is broken ??
def enable_logging(enable=True):
    """Enables or disables logging. """
    if enable:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)



def debug(aMesg):
    """Prints a debug message to logger."""
    logging.debug(itpl(str(aMesg)))

def warn(aMesg):
    """Prints a warning message to logger."""
    logging.warn(itpl(str(aMesg)))


def info(aMesg):
    """Prints an info message to logger."""
    logging.info(itpl(str(aMesg)))

def critical(aMesg):
    """Prints a critical message to logger."""
    logging.critical(itpl(str(aMesg)))

def error(aMesg):
    """Writes error messages and exits. """
    sys.stderr.write("Error: " + itpl(str(aMesg)))
    sys.stderr.write("\n")
    sys.stderr.flush()
    sys.exit()


log = debug




#----------------------------------------------------------
# Build and repo related functions
#


def get_git_root_dir(path):
    """Returns Git root path for given file, if file is in Git repository."""
    path = os.path.abspath(path)
    parent = os.path.dirname(path)
    # go up recursively until find .git dir or go to top directory
    while not os.path.isdir(os.path.join(path, '.git')) and path != '' and path != parent:
        path = parent
        parent = os.path.dirname(path)

    if os.path.isdir(os.path.join(path, '.git')) and \
        os.path.isdir(os.path.join(path, '.git/refs')) and \
        os.path.isfile(os.path.join(path, '.git/HEAD')):
        return os.path.join(path, '.git')
    else:
        return None



def generate_buildno(path):
    """Generates build number in build_stamp.py file, which gets imported to
    read the current build version.
    The build number is generated as current date yyyymmdd plus 6 digits of
    current head git sha1 code.
    """
    # generate current date
    builddate = time.strftime('%y%m%d')

    # try to find .git head tip and use it as a tip
    # else read embedded number by the build script.
    buildsha1 = ''
    git_root_dir = get_git_root_dir(path)
    if git_root_dir:
        # try to read SHA1 from head file directly
        try:
            head = open(os.path.join(git_root_dir, 'HEAD')).read().strip()[5:]
            headsha1 = open(os.path.join(git_root_dir, head)).read().strip()
        except:
            # try to run git to retrieve the name directly
            # if it's not found then try to run git process
            import subprocess
            olddir = os.getcwd()
            os.chdir(git_root_dir)
            output = subprocess.Popen(['git', 'show', '-s'], stdout=subprocess.PIPE).communicate()[0]
            headsha1 = output[7:]
            os.chdir(olddir)
        buildsha1 = headsha1[0:6]
    else:
        return None

    return builddate + '.' + buildsha1


def load_stamped_buildno():
    buildno = None
    try:
        import build_stamp
        buildno = build_stamp.buildno
    except:
        raise
#         pass
    return buildno


def save_stamped_buildno():
    git_root_dir = get_git_root_dir(os.getcwd())
    root_dir = os.path.dirname(git_root_dir)
    assert root_dir <> '', 'GIT root dir not found!'
    f = open(os.path.join(root_dir, 'src/build_stamp.py'), 'wt')
    f.write('#!/bin/env python\n')
    f.write('# DO NOT EDIT THIS FILE.\n')
    f.write('# This file is generated automatically by the build.py script.\n')
    f.write('# All contents here will be overwritten.\n\n')
    f.write('buildno = "%s"' % generate_buildno(root_dir))
    f.close()
