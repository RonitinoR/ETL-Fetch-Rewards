import os
import json
import time
import boto3
import psycopg2
import hashlib
from datetime import datetime
from botocore.exceptions import ClientError, EndpointConnectionError

#Fetching the configurations
queue_url = 'http://localhost:4566/000000000000/login-queue'
database_url = 'postgresql://postgres:postgres@localhost:5432/postgres'

def pii(value):
    return hashlib.sha256(value.encode()).hexdigest()

def sqs_message():
    sqs = boto3.client('sqs', endpoint_url='http://localhost:4566')
    for attempt in range(5):
        try:
            print("Attempting to receive messages...")
            response = sqs.receive_message(
                QueueUrl = queue_url,
                MaxNumberOfMessages = 10,
                WaitTimeSeconds = 5
            )
            print(f"Response from SQS: {response}")
            return response.get('Messages', [])
        except (ClientError, EndpointConnectionError) as e: # type: ignore
            print(f"Attempt {attempt + 1}: Failed to receive messages - {e}")
            time.sleep(2 ** attempt)  # type: ignore # Exponential backoff
    raise RuntimeError("Failed to receive messages after multiple attempts")


def transform_message(message):
    body = json.loads(message['Body'])
    user_id = body['user_id']
    device_type = body['device_type']
    masked_ip = pii(body['ip'])
    masked_device_id = pii(body['device_id'])
    locale = body['locale']
    app_version = int(body['app_version'])
    create_date = datetime.strptime(body['create_date'], '%Y-%m-%d').date()

    return (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)

def write_to_postgresql(records):
    con = psycopg2.connect(database_url)
    cur = con.cursor()
    cur.executemany("""
        INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, records)
    
    con.commit()
    cur.close()
    con.close()

def main():
    try:
        messages = sqs_message()
        if not messages:
            print("No messages to process.")
        records = [transform_message(msg) for msg in messages]
        write_to_postgresql(records)
        print(f"Processed {len(records)} records.")
    
    except Exception as e:
        print("Failed to process messages - {e}")

if __name__ == '__main__':
    main()