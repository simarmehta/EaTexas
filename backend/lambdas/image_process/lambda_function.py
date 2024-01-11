# import boto3
# import json
# import os
# import uuid
# import base64

# s3_client = boto3.client('s3')

# def lambda_handler(event, context):
#     try:
#         # Parse the image data
#         image_data = event['body']
#         if 'isBase64Encoded' in event and event['isBase64Encoded']:
#             image_data = base64.b64decode(image_data)

#         # Define the S3 bucket and generate a unique file name
#         bucket_name = 'user-images-upload'  # Replace with your S3 bucket name
#         file_name = str(uuid.uuid4()) + '.jpg'  # Assumes the image is a JPEG

#         # Upload the image to S3
#         s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=image_data)

#         # Construct the URL of the uploaded image
#         region_name = s3_client.meta.region_name
#         image_url = f'https://{bucket_name}.s3.us-east-1.amazonaws.com/{file_name}'

#         # Return the URL in the response
#         return {
#             'statusCode': 200,
#             'body': json.dumps({'imageUrl': image_url})
#         }

#     except Exception as e:
#         print(e)
#         return {
#             'statusCode': 500,
#             'body': json.dumps({'error': 'Error uploading image'})
#         }


import boto3
import json
import os
import uuid
import base64
import logging
from botocore.exceptions import ClientError

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Parse the JSON body and extract the base64 encoded image data
        logger.info(event)
        image_data = json.loads(event['body'])['image']
        image_data = base64.b64decode(image_data)

        # Define the S3 bucket and generate a unique file name
        bucket_name = 'user-images-upload'  # Use environment variable for the bucket name
        file_name = str(uuid.uuid4()) + '.jpg'  # Assumes the image is a JPEG

        # Upload the image to S3
        s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=image_data)

        # Construct the URL of the uploaded image
        region_name = s3_client.meta.region_name
        image_url = f'https://{bucket_name}.s3.{region_name}.amazonaws.com/{file_name}'

        # Return the URL in the response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # CORS header, adjust as needed
            },
            'body': json.dumps({'imageUrl': image_url})
        }

    except ClientError as e:
        logger.error("ClientError: %s", e)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # CORS header, adjust as needed
            },
            'body': json.dumps({'error': 'Error uploading image to S3'})
        }
    except Exception as e:
        logger.error("Exception: %s", e)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # CORS header, adjust as needed
            },
            'body': json.dumps({'error': 'Error processing the image'})
        }
