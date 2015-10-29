# AWS Lambda python handler to push Cloudfront logs from s3 to loggly

import csv
import boto3
import gzip
import json
import logging
from StringIO import StringIO
from tempfile import NamedTemporaryFile
from ConfigParser import ConfigParser
from botocore.vendored import requests

LOGGLY_URL = 'https://logs-01.loggly.com'

log = logging.getLogger()
log_format = '%(asctime)-15s %(levelname)s %(name)s %(module)s:%(funcName)s:%(lineno)s - %(message)s'
log_format=logging.Formatter(log_format)
for h in log.handlers:
    h.setFormatter(log_format)
log.setLevel(logging.INFO)

log.info("Loading function")

config = ConfigParser(allow_no_value=True)
config.read('config.cfg')

if config.getboolean('config', 'debug'):
    log.setLevel(logging.DEBUG)

s3 = boto3.resource('s3')

def upload(fh, bucket):

    token = config.get('config', 'loggly_token')
    tags = config.get('config', 'loggly_tags')
    if config.getboolean('config', 'include_bucket_tag'):
        tags += ',%s' % bucket
    upload_url = '%s/bulk/%s/tag/%s' % (LOGGLY_URL, token, tags)

    log.debug("uploading bulk events from %s", fh.name)
    log.debug("using upload url: %s", upload_url)

    fh.flush()
    fh.seek(0)

    resp = requests.post(upload_url, data=fh,
                         headers={'Content-type': 'application/json'})
    log.debug("response status: %d", resp.status_code)
    log.debug("response: %s", resp.content)
    resp.raise_for_status()

def lambda_handler(event, context):
    logging.debug("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    logging.info("bucket: %s, key: %s", bucket_name, key)

    try:
        obj = s3.Object(bucket_name, key).get()
    except Exception as e:
        log.error(e)
        log.error('Error getting object %s from bucket %s', key, bucket_name)
        raise

    gzip_steam = gzip.GzipFile(mode='rb', fileobj=StringIO(obj['Body'].read()))

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
                try:
                    upload(tmp_file, bucket_name)
                except Exception, e:
                    log.error("Error during upload: %s", str(e))
                    raise
                finally:
                    tmp_file.close()
            tmp_file = NamedTemporaryFile(mode='rb+')
        row['timestamp'] = "%sT%s.000Z" % (row['date'], row['time'])
        
        # convert stringified int/float values  
        row = dict((k, str2num(v)) for k,v in row.iteritems())

        tmp_file.write(json.dumps(row) + "\n")
        count += 1

    if tmp_file is not None:
        upload(tmp_file, bucket_name)
        tmp_file.close()

    log.info("Uploaded %d total events", count)


# helpers for converting the stringified int/float values in the parsed log data
# into their indexable format. not the most effficient way to do this, but more
# scrutable than other methods i've seen
def is_int(obj):
    try: i = int(obj)
    except: return False
    return True

def is_float(obj):
    try: f = float(obj)
    except: return False
    return True

def str2num(obj):
    if not isinstance(obj, basestring): return obj
    if is_int(obj): return int(obj)
    if is_float(obj): return float(obj)
    return obj

