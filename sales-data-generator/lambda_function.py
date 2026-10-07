import boto3, csv, io, os, random
from datetime import datetime, timedelta

s3 = boto3.client('s3')
SOURCE_BUCKET = os.environ['SOURCE_BUCKET']

PRODUCTS = ['Laptop','Mouse','Keyboard','Monitor','Headphones',
            'Webcam','USB Hub','Laptop Stand']
REGIONS  = ['North','South','East','West']
PRICES   = {
    'Laptop': 850.00, 'Mouse': 25.50, 'Keyboard': 45.00,
    'Monitor': 320.00, 'Headphones': 75.00, 'Webcam': 60.00,
    'USB Hub': 18.00, 'Laptop Stand': 35.00
}

def lambda_handler(event, context):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['sale_id','product','region',
                     'quantity','unit_price','sale_date'])

    for i in range(1, 11):
        product  = random.choice(PRODUCTS)
        region   = random.choice(REGIONS)
        quantity = random.randint(1, 10)
        date     = (datetime.utcnow() - timedelta(
                     days=random.randint(0, 2))).strftime('%Y-%m-%d')
        writer.writerow([
            f"S{i:03d}", product, region,
            quantity, PRICES[product], date
        ])

    filename = f"raw/sales_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    s3.put_object(
        Bucket=SOURCE_BUCKET,
        Key=filename,
        Body=output.getvalue(),
        ContentType='text/csv'
    )
    print(f"✅ Generated & uploaded: s3://{SOURCE_BUCKET}/{filename}")
    return {'statusCode': 200, 'body': f'Uploaded {filename}'}
