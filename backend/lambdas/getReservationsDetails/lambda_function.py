# import json
# import boto3
# from boto3.dynamodb.conditions import Key

# # Initialize a DynamoDB client
# dynamodb = boto3.resource('dynamodb')

# def lambda_handler(event, context):
#     # Parse the email from the Lambda function input
#     email = event['email']
    
#     # Select the DynamoDB table
#     table = dynamodb.Table('reservation_table')
    
#     # Query the table for reservations associated with the email
#     response = table.query(
#         KeyConditionExpression=Key('email').eq(email)
#     )
    
#     # Get the items from the response
#     items = response.get('Items', [])
    
#     # Create a response object containing the reservations
#     reservations = {'reservations': items}
#     print(reservations)
#     # Send the reservations back to the frontend
#     return {
#         'statusCode': 200,
#         'headers': {
#             'Content-Type': 'application/json',
#             'Access-Control-Allow-Origin': '*'  # Required for CORS support to work
#         },
#         'body': json.dumps(reservations)
#     }


import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal


# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            # Convert decimal instances to float. Use str(o) if you want to convert to string
            return float(o)
        return super(DecimalEncoder, self).default(o)


def lambda_handler(event, context):
    # Parse the email from the Lambda function input
    email = event['email']
    
    # Select the DynamoDB table
    table = dynamodb.Table('reservation_table')
    
    # Scan the table with a filter expression for the email
    response = table.scan(
        FilterExpression=Attr('email').eq(email)
    )
    
    # Get the items from the response
    items = response.get('Items', [])
    
    # Create a response object containing the reservations
    reservations = {'reservations': items}
    print(reservations)
    
    # Send the reservations back to the frontend
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # Required for CORS support to work
        },
        
        'body': json.dumps(reservations, cls=DecimalEncoder)
    }
                           