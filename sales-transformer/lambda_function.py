import boto3, csv, io, json, os
from datetime import datetime

s3       = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

DEST_BUCKET  = os.environ['DEST_BUCKET']
DYNAMO_TABLE = os.environ['DYNAMO_TABLE']

def lambda_handler(event, context):
    table = dynamodb.Table(DYNAMO_TABLE)

    for sqs_record in event['Records']:
        msg    = json.loads(sqs_record['body'])
        bucket = msg['bucket']
        key    = msg['key']
        print(f"📂 Processing: s3://{bucket}/{key}")

        # Read CSV from source S3
        obj     = s3.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        rows    = list(csv.DictReader(io.StringIO(content)))

        processed = []
        for row in rows:
            item = {
                'sale_id':      row['sale_id'].strip(),
                'product':      row['product'].strip(),
                'region':       row['region'].strip(),
                'quantity':     int(row['quantity']),
                'unit_price':   str(round(float(row['unit_price']), 2)),
                'total_amount': str(round(int(row['quantity']) * float(row['unit_price']), 2)),
                'sale_date':    row['sale_date'].strip(),
                'processed_at': datetime.utcnow().isoformat(),
                'source_file':  key,
                'status':       'processed'
            }
            # Save to DynamoDB
            table.put_item(Item=item)
            processed.append(item)
            print(f"✅ DynamoDB saved: {item['sale_id']} | {item['product']} | ${item['total_amount']}")

        # Save processed JSON to destination S3
        out_key = 'processed/' + key.split('/')[-1].replace('.csv', '_processed.json')
        summary = {
            'source_file':   key,
            'processed_at':  datetime.utcnow().isoformat(),
            'total_records': len(processed),
            'total_revenue': str(round(sum(float(r['total_amount']) for r in processed), 2)),
            'records':       processed
        }
        s3.put_object(
            Bucket=DEST_BUCKET,
            Key=out_key,
            Body=json.dumps(summary, indent=2),
            ContentType='application/json'
        )
        print(f"✅ S3 saved: s3://{DEST_BUCKET}/{out_key}")
        print(f"💰 Total Revenue: ${summary['total_revenue']}")
