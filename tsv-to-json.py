#!/usr/bin/env python
"""
TSV in; JSON out
"""

import os
import csv
import sys
import gzip
import boto
import simplejson as json
import string
from StringIO import StringIO
from optparse import OptionParser

def convert(opts, obj_name):

    s3 = boto.connect_s3()

    obj = s3.lookup('mh-cloudfront-logs').lookup(obj_name)
    gzip_stream = gzip.GzipFile(mode='rb', fileobj=StringIO(obj.read()))

    if opts.skip is not None:
        for i in range(opts.skip):
            next(gzip_stream)

    in_parts = os.path.splitext(obj_name)
    dest_base = os.path.join(opts.dest, os.path.basename(in_parts[0]))

    keys = next(gzip_stream).replace('#Fields: ', '')
    keys = [k.strip() for k in keys.split()]
    reader = csv.DictReader(gzip_stream, fieldnames=keys, delimiter="\t")

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
        dest_fh.write(json.dumps(row) + "\n")
#        line = " ".join("%s=%s" % i for i in row.iteritems())
#        dest_fh.write("%s %s\n" % (timestamp, line))
        count += 1

    if dest_fh is not None:
        dest_fh.close()

if __name__ == '__main__':
    op = OptionParser()
    op.add_option('-s', '--skip', dest='skip', action='store',
        help='skip x number of lines', type=int)
    op.add_option('-t', '--split', dest='split', action='store',
        help='max lines per output file', type=int)
    op.add_option('-d', '--dest', dest='dest', action='store',
        help='output directory path')

    opts, obj_names = op.parse_args()

    for obj_name in obj_names:
        convert(opts, obj_name)



