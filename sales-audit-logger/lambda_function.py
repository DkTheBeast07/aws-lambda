import json
from datetime import datetime

def lambda_handler(event, context):

    print(f"🔍 Audit Logger fired — {len(event['Records'])} change(s) detected")

    for record in event['Records']:
        event_name = record['eventName']  # INSERT / MODIFY / REMOVE
        new_image  = record['dynamodb'].get('NewImage', {})
        old_image  = record['dynamodb'].get('OldImage', {})

        # Pull values from DynamoDB stream format
        sale_id = new_image.get('sale_id', {}).get('S', 'unknown')
        product = new_image.get('product', {}).get('S', 'unknown')
        region  = new_image.get('region',  {}).get('S', 'unknown')
        amount  = new_image.get('total_amount', {}).get('S', '0')
        status  = new_image.get('status',  {}).get('S', 'unknown')

        # Build audit log entry
        audit = {
            'timestamp':  datetime.utcnow().isoformat(),
            'event_type': event_name,
            'sale_id':    sale_id,
            'product':    product,
            'region':     region,
            'amount':     f"${amount}",
            'status':     status,
            'message':    f"Record {sale_id} was {event_name.lower()}ed in DynamoDB"
        }

        # Log it — shows in CloudWatch
        if event_name == 'INSERT':
            print(f"✅ NEW RECORD  | {sale_id} | {product} | {region} | ${amount}")
        elif event_name == 'MODIFY':
            print(f"✏️  UPDATED     | {sale_id} | {product} | {region} | ${amount}")
        elif event_name == 'REMOVE':
            print(f"🗑️  DELETED     | {sale_id}")

        print(f"📋 AUDIT LOG: {json.dumps(audit)}")

    print(f"✅ Audit complete — {len(event['Records'])} record(s) logged")
