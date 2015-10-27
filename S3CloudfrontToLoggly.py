# AWS Lambda python handler to push Cloudfront logs from s3 to loggly

import csv
import boto
import gzip
import json
import logging
from StringIO import StringIO
from tempfile import NamedTemporaryFile
from ConfigParser import ConfigParser
from httplib import HTTPConnection, HTTPException

log = logging.getLogger()
log.setLevel(logging.INFO)

log.info("Loading function")

config = ConfigParser(allow_no_value=True)
config.read('config.cfg')

if config.getboolean('config', 'debug'):
    log.setLevel(logging.DEBUG)

s3 = boto.connect_s3()
conn = HTTPConnection("logs-01.loggly.com")

def upload(fh, bucket):

    token = config.get('config', 'loggly_token')
    tags = config.get('config', 'loggly_tags')
    if config.getboolean('config', 'include_bucket_tag'):
        tags += ',%s' % bucket
    upload_path = '/bulk/%s/tag/%s' % (token, tags)
    log.debug("using upload_path: %s", upload_path)

    try:
        conn.request("POST", upload_path, fh, {'Content-type': 'application/json'})
    finally:
        conn.close()

    resp = conn.getresponse()
    if resp.status != 200:
        raise Exception("%s %s: %s" % resp.status, resp.reason, resp.read())
    log.debug("response: %s", resp.read())

def lambda_handler(event, context):
    logging.debug("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    logging.info("bucket: %s, key: %s", bucket, key)

    try:
        bucket = s3.get_bucket(bucket)
        obj = bucket.get_key(key)
    except Exception as e:
        log.error(e)
        log.error('Error getting object %s from bucket %s', key, bucket)
        raise

    gzip_steam = gzip.GzipFile(mode='rb', fileobj=StringIO(obj.read()))

    # skip the first header line
    next(gzip_steam)

    keys = next(gzip_steam).replace('#Fields: ', '')
    keys = [k.strip() for k in keys.split()]

    reader = csv.DictReader(gzip_steam, fieldnames=keys, delimiter="\t")

    count = 0
    tmp_file = None
    max_lines = config.getint('config', 'max_lines')

    for row in reader:
        if count % max_lines == 0:
            log.debug("count: %d", count)
            if tmp_file is not None:
                tmp_file.flush()
                tmp_file.seek(0)
                try:
                    log.debug("uploading bulk events from %s", tmp_file.name)
                    upload(tmp_file, bucket)
                except Exception, e:
                    log.error("Error during upload of %s from %s", key, bucket)
                    log.error(e)
                    raise
                tmp_file.close()
            tmp_file = NamedTemporaryFile(mode='rb+')
        row['timestamp'] = "%sT%s.000Z" % (row['date'], row['time'])
        tmp_file.write(json.dumps(row) + "\n")
        count += 1

    log.info("Uploaded %d total events", count)

    if tmp_file is not None:
        tmp_file.close()


