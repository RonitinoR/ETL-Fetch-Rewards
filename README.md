# Fetch Rewards
# ETL from SQS to PostgreSQL

## Overview

This project demonstrates an ETL(Extract, Transform and Load) process that: 

1. Reads `user_logins` data which is in JSON format, from an AWS SQS (Simple Queue Service) Queue.
2. Masks the personal identifying information (pii).
3. Transforms and then stores the data back into the PostgreSQL database.

The process is run locally using Docker and LocalStack to simulate the AWS services.

## Prerequisites

Before running the ETL process, ensure the following prerequisites are installed:

1. Docker: To create a local environment with the necessary services.
2. Docker compose.
3. `awscli-local`: If not installed, you can install it using the command `pip install awscli-local`.
4. PostgreSQL client (`psql`).

## Setup

1. **Clone the repository** to your local desktop:
   ```sh
   git clone <repository-URL>
   cd <repository-directory>
   
2. Make sure Docker is running.
3. Make sure you have aws cli installed. 

## Running the ETL Process

1. Open a terminal or command prompt.
2. Navigate to the directory where you cloned the repository.
3. Set up your virtual environment by running the below code.

        python3 -m venv venv
        source venv/bin/activate

4. Make sure the `reuirements.txt` file consisting of the library installations required to run script by using the command:

        pip install -r requirements.txt
   
5. Run the following command to build and run the docker containers:

         docker-compose up 

*Note*: Before running the above command make sure the docker compose yaml file is correct consisting of the proper image urls.

This will create a local environment with AWS services and a PostgreSQL database.

6. Open another terminal or command prompt and navigate to the same directory.
7. Run the ETL script by executing the following command:

          python fetch.py

The script will read user login data from the SQS Queue, mask sensitive information like IP addresses and device IDs, and store the masked data into the PostgreSQL database.

## Checking the Database

To verify whether the `user_logins` table is succesfully loaded to postgreSQL database, you need to connect to the database by running the following commands:

        psql -d postgres -U postgres -p 5433 -h localhost -W

        SELECT * FROM user_logins;

## Thought Process

1. **Data Masking**: SHA-256 hashing is used in the script to mask `device_id` and `ip` fields while allowing for duplicate detection.
2. **Error Handling**: To handle the exceptions while receiving SQS messages, implemented retries with exponential backoff.
3. **Context Managers**: Ensured proper handling of database connection through context managers.

## Future Improvements

1. **Scalability**: For larger dataset operations message batching and parallel processing can be implemented.
2. **Deployment**: This application can be deployed on cloud platoforms such as AWS ECS or Kubernetes by containerizing it.
3. **Monitoring**: To have better visiblity and error tracking, logging and monitoring can be added.

## Troubleshooting

If you encounter any issues while running the ETL process, make sure Docker is running and all prerequisites are installed correctly.
