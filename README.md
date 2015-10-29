# S3CloudfrontToLoggly

Python-flavored AWS Lambda function for fetching cloudfront logs from s3 and bulk uploading to loggly

The handler function is designed to be fired when a new, gzipped Cloudfront log file is dropped into an s3 bucket. (See the Cloudfront docs for how to set that stuff up.) It will first fetch the contents of the file, gzip decompress it, parse and structure the tsv-formatted events into json, and then push them to loggly via their bulk upload endpoint.

# Prerequisites

* an AWS account that includes usage rights for the relevant services, Lambda & S3.

# Prep the function code

* Clone the repo and `cd` into the directory:

```
git clone https://github.com/harvard-dce/S3CloudfrontToLoggly.git
cd S3CloudfrontToLoggly
```

* Make a local copy of the config file:

```
cp config.cfg.example config.cfg
```

* Update `config.cfg` with the appropriate values (see below)

* Create the zip file:

```
zip S3CloudfrontToLoggly.zip S3CloudfrontToLoggly.py config.cfg
```

# Create the function

1. Open the Lambda console: https://console.aws.amazon.com/lambda/home
1. Click **Create a Lambda Function**
1. Click **Skip** to skip the blueprint
1. In the **Name** field enter "S3CloudfrontToLoggly" (or whatever you want)
1. Choose the **python2.7** runtime
1. Select **Upload a .ZIP file** and select the zip file you created earlier
1. Enter "S3CloudfrontToLoggly.lambda_handler" as the **Handler**
1. For the **Role** select "S3 execution role" and follow the steps to create the new role
1. Other defaults depend on the size of your log files (I'm using 1024m/10s timeout)
1. Click **Next** and then **Create function**

# Configure the source

1. Click the **Event Sources** tab in your new function
1. Click **Add event source**
1. Choose "S3" as the **Event source type**
1. Select the bucket where your cloudfront logs are dumped
1. For **Event type** choose "Object Created (All)" -> "PUT"
1. Click **Submit** and you're done!

In the **Monitoring** tab of your fuction there is a link to the Cloudwatch log streams where you can check for success/errors.


# Config options

* **loggly_token** - the access token for your loggly account
* **loggly_tags** - any additional tags you want added to the events, separated by commas. See [here](https://www.loggly.com/docs/tags/) for more.
* **include_bucket_tag** - if enabled, include the s3 source bucket name as a loggly event tag
* **max_lines** - max number of events to send at once. Default is probably fine. You just don't want the uploaded "chunks" to be greater than 5MB.
* **debug** - if enabled, extra debug info will be written to the lambda function log output

