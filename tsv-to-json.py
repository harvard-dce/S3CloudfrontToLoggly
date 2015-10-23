#!/usr/bin/env python
"""
TSV in; JSON out
"""

import os
import csv
import sys
import gzip
import string
import json
from optparse import OptionParser

if __name__ == '__main__':
    op = OptionParser()
    op.add_option('-s', '--skip', dest='skip', action='store',
        help='skip x number of lines', type=int)
    op.add_option('-i', '--in', dest='input', action='store',
        help='input source. default is stdin', default='-')
    op.add_option('-t', '--split', dest='split', action='store',
        help='max lines per output file', type=int)
    op.add_option('-d', '--dest', dest='dest', action='store',
        help='output directory path')

    opts, args = op.parse_args()

    if opts.input == '-':
        in_stream = sys.stdin
    else:
        if opts.input.endswith('.gz'):
            in_stream = gzip.open(opts.input, 'rb')
        else:
            in_stream = open(opts.input, 'rb')

    if opts.skip is not None:
        for i in range(opts.skip):
            next(in_stream)

    in_parts = os.path.splitext(opts.input)
    dest_base = os.path.join( opts.dest, os.path.basename(in_parts[0]))

    keys = next(in_stream).replace('#Fields: ', '')
    keys = [string.strip(t) for t in string.split(keys)]
    reader = csv.DictReader(in_stream, fieldnames=keys, delimiter="\t")

    count = 0
    split_num = 0
    dest_fh = None
    for row in reader:
        if opts.split is not None:
            if count % opts.split == 0:
                if dest_fh is not None:
                    dest_fh.close()
                dest_fh = open(dest_base + '_' + str(split_num) + '.json', 'wb')
                split_num += 1
        else:
            dest_fh = open(dest_base + '.json', 'wb')

        row['timestamp'] = "%sT%s.000Z" % (row['date'], row['time'])
        dest_fh.write(json.dumps(row) + '\n')
        count += 1

    if dest_fh is not None:
        dest_fh.close()
