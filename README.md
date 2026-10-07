# 🚀 AWS Lambda Serverless Data Pipeline
### A fully automated, event-driven sales data pipeline built on AWS Lambda

![AWS](https://img.shields.io/badge/AWS-Lambda-orange)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-blue)
![S3](https://img.shields.io/badge/AWS-S3-green)
![Region](https://img.shields.io/badge/Region-ap--south--1-yellow)

---

## 📌 Project OverviewT

This project demonstrates a **fully serverless, event-driven data pipeline** built entirely on AWS Lambda. No servers. No manual steps. No CSV files needed.

When triggered, the pipeline:
1. **Generates** mock sales data automatically
2. **Validates** the file structure
3. **Transforms** and stores the data
4. **Audits** every database change
5. **Emails** a daily summary report

All steps fire **automatically** — each Lambda triggers the next one.

---

## 🏗️ Architecture

```
EventBridge (cron)
      │
      ▼
Lambda 0 — Data Generator
      │  generates CSV → uploads to S3 (raw/)
      ▼
S3 Trigger
      │
      ▼
Lambda 1 — File Validator
      │  validates CSV columns & rows
      ├── ✅ valid   → SQS Queue
      └── ❌ invalid → SNS Alert Email
                │
                ▼
          Lambda 2 — Transformer
                │  transforms rows → DynamoDB + S3 (processed/)
                ▼
          DynamoDB Stream
                │
                ▼
          Lambda 3 — Audit Logger
                │  logs every INSERT / MODIFY / REMOVE → CloudWatch

EventBridge (daily cron)
      │
      ▼
Lambda 4 — Daily Reporter
      reads DynamoDB → aggregates → emails report via SNS
```

---

## ⚙️ AWS Services Used

| Service | Purpose |
|---|---|
| **AWS Lambda** | 5 serverless functions — core compute |
| **Amazon S3** | Source bucket (raw CSV) + Destination bucket (processed JSON) |
| **Amazon DynamoDB** | NoSQL database storing all sale records |
| **Amazon SQS** | Message queue between validator and transformer |
| **Amazon SNS** | Email alerts on errors + daily report delivery |
| **Amazon EventBridge** | Cron schedule to trigger daily reporter |
| **Amazon CloudWatch** | Logs and monitoring for all Lambda functions |
| **AWS IAM** | Execution roles and permissions for each Lambda |

---

## 🔧 Lambda Functions

### Lambda 0 — `sales-data-generator`
- **Trigger:** Manual / EventBridge
- **What it does:** Generates 10 random sales rows and uploads a CSV to S3
- **Key concepts:** `boto3 S3 put_object`, CSV generation in memory, no file system needed
- **Environment variables:**
  - `SOURCE_BUCKET` = `sales-source-name`

---

### Lambda 1 — `sales-file-validator`
- **Trigger:** S3 PUT event (`raw/*.csv`)
- **What it does:** Reads the uploaded CSV, checks required columns and row count
  - ✅ Valid → sends message to SQS
  - ❌ Invalid → sends alert email via SNS
- **Key concepts:** S3 event trigger, CSV validation, SQS `send_message`, SNS `publish`
- **Environment variables:**
  - `QUEUE_URL` = SQS queue URL
  - `SNS_ARN` = SNS topic ARN

---

### Lambda 2 — `sales-transformer`
- **Trigger:** SQS (`valid_files_queue`)
- **What it does:** Reads validated CSV from S3, transforms each row, saves to DynamoDB and writes processed JSON to destination S3
- **Key concepts:** SQS batch trigger, DynamoDB `put_item`, data transformation, `total_amount` calculation
- **Environment variables:**
  - `DEST_BUCKET` = `sales-processed-name`
  - `DYNAMO_TABLE` = `sales_records`

---

### Lambda 3 — `sales-audit-logger`
- **Trigger:** DynamoDB Streams (New and old images)
- **What it does:** Listens to every INSERT / MODIFY / REMOVE on the DynamoDB table and logs a structured audit entry to CloudWatch
- **Key concepts:** Change Data Capture (CDC), DynamoDB stream parsing, structured logging
- **No environment variables needed**

---

### Lambda 4 — `sales-daily-reporter`
- **Trigger:** EventBridge cron — `cron(0 8 * * ? *)` — every day at 8AM UTC
- **What it does:** Scans DynamoDB, aggregates revenue by region and product, formats a report and sends it via SNS email
- **Key concepts:** DynamoDB `scan`, data aggregation, EventBridge schedule, SNS email delivery
- **Environment variables:**
  - `DYNAMO_TABLE` = `sales_records`
  - `SNS_ARN` = SNS topic ARN

---

## 🗂️ AWS Resources Created

| Resource | Name | Type |
|---|---|---|
| S3 Bucket (source) | `sales-source-name` | Amazon S3 |
| S3 Bucket (destination) | `sales-processed-name` | Amazon S3 |
| DynamoDB Table | `sales_records` | Partition key: `sale_id` (String) |
| SQS Queue | `valid_files_queue` | Standard Queue |
| SNS Topic | `sales_alerts` | Standard Topic |
| EventBridge Rule | `daily-sales-report-schedule` | Cron schedule |

---

## 📊 Data Flow

**Step 1** — Lambda 0 generates this CSV in memory:

```
sale_id   product    region   quantity   unit_price   sale_date
S001      Laptop     North    2          850.00       2026-09-16
S002      Mouse      South    3          25.50        2026-09-16
...
```

**Step 2** — Lambda 1 validates headers and row count

**Step 3** — Lambda 2 transforms and enriches each row:

```json
{
  "sale_id": "S001",
  "product": "Laptop",
  "region": "North",
  "quantity": 2,
  "unit_price": "850.0",
  "total_amount": "1700.0",
  "sale_date": "2026-09-16",
  "processed_at": "2026-09-16T19:44:01",
  "source_file": "raw/sales_20260916_194401.csv",
  "status": "processed"
}
```

**Step 4** — Lambda 3 logs every DynamoDB write to CloudWatch

**Step 5** — Lambda 4 emails this report daily:

```
╔══════════════════════════════════════════════╗
   📊 DAILY SALES REPORT — 2026-09-16
╚══════════════════════════════════════════════╝

  Total Records   : 10
  Total Revenue   : $14,436.00
  Top Region      : North ($11,946.00)
  Top Product     : Laptop ($8,500.00)

REVENUE BY REGION          REVENUE BY PRODUCT
  North  : $11,946.00        Laptop       : $8,500.00
  East   : $1,740.00         Monitor      : $3,840.00
  West   : $540.00           Headphones   : $750.00
  South  : $210.00           Laptop Stand : $560.00
```

---

## 🧠 Concepts Learned

| Concept | Where Used |
|---|---|
| S3 event trigger | Lambda 1 |
| SQS trigger + message passing | Lambda 1 → Lambda 2 |
| DynamoDB Streams / Change Data Capture | Lambda 3 |
| EventBridge cron schedule | Lambda 4 |
| Environment variables | All Lambdas |
| IAM execution roles and policies | All Lambdas |
| Error handling + SNS alerts | Lambda 1 |
| boto3 S3 get/put | Lambda 0, Lambda 2 |
| boto3 DynamoDB put_item + scan | Lambda 2, Lambda 4 |
| CloudWatch Logs | All Lambdas |
| Data transformation + enrichment | Lambda 2 |
| Data aggregation + reporting | Lambda 4 |
| Serverless event-driven architecture | Entire pipeline |

---

## 🚀 How to Run This Project

### Prerequisites
- AWS Account with Console access
- Region: `ap-south-1` (Mumbai)

### Step 1 — Create Infrastructure

```
S3 Bucket  : sales-source-name       (source)
S3 Bucket  : sales-processed-name    (destination)
DynamoDB   : sales_records             (partition key: sale_id)
SQS Queue  : valid_files_queue         (Standard)
SNS Topic  : sales_alerts              (subscribe your email)
```

### Step 2 — Deploy Lambda Functions
Deploy all 5 functions with **Python 3.12** runtime. Add environment variables and IAM policies as listed above.

### Step 3 — Add Triggers

```
Lambda 1 ← S3 trigger       (Bucket: sales-source-name, Prefix: raw/, Suffix: .csv)
Lambda 2 ← SQS trigger      (Queue: valid_files_queue, Batch size: 1)
Lambda 3 ← DynamoDB Stream  (Table: sales_records, Starting position: Latest)
Lambda 4 ← EventBridge      (cron(0 8 * * ? *))
```

### Step 4 — Run the Pipeline
Go to `sales-data-generator` Lambda → **Test** tab → click **Test**

Watch the pipeline fire automatically end to end! 🚀

### Step 5 — Verify Results
- DynamoDB `sales_records` → 10 records written
- S3 `sales-processed-name/processed/` → JSON file created
- CloudWatch `/aws/lambda/sales-audit-logger` → audit logs
- Your email inbox → daily sales report

---

## 📁 Project Structure

```
aws-lambda/
├── sales-data-generator/
│   └── lambda_function.py
├── sales-file-validator/
│   └── lambda_function.py
├── sales-transformer/
│   └── lambda_function.py
├── sales-audit-logger/
│   └── lambda_function.py
├── sales-daily-reporter/
│   └── lambda_function.py
└── README.md
```

---

## 👨‍💻 Author

**Kotesh**
- Built on AWS Lambda (`ap-south-1`)
- Completed as a hands-on AWS learning project
- All infrastructure created manually via AWS Console

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
