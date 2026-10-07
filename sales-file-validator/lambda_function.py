import boto3, csv, io, json, os

s3  = boto3.client('s3')
sqs = boto3.client('sqs')
sns = boto3.client('sns')

QUEUE_URL = os.environ['QUEUE_URL']
SNS_ARN   = os.environ['SNS_ARN']

REQUIRED  = {'sale_id','product','region','quantity','unit_price','sale_date'}

def lambda_handler(event, context):
    rec    = event['Records'][0]
    bucket = rec['s3']['bucket']['name']
    key    = rec['s3']['object']['key']
    print(f"📂 File received: s3://{bucket}/{key}")

    try:
        obj     = s3.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        reader  = csv.DictReader(io.StringIO(content))
        headers = set(reader.fieldnames or [])

        # Check headers
        missing = REQUIRED - headers
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        rows = list(reader)
        if len(rows) == 0:
            raise ValueError("CSV file has no data rows")

        # ✅ Valid — send to SQS
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps({
                'bucket':    bucket,
                'key':       key,
                'row_count': len(rows)
            })
        )
        print(f"✅ VALID: {len(rows)} rows → sent to SQS")

    except Exception as e:
        # ❌ Invalid — send alert email
        sns.publish(
            TopicArn=SNS_ARN,
            Subject=f"❌ Pipeline FAILED: {key}",
            Message=f"File: {key}\nReason: {str(e)}"
        )
        print(f"❌ INVALID: {str(e)} → SNS alert sent")
