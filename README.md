# S3CloudfrontToLoggly

Python-flavored AWS Lambda function for fetching cloudfront logs from s3 and bulk uploading to loggly

# Prerequisites

* an AWS account that includes permissions to the relevant services: Lambda & S3.
* a python2.7 environment for building the Lambda function package. I recommend [pyenv](https://github.com/yyuu/pyenv) for managing multiple python versions.
* the `python-virtualenv` package installed

# Getting started

* `git clone` this repo and `cd` into it
* Create & activate a virtualenv: `virtualenv venv && source venv/bin/activate`
* `pip install -r requirements.txt`
* `cp config.cfg.example config.cfg`
* Update `config.cfg` with the appropriate values

# Config options

* **AWS key id/secret**: optional. leave empty if using role-based auth (recommended). 
* **loggly_token** - the access token for your loggly account
* **loggly_tags** - any additional tags you want added to the events, separated by commas. See [here](https://www.loggly.com/docs/tags/) for more.
* **include_bucket_tag** - if enabled, include the s3 source bucket name as a loggly event tag
* **max_lines** - max number of events to send at once. Default is probably fine. You just don't want the uploaded "chunks" to be greater than 5MB.
* **debug** - if enabled, extra debug info will be written to the lambda function log output

# Prep your lambda code

