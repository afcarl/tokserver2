#!/usr/bin/env python3
import argparse
import sys
#import codecs
from collections import defaultdict as dd
import re
import os.path
import gzip
from flask import Flask, url_for, request
import random
import utok
import tempfile
import os
import shutil
import atexit
import difflib
from subprocess import check_output, STDOUT, CalledProcessError, getoutput
import html
from html.parser import HTMLParser
scriptdir = os.path.dirname(os.path.abspath(__file__))

from flask_restful import Resource, Api
from flask.ext.cors import CORS
scriptdir = os.path.dirname(os.path.abspath(__file__))
archivedir = os.path.join(scriptdir, 'archive')

workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))
def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
atexit.register(cleanwork)

scrapefile=os.path.join(scriptdir, 'scrape.py')

app = Flask(__name__)

print("about to cors")
# this CORS wrapper is essential to prevent the ubiquitous CORS error!
CORS(app)
api = Api(app)

print("done with init")
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

class NumberedLetters(Resource):
    def get(self):
        d = dd(lambda: dd(list))
        #d = dd(list)
        d['id-a']['grub']=[1,2]
        d['content']['blarg']='hello world'
#        d['foo']={}
        d['foo']['bar']=7
        return d




import mspatterntokserver
patternpath=os.path.join(scriptdir, 'eng.20k.digsub-m4.tok.patterns')
#patternpath=os.path.join(scriptdir, 'foo')
pattok = mspatterntokserver.Tokenizer(True, True, open(patternpath))
def patterntokenize(data):
    return list(map(pattok.tokenize, data))

#agiletokpath=os.path.join(scriptdir, 'agile_tokenizer', 'dummy.sh')
#agiletokpath=os.path.join(scriptdir, 'twokenize.sh')
agiletokpath=os.path.join(scriptdir, 'agile_tokenizer', 'gale-eng-tok.sh')
twokenizepath=os.path.join(scriptdir, 'twokenize.sh')
cdectokpath=os.path.join(scriptdir, 'cdectok', 'tokenize-anything.sh')

def agiletok(data):
    return script_tokenize(data, agiletokpath)

def twokenize(data):
    return script_tokenize(data, twokenizepath)

def cdectok(data):
    return script_tokenize(data, cdectokpath)

def script_tokenize(data, cmdpath):
    ''' kludgy wrap of cmd line tokenizers '''
    datafile, dfname=tempfile.mkstemp(prefix=os.path.basename(__file__), dir=workdir)
    datafile = open(dfname, 'wb')
    for line in data:
        datafile.write((line+"\n").encode('utf8'))
    datafile.close()
    cmd=cmdpath+" < "+dfname+" 2> /dev/null"
    #print(cmd)
    tokres=check_output(cmd, shell=True).decode('utf8')
    #print(tokres)
    res = []
    for line in tokres.split('\n'):
        res.append(line.strip().split('\t')[0])
    os.remove(dfname)
    return res



tokenizations = [
    ('original', lambda x: x),
    ('baseline', cdectok),
    ('unitok', lambda x: list(map(utok.tokenize, x))),
    ('twokenize', twokenize),
    ('e20kpat', patterntokenize),
    ('agile', agiletok),

]

seqmatch = difflib.SequenceMatcher()
def diffcodes(base, mod):
    ''' get list of list of opcodes '''
    ret = []
    for bstr, mstr in zip(base, mod):
        seqmatch.set_seqs(bstr, mstr)
        opcodes = seqmatch.get_opcodes()
        newopcodes = []
        for opcode in opcodes:
            substr = mstr[opcode[3]:opcode[4]]
            newopcodes.append(opcode+(substr,))
        ret.append(newopcodes)
    return ret

    
class SpecificSet(Resource):
    print("Class init")
    loaded = dd(lambda: dd(list))
    

    def setup(lang, date):
        if len(SpecificSet.loaded[date][lang]) == 0:
            print("Setting up %s/%s" % (date, lang))
            path=os.path.join(archivedir, date, lang, 'tweets.txt')
            fh = open(path, 'rb')
            lines = []
            for line in fh:
                SpecificSet.loaded[date][lang].append(line.decode('utf8').strip().split('\t')[2])
            print("%d lines read" % len(SpecificSet.loaded[date][lang]))

    def __init__(self, lang, date):
        self.lang = lang
        self.date = date
        SpecificSet.setup(lang, date)



    def get(self):
        #print("Getting")
        d = dd(lambda: dd(list))
        lines = SpecificSet.loaded[self.date][self.lang]
        linelen=len(lines)
        numtweets=10
        selection = []
        for i in (range(numtweets)):
            choice = random.randint(0, linelen-1)
            item = lines[choice]
            selection.append(item)
        d['data']['length']=len(selection)
        for tokname, tokfun in tokenizations:
            tokres = tokfun(selection)
            d['data'][tokname]=tokres
            d['diffs'][tokname]=diffcodes(selection, tokres)

        return d

for thelang in ('Thai', 'Arabic', 'Indonesian', 'Spanish', 'Russian'):
    for thedate in ('20160103',):
        newurl = '%s_%s' % (thelang, thedate)
        api.add_resource(SpecificSet, '/'+newurl, endpoint=newurl, resource_class_args=(thelang, thedate))


api.add_resource(HelloWorld, '/')
api.add_resource(NumberedLetters, '/nl')
htmlparser = HTMLParser();


def mimicscrape(line):
    return "\t".join(('foo', 'User-supplied', '#', line, 'usr'))

class GetWikis(Resource):
    def get(self):
        items = request.args.get('items') or "1"
        items = int(items)
        lang = request.args.get('lang') or "random"
        usertext = request.args.get('usertext')
        if usertext is not None:
            lines = list(map(mimicscrape, usertext.split('\n')))
        else:
            if lang == 'random':
                langchoice = "--random"
            else:
                langchoice = "--code %s" % lang
            cmd=scrapefile+" --chars=140 %s --extracts=%d" % (langchoice, items)
            wikres = check_output(cmd, shell=True).decode('utf8')
            lines = wikres.split('\n')

        ret = []
        texts = []
        langs = []
        isocodes = []
        urls = []
        for line in lines:
            toks = line.split('\t')
            if len(toks) >= 4:
                texts.append(toks[3])
                langs.append(toks[1])
                isocodes.append(toks[4])
                urls.append(toks[2])
        alltokresults = {}
        alltokdiffs = {}
        for tokname, tokfun in tokenizations[1:]:
            #print(tokname)
            tokres = tokfun(texts)
            #print(tokres)
            #print(tokres[0])
            alltokresults[tokname] = tokres
            alltokdiffs[tokname] = diffcodes(texts, tokres)
        for tn, text in enumerate(texts):
                d = {'lang':langs[tn], 'isocode': isocodes[tn], 'url':urls[tn], 'text':text}
                tokresults = {}
                for tokname in alltokresults.keys():
                    tokresults[tokname] = {}
                    tokresults[tokname]['data']=alltokresults[tokname][tn]
                    tokresults[tokname]['diffs']=alltokdiffs[tokname][tn]
                d['tokenizations']=tokresults
                ret.append(d)
        return ret

api.add_resource(GetWikis, '/wik')

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="server for wiktok and tt2")
    parser.add_argument("--port", "-p", default=8082, type=int, help="port to run on")
    parser.add_argument("--host", "-o", default="0.0.0.0", help="host (usually 0.0.0.0 or 127.0.0.1")
    parser.add_argument("--debug", "-d", action='store_true', default=False, help="debug mode")


    try:
        args = parser.parse_args()
    except IOError as msg:
        parser.error(str(msg))

    print("running")
    app.run(host=args.host, port=args.port, debug=args.debug)

