#!/usr/bin/env python

__description__ = "Program to use Python's re.findall on files"
__author__ = 'Didier Stevens'
__version__ = '0.0.12'
__date__ = '2018/07/28'

"""

Source code put in public domain by Didier Stevens, no Copyright
https://DidierStevens.com
Use at your own risk

History:
  2013/12/06: start
  2013/12/15: added re-search.txt support, options -b -s
  2014/03/25: added ipv4
  2014/04/03: added extra regex comments
  2014/04/09: refactoring: module reextra
  2014/07/18: added manual, stdin
  2014/09/16: updated manual
  2014/09/17: added exception handling for import reextra
  2014/10/10: added options csv, grep and removeanchor
  2014/11/04: updated man
  2014/11/13: added error handling to CompileRegex
  2015/07/07: added option fullread
  2015/07/28: 0.0.2 added option dotall
  2016/07/22: fix for binary files/data
  2017/03/03: added str regex
  2017/04/10: 0.0.4 added option grepall
  2017/05/13: 0.0.5 bugfix output line
  2017/05/17: 0.0.6 added regex btc
  2017/05/18: 0.0.7 fixed regex btc, thanks @SecurityBeard
  2017/06/13: 0.0.8 added --script and --execute
  2017/09/06: 0.0.9 added option -x
  2018/06/25: 0.0.10 added regexs email-domain, url-domain and onion
  2018/06/29: 0.0.11 fixed ProcessFile for Linux/OSX
  2018/06/30: added option -e
  2018/07/28: added regexes str-e, str-u and str-eu

Todo:
  add hostname to header
"""

import optparse
import glob
import collections
import re
import sys
import os
import pickle
import math
import textwrap
import csv
import binascii

try:
    import reextra
except:
    print("This program requires module reextra (it is a part of the re-search package).\nMake sure it is installed in Python's module repository or the same folder where re-search.py is installed.")
    exit(-1)

REGEX_STANDARD = '[\x09\x20-\x7E]'

dLibrary = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}',
            'email-domain': r'[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,6})',
            'url': r'[a-zA-Z]+://[-a-zA-Z0-9.]+(?:/[-a-zA-Z0-9+&@#/%=~_|!:,.;]*)?(?:\?[a-zA-Z0-9+&@#/%=~_|!:,.;]*)?',
            'url-domain': r'[a-zA-Z]+://([-a-zA-Z0-9.]+)(?:/[-a-zA-Z0-9+&@#/%=~_|!:,.;]*)?(?:\?[a-zA-Z0-9+&@#/%=~_|!:,.;]*)?',
            'ipv4': r'\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b',
            'str': r'"[^"]+"',
            'str-e': r'"[^"]*"',
            'str-u': r'"([^"]+)"',
            'str-eu': r'"([^"]*)"',
            'btc': r'(?#extra=P:BTCValidate)\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
            'onion': r'[a-zA-Z2-7]{16}\.onion',
           }

excludeRegexesForAll = ['str', 'url-domain', 'email-domain']

def ListLibraryNames():
    result = ''
    MergeUserLibrary()
    for key in sorted(dLibrary.keys()):
        result += ' %s%s: %s\n' % (key, IFF(key in excludeRegexesForAll, '', '*'), dLibrary[key])
    return result + ' all: all names marked with *\n'

def PrintManual():
    manual = '''
Manual:

re-search is a program to match regular expressions. It is like grep -o, it will match regular expressions in text files, not the complete line.

It has 2 major features: a small, extendable library of regular expressions selectable by name; and extra functionality like gibberish detection, whitelists/blacklists and Python functions.

We will use this list of URLs in our examples:
http://didierstevens.com
http://zcczjhbczhbzhj.com
http://www.google.com
http://ryzaocnsyvozkd.com
http://www.microsoft.com
http://ahsnvyetdhfkg.com

Example to extract alphabetical .com domains from file list.txt with a regular expression:
re-search.py [a-z]+\.com list.txt

Output:
didierstevens.com
zcczjhbczhbzhj.com
google.com
ryzaocnsyvozkd.com
microsoft.com
ahsnvyetdhfkg.com

Example to extract URLs from file list.txt with the build-in regular expression for URLs:
re-search.py -n url list.txt

Output:
http://didierstevens.com
http://zcczjhbczhbzhj.com
http://www.google.com
http://ryzaocnsyvozkd.com
http://www.microsoft.com
http://ahsnvyetdhfkg.com

Here is a list of build-in regular expressions:\n''' + ListLibraryNames() + '''
You can also use a capture group in your regular expression. The selected text will be extracted from the first capture group:
re-search.py ([a-z]+)\.com list.txt

Output:
didierstevens
zcczjhbczhbzhj
google
ryzaocnsyvozkd
microsoft
ahsnvyetdhfkg

By default the regular expression matching is not case sensitive. You can make it case sensitive with option -c. To surround the regular expression with boundaries (\b), use option -b. Output can be mode lowercase with option -l and unique with option -u. Output can be saved to a file with option -o filename. And if you also want to output the regular expression used for matching, use option -d.
To get grep-like output, use option -g. Option -r removes the anchor (^and $) or the regular expression. Use option -D (dotall) to make the . expression match newline characters.
By default, re-search reads the file(s) line-by-line. Binary files can also be processed, but are best read completely and not line-by-line. Use option -f (fullread) to perform a full binary read of the file (and not line-by-line).
Option -e (extractstrings) will also do a full binary read of the file (like -f --fullread), and then extract all strings (ASCII and UNICODE, and at least 4 characters long) for further matching.
Option -G (grepall) will also do a full binary read of the file (like -f --fullread), but output the complete file if there is a match. This is usefull to select files for further processing, like string searching.
Option -x (hex) will produce hexadecimal output.

If you have a list of regular expressions to match, put them in a csv file, and use option -v, -S, -I, -H, -R and -C.
Example:
re-search.py -vHrg -o result -S , -I " " -R PCRE -C pcre.csv logs

Gibberish detection, whitelists/blacklists filtering and matching with Python functions is done by prefixing the regular expression with a comment. Regular expressions can contain comments, like programming languages. This is a comment for regular expressions: (?#comment).
If you use re-search with regular expression comments, nothing special happens:
re-search.py "(?#comment)[a-z]+\.com" list.txt

However, if your regular expression comment prefixes the regular expression, and the comment starts with keyword extra=, then you can use gibberish detection, whitelist/blacklist filtering and Python function matching.
To use gibberisch detection, you use directive S (S stands for sensical). If you want to filter all strings that match the regular expression and are gibberish, you use the following regular expression comment: (?#extra=S:g). :g means that you want to filter for gibberish.

Example to extract alphabetical .com domains from file list.txt with a regular expression that are gibberish:
re-search.py "(?#extra=S:g)[a-z]+\.com" list.txt

Output:
zcczjhbczhbzhj.com
ryzaocnsyvozkd.com
ahsnvyetdhfkg.com

If you want to filter all strings that match the regular expression and are not gibberish, you use the following regular expression comment: (?#extra=S:s). :s means that you want to filter for sensical strings.

Example to extract alphabetical .com domains from file list.txt with a regular expression that are not gibberish:
re-search.py "(?#extra=S:s)[a-z]+\.com" list.txt

Output:
didierstevens.com
google.com
microsoft.com

Blacklists are defined via directive E (Exclude). If you want to filter all strings that match the regular expression and are not in the blacklist, you use the following regular expression comment: (?#extra=E:blacklist). blacklist is a textfile you provide containing all the strings to be blacklisted.

Example to extract alphabetical .com domains from file list.txt with a regular expression that are not in file blacklist (blacklist contains google.com):
re-search.py "(?#extra=E:blacklist)[a-z]+\.com" list.txt

Output:
didierstevens.com
zcczjhbczhbzhj.com
ryzaocnsyvozkd.com
microsoft.com
ahsnvyetdhfkg.com

Whitelists are defined via directive I (Include). If you want to filter all strings that match the regular expression and are in the whitelist, you use the following regular expression comment: (?#extra=I:whitelist). Whitelist is a textfile you provide containing all the strings to be whitelisted.

Example to extract alphabetical .com domains from file list.txt with a regular expression that are in file whitelist (whitelist contains didierstevens.com):
re-search.py "(?#extra=I:whitelistlist)[a-z]+\.com" list.txt

Output:
didierstevens.com

Python function matching is defined via directive P (Python). If you want to validate a string with a Python function, you use the following regular expression comment: (?#extra=P:Validate). Validate is a Python function that takes a string as argument and returns a boolean: True for a match and False if there is no match. You can provide your custom Python function(s) in a file via option --script or as a commandline argument via option --execute.

Example: Bitcoin address matching. Regular expression [13][a-km-zA-HJ-NP-Z1-9]{25,34} will match Bitcoin addresses, but also other strings that look like a Bitcoin address but are not a valid Bitcoin address. A valid Bitcoin address has a particular syntax, and a valid checksum. The regular expression can check the syntax, but not validate the checksum. Python function BTCValidate can check the checksum of a Bitcoin address. The following regular expression matches Bitcoin addresses with a valid syntax and uses Python function BTCValidate to validate the checksum:
(?#extra=P:BTCValidate)[13][a-km-zA-HJ-NP-Z1-9]{25,34}

You can use more than one directive in a regular expression. Directives are separated by the ; character.

Example to extract alphabetical .com domains from file list.txt with a regular expression that are not gibberish and that are not blacklisted:
re-search.py "(?#extra=S:s;E:blacklist)[a-z]+\.com" list.txt

Output:
didierstevens.com
microsoft.com


Classifying a string as gibberish or not, is done with a set of classes that I developed based on work done by rrenaud at https://github.com/rrenaud/Gibberish-Detector. The training text is a public domain book in the Sherlock Holmes series. This means that English text is used for gibberish classification. You can provide your own trained pickle file with option -s.

You can extend the library of regular expressions used by re-search without changing the program source code. Create a text file named re-search.txt located in the same directory as re-search.py. For each regular expression you want to add to the library, enter a line with format name=regex. Here is an example for MAC addresses:

mac=[0-9A-F]{2}([-:]?)(?:[0-9A-F]{2}\1){4}[0-9A-F]{2}

re-search.py requires module reextra, which is part of the re-search package.
'''
    for line in manual.split('\n'):
        print(textwrap.fill(line))

QUOTE = '"'

def IfWIN32SetBinary(io):
    if sys.platform == 'win32':
        import msvcrt
        msvcrt.setmode(io.fileno(), os.O_BINARY)

def ToString(value):
    if type(value) == type(''):
        return value
    else:
        return str(value)

def Quote(value, separator, quote):
    value = ToString(value)
    if separator in value:
        return quote + value + quote
    else:
        return value

def MakeCSVLine(row, separator, quote):
    return separator.join([Quote(value, separator, quote) for value in row])

def File2Strings(filename):
    try:
        f = open(filename, 'r')
    except:
        return None
    try:
        return map(lambda line:line.rstrip('\n'), f.readlines())
    except:
        return None
    finally:
        f.close()

def ProcessAt(argument):
    if argument.startswith('@'):
        strings = File2Strings(argument[1:])
        if strings == None:
            raise Exception('Error reading %s' % argument)
        else:
            return strings
    else:
        return [argument]

# CIC: Call If Callable
def CIC(expression):
    if callable(expression):
        return expression()
    else:
        return expression

# IFF: IF Function
def IFF(expression, valueTrue, valueFalse):
    if expression:
        return CIC(valueTrue)
    else:
        return CIC(valueFalse)

#Fix for http://bugs.python.org/issue11395
def StdoutWriteChunked(data):
    while data != '':
        sys.stdout.write(data[0:10000])
        try:
            sys.stdout.flush()
        except IOError:
            return
        data = data[10000:]

class cOutput():
    def __init__(self, grepall, filename=None):
        self.grepall = grepall
        self.filename = filename
        if self.filename and self.filename != '':
            if self.grepall:
                self.f = open(self.filename, 'wb')
            else:
                self.f = open(self.filename, 'w')
        else:
            self.f = None
            if self.grepall:
                IfWIN32SetBinary(sys.stdout)

    def Line(self, line):
        if self.grepall:
            if self.f:
                self.f.write(line)
            else:
                StdoutWriteChunked(line)
        else:
            if self.f:
                self.f.write(line + '\n')
            else:
                print(line)

    def Close(self):
        if self.f:
            self.f.close()
            self.f = None

def ExpandFilenameArguments(filenames):
    return list(collections.OrderedDict.fromkeys(sum(map(glob.glob, sum(map(ProcessAt, filenames), [])), [])))

def PrintLibrary():
    global dLibrary

    print('Valid regex library names:')
    for key in sorted(dLibrary.keys()):
        print(' %s: %s' % (key, dLibrary[key]))

def MergeUserLibrary():
    global dLibrary

    lines = File2Strings(os.path.splitext(sys.argv[0])[0] + '.txt')
    if not lines:
        return
    for line in lines:
        if not line.startswith('#'):
            result = line.split('=')
            if len(result) == 2:
                dLibrary[result[0]] = result[1]

def Library(name):
    global dLibrary

    MergeUserLibrary()

    try:
        return dLibrary[name]
    except KeyError:
        print('Invalid regex library name: %s' % name)
        print('')
        PrintLibrary()
        sys.exit(-1)

def LibraryAllNames():
    global dLibrary

    MergeUserLibrary()
    return sorted(dLibrary.keys())

class cOutputResult():
    def __init__(self, options):
        if options.output:
            self.oOutput = cOutput(options.grepall, options.output)
        else:
            self.oOutput = cOutput(options.grepall)
        self.options = options
        self.dLines = {}

    def Line(self, line):
        if self.options.grepall:
            self.oOutput.Line(line)
        else:
            line = IFF(self.options.lower, lambda: line.lower(), line)
            if not line in self.dLines:
                self.oOutput.Line(line)
            if self.options.unique and not line in self.dLines:
                self.dLines[line] = True

    def Close(self):
        self.oOutput.Close()

def CompileRegex(regex, options):
    regex = IFF(options.name, lambda: Library(regex), regex)
    if options.removeanchor:
        regex = IFF(regex.startswith('^'), regex[1:], regex)
        regex = IFF(regex.endswith('$'), regex[:-1], regex)
    regex = IFF(options.boundary, '\\b%s\\b' % regex, regex)
    try:
        oREExtra = reextra.cREExtra(regex, IFF(options.casesensitive, 0, re.IGNORECASE) + IFF(options.dotall, 0, re.DOTALL), options.sensical)
    except:
        raise Exception('Error regex: %s' % regex)
    return regex, oREExtra

def ProcessFile(fIn, fullread):
    if fullread:
        yield fIn.read()
    else:
        for line in fIn:
            yield line.strip('\n\r')

def Hex(data, dohex):
    if dohex:
        return binascii.b2a_hex(data)
    else:
        return data

def ExtractStringsASCII(data):
    regex = REGEX_STANDARD + '{%d,}'
    return re.findall(regex % 4, data)

def ExtractStringsUNICODE(data):
    regex = '((' + REGEX_STANDARD + '\x00){%d,})'
    return [foundunicodestring.replace('\x00', '') for foundunicodestring, dummy in re.findall(regex % 4, data)]

def ExtractStrings(data):
    return ExtractStringsASCII(data) + ExtractStringsUNICODE(data)

def DumpFunctionStrings(data):
    return ''.join([extractedstring + '\n' for extractedstring in ExtractStrings(data)])

def RESearchSingle(regex, filenames, oOutput, options):
    if options.name and regex == 'all':
        regexes = [CompileRegex(name, options) for name in LibraryAllNames() if not name in excludeRegexesForAll]
    else:
        regexes = [CompileRegex(regex, options)]
    for filename in filenames:
        if filename == '':
            if options.fullread or options.extractstrings or options.grepall:
                IfWIN32SetBinary(sys.stdin)
            fIn = sys.stdin
        else:
            fIn = open(filename, IFF(options.fullread or options.extractstrings or options.grepall, 'rb', 'r'))
        for line in ProcessFile(fIn, options.fullread or options.extractstrings or options.grepall):
            if options.extractstrings:
                line = DumpFunctionStrings(line)
            for regex, oREExtra in regexes:
                if options.display:
                    oOutput.Line('Regex: %s' % regex)
                results = oREExtra.Findall(line)
                if options.grepall or options.grep:
                    if results != []:
                        oOutput.Line(Hex(line, options.hex))
                else:
                    for result in results:
                        if isinstance(result, str):
                            oOutput.Line(Hex(result, options.hex))
                        if isinstance(result, tuple):
                            oOutput.Line(Hex(result[0], options.hex))
        if fIn != sys.stdin:
            fIn.close()

def RESearchCSV(csvFilename, filenames, oOutput, options):
    reader = csv.reader(open(csvFilename, 'r'), delimiter=options.separatorcsv, skipinitialspace=False, quoting=IFF(options.unquoted, csv.QUOTE_NONE, csv.QUOTE_MINIMAL))
    indexRegex = 0
    indexComment = None
    if not options.header:
        if options.regexindex != '':
            indexRegex = int(options.regexindex)
        if options.commentindex != '':
            indexComment = int(options.commentindex)
    firstRow = True
    dRegex = {}
    for row in reader:
        if options.header and firstRow:
            firstRow = False
            if options.regexindex != '':
                indexRegex = row.index(options.regexindex)
            if options.commentindex != '':
                indexComment = row.index(options.commentindex)
            continue
        regex, oREExtra = CompileRegex(row[indexRegex], options)
        if options.display:
            oOutput.Line('Regex: %s' % row[indexRegex])
        dRegex[regex] = (oREExtra, IFF(indexComment == None, None, lambda: row[indexComment]))

    for filename in filenames:
        if filename == '':
            if options.fullread or options.extractstrings or options.grepall:
                IfWIN32SetBinary(sys.stdin)
            fIn = sys.stdin
        else:
            fIn = open(filename, IFF(options.fullread or options.extractstrings or options.grepall, 'rb', 'r'))
        for line in ProcessFile(fIn, options.fullread or options.extractstrings or options.grepall):
            if options.extractstrings:
                line = DumpFunctionStrings(line)
            for regex, (oREExtra, comment) in dRegex.items():
                results = oREExtra.Findall(line)
                newRow = [regex]
                if comment != None:
                    newRow.append(comment)
                if options.grep:
                    if results != []:
                        if options.separatorinput == '':
                            newRow.append(line)
                            outputLine = MakeCSVLine(newRow, options.separatorcsv, QUOTE)
                        else:
                            outputLine = MakeCSVLine(newRow, options.separatorinput, QUOTE) + options.separatorinput + line
                        oOutput.Line(outputLine)
                else:
                    for result in results:
                        if isinstance(result, str):
                            if options.separatorinput == '':
                                newRow.append(result)
                                outputLine = MakeCSVLine(newRow, options.separatorcsv, QUOTE)
                            else:
                                outputLine = MakeCSVLine(newRow, options.separatorinput, QUOTE) + options.separatorinput + result
                        if isinstance(result, tuple):
                            if options.separatorinput == '':
                                newRow.append(result[0])
                                outputLine = MakeCSVLine(newRow, options.separatorcsv, QUOTE)
                            else:
                                outputLine = MakeCSVLine(newRow, options.separatorinput, QUOTE) + options.separatorinput + result[0]
                        oOutput.Line(outputLine)
        if fIn != sys.stdin:
            fIn.close()

def RESearch(regex, filenames, options):
    oOutput = cOutputResult(options)
    if options.script != '':
        reextra.Script(options.script)
    if options.execute != '':
        reextra.Execute(options.execute)
    if options.csv:
        RESearchCSV(regex, filenames, oOutput, options)
    else:
        RESearchSingle(regex, filenames, oOutput, options)
    oOutput.Close()

def Main():
    global dLibrary

    moredesc = '''

Arguments:
@file: process each file listed in the text file specified
wildcards are supported

Valid regex library names:
'''

    moredesc += ListLibraryNames()
    moredesc += '''
Source code put in the public domain by Didier Stevens, no Copyright
Use at your own risk
https://DidierStevens.com'''

    oParser = optparse.OptionParser(usage='usage: %prog [options] regex [[@]file ...]\n' + __description__ + moredesc, version='%prog ' + __version__)
    oParser.add_option('-n', '--name', action='store_true', default=False, help='The regex argument is a name of a library regex')
    oParser.add_option('-c', '--casesensitive', action='store_true', default=False, help='Make search case-sensitive')
    oParser.add_option('-l', '--lower', action='store_true', default=False, help='Lowercase output')
    oParser.add_option('-u', '--unique', action='store_true', default=False, help='Unique output')
    oParser.add_option('-o', '--output', type=str, default='', help='Output to file')
    oParser.add_option('-b', '--boundary', action='store_true', default=False, help='Add boundaries (\\b) around the regex')
    oParser.add_option('-d', '--display', action='store_true', default=False, help='Display the regex')
    oParser.add_option('-s', '--sensical', default='', help='Sensical pickle file')
    oParser.add_option('-m', '--man', action='store_true', default=False, help='Print manual')
    oParser.add_option('-g', '--grep', action='store_true', default=False, help='Outputs the complete line, like grep (without -o)')
    oParser.add_option('-r', '--removeanchor', action='store_true', default=False, help='Remove anchor of regex starting with ^ and/or ending with $')
    oParser.add_option('-v', '--csv', action='store_true', default=False, help='First argument is a CSV file with regular expressions')
    oParser.add_option('-S', '--separatorcsv', default=';', help='Separator character for CSV file (default ;)')
    oParser.add_option('-I', '--separatorinput', default='', help='Separator character for input file (default none)')
    oParser.add_option('-U', '--unquoted', action='store_true', default=False, help='No handling of quotes in CSV file')
    oParser.add_option('-H', '--header', action='store_true', default=False, help='Header')
    oParser.add_option('-R', '--regexindex', default='', help='Index or title of the regex column in the CSV file')
    oParser.add_option('-C', '--commentindex', default='', help='Index or title of the comment column in the CSV file')
    oParser.add_option('-f', '--fullread', action='store_true', default=False, help='Do a full binary read of the input, not line per line')
    oParser.add_option('-e', '--extractstrings', action='store_true', default=False, help='Do a full binary read of the input, and extract strings for matching')
    oParser.add_option('-G', '--grepall', action='store_true', default=False, help='Do a full read of the input and a full write when there is a match, not line per line')
    oParser.add_option('-D', '--dotall', action='store_true', default=False, help='. matches newline too')
    oParser.add_option('-x', '--hex', action='store_true', default=False, help='output in hex format')
    oParser.add_option('--script', default='', help='Python script file with definitions to include')
    oParser.add_option('--execute', default='', help='Python commands to execute')
    (options, args) = oParser.parse_args()

    if options.man:
        oParser.print_help()
        PrintManual()
        return

    if len(args) == 0:
        oParser.print_help()
    elif len(args) == 1:
        RESearch(args[0], [''], options)
    else:
        RESearch(args[0], ExpandFilenameArguments(args[1:]), options)

if __name__ == '__main__':
    Main()
