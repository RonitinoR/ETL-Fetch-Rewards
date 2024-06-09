import os
import json
import time
import boto3
import psycopg2
import hashlib
from datetime import datetime
from botocore.exceptions import ClientError, EndpointConnectionError

#Fetching the configurations for posgtgresql and localstack sqs queue URL
queue_url = 'http://localhost:4566/000000000000/login-queue'
database_url = 'postgresql://postgres:postgres@localhost:5432/postgres'

#defining a function to mask the personal indentifying information (pii)
def pii(value):
    return hashlib.sha256(value.encode()).hexdigest()

#defining sqs_message function to recieve and read the message from SQS queue
def sqs_message():
    sqs = boto3.client('sqs', endpoint_url='http://localhost:4566')
    for attempt in range(5):
        try:
            print("Attempting to receive messages...")
            response = sqs.receive_message(
                QueueUrl = queue_url,
                MaxNumberOfMessages = 100,
                VisibilityTimeout = 0,
                WaitTimeSeconds = 0
            )
            print(f"Response from SQS: {response}")
            return response.get('Messages', [])
        except (ClientError, EndpointConnectionError) as e: # type: ignore
            print(f"Attempt {attempt + 1}: Failed to receive messages - {e}")
            time.sleep(2 ** attempt)  # type: ignore # Exponential backoff
    raise RuntimeError("Failed to receive messages after multiple attempts")

#tranforming it into a format desired in the postgresql to load it back into it
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

#defining another function to write the changes done back into the posgres database
# Function to write records to PostgreSQL
def write_to_postgresql(records):
    with psycopg2.connect(database_url) as con:
        with con.cursor() as cur:
            cur.executemany("""
                INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, records)
            con.commit()

# main function consists of the entire code sequence and link between the function to run the code
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