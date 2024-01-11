
import boto3

def lambda_handler(event, context):
    # Replace 'YOUR_CLUSTER_ARN' with the actual ARN of your Aurora cluster
    cluster_arn = 'arn:aws:rds:us-east-1:944218954103:cluster:database-3'  
    sql_statement = "CREATE DATABASE YourDatabaseName"

    rds_data = boto3.client('rds-data')

    try:
        response = rds_data.execute_statement(
            secretArn='arn:aws:secretsmanager:us-east-1:944218954103:secret:rds-secret-FGmJz7',  # ARN of the AWS Secrets Manager secret containing your Aurora credentials
            resourceArn=cluster_arn,
            sql=sql_statement
        )
        print("Database created successfully:", response)
        return {
            'statusCode': 200,
            'body': 'Database created successfully'
        }
    except Exception as e:
        print("Error creating database:", e)
        return {
            'statusCode': 500,
            'body': 'Error creating database'
        }
    # Your SQL statement for table creation
    sql_statement = "CREATE TABLE YourTableName (id INT NOT NULL, name VARCHAR(100), PRIMARY KEY (id))"

    rds_data = boto3.client('rds-data')

    try:
        response = rds_data.execute_statement(
            secretArn='LrKBliv0z5nCCvVcPtje9HPQ6CExyylgooox2IEc',  # ARN of the AWS Secrets Manager secret containing your Aurora credentials
            resourceArn=cluster_arn,
            sql=sql_statement,
            database='YourDatabaseName'  # Name of your database in Aurora
        )
        print("Table created successfully:", response)
        return {
            'statusCode': 200,
            'body': 'Table created successfully'
        }
    except Exception as e:
        print("Error creating table:", e)
        return {
            'statusCode': 500,
            'body': 'Error creating table'
        }

