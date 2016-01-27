#!/usr/bin/env python


import sys
if sys.version_info[0] >= 2 and sys.version_info[1] >= 7:
  import argparse
import codecs
from collections import defaultdict as dd
import re
import os.path
import gzip
import unicodedata as ud
scriptdir = os.path.dirname(os.path.abspath(__file__))



excluded = set([ud.lookup("TIBETAN MARK INTERSYLLABIC TSHEG"), # tshegs appear between syllables
                ud.lookup("TIBETAN MARK DELIMITER TSHEG BSTAR"),
                ])

def tokenize(line, tokchar=u' '):
  ''' Given a line of unicode, return the unitok tokenization of that line '''
  toks = []
  for char in line:
    cc = ud.category(char)
    if (cc.startswith("P") or cc.startswith("S")) and char not in excluded:
      toks.append(tokchar)
      toks.append(char)
      toks.append(tokchar)
    else:
      toks.append(char)
  return ' '.join(''.join(toks).split())
  
def main():
  parser = argparse.ArgumentParser(description="unicode-based tokenization",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('rb'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  reader = codecs.getreader('utf8')
  writer = codecs.getwriter('utf8')
  infile = gzip.open(args.infile.name, 'r') if args.infile.name.endswith(".gz") else args.infile
  infile = reader(infile)
  outfile = gzip.open(args.outfile.name, 'w') if args.outfile.name.endswith(".gz") else args.outfile
  outfile = writer(outfile)


  for line in infile:
    outfile.write(tokenize(line)+"\n")

if __name__ == '__main__':
  main()
