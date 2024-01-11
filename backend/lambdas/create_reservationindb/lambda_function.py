# import json
# import boto3
# from datetime import datetime
# from uuid import uuid4

# def lambda_handler(event, context):
#     print(event)
#     # Initialize a DynamoDB client
#     dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

#     # Specify your table name
#     table = dynamodb.Table('reservation_table')
#     restaurant_table = dynamodb.Table('table_restaurant')

#     # Generate a unique ID for the new entry
#     unique_id = str(uuid4())

#     # Extract details from the event (assuming they are passed in the event)
#     for record in event['Records']:
#         # Parse the message body
#         message_body = json.loads(record['body'])

#         # Now you can extract the individual fields
#         rest_id = message_body['rest_id']
#         email = message_body['email']
#         people = message_body['people']
#         date = message_body['date']
#         time = message_body['time']

#     # Insert the item into the DynamoDB table
#     response = table.put_item(
#         Item={
#             'id': unique_id,
#             'rest_id': rest_id,
#             'email': email,
#             'people': people,
#             'date': date,
#             'time': time
#         }
#     )
#     restaurant_response = restaurant_table.get_item(
#         Key={'id': rest_id}
#     )
#     restaurant_item = restaurant_response.get('Item', {})
#     restaurant_name = restaurant_item.get('name', 'Unknown Restaurant')
#     restaurant_address = restaurant_item.get('address', 'Address not available')


#     # You can add additional error handling and logging here based on the response

#     # Return the inserted item details
# subject = 'Your Reservation Details at ' + restaurant_name
#     body_text = (f"Dear Customer,\n\n"
#                  f"You have successfully made a reservation at {restaurant_name}.\n"
#                  f"Address: {restaurant_address}\n"
#                  f"Reservation Details:\n"
#                  f" - People: {people}\n"
#                  f" - Date: {date}\n"
#                  f" - Time: {time}\n\n"
#                  f"Best regards,\n{restaurant_name}")

#     # Send the email
#     ses_client.send_email(
#         Source=sender_email,
#         Destination={'ToAddresses': [email]},
#         Message={
#             'Subject': {'Data': subject},
#             'Body': {'Text': {'Data': body_text}}
#         }
#     )

#     # Return the inserted item details
#     return {
#         'statusCode': 200,
#         'body': json.dumps({
#             'id': unique_id,
#             'rest_id': rest_id,
#             'email': email,
#             'people': people,
#             'date': date,
#             'time': time,
#             'restaurant_name': restaurant_name,
#             'restaurant_address': restaurant_address
#         })
#     }


import json
import boto3
from uuid import uuid4

def lambda_handler(event, context):
    print(event)
    # Initialize DynamoDB and SES clients
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    ses_client = boto3.client('ses', region_name='us-east-1')

    # DynamoDB tables
    table = dynamodb.Table('reservation_table')
    restaurant_table = dynamodb.Table('table_restaurant')

    # Sender's email - must be verified in Amazon SES
    sender_email = 'ccprojectcp@gmail.com'

    # Process each record from the event
    for record in event['Records']:
        unique_id = str(uuid4())  # Generate a unique ID for the new entry
        message_body = json.loads(record['body'])  # Parse the message body

        # Extract individual fields
        rest_id = message_body['rest_id']
        email = message_body['email']
        people = message_body['people']
        date = message_body['date']
        time = message_body['time']

        # Insert into DynamoDB table
        response = table.put_item(
            Item={
                'id': unique_id,
                'rest_id': rest_id,
                'email': email,
                'people': people,
                'date': date,
                'time': time
            }
        )
        # Fetch restaurant details
        restaurant_response = restaurant_table.get_item(Key={'id': rest_id})
        print(restaurant_response)
        restaurant_item = restaurant_response.get('Item', {})
        restaurant_name = restaurant_item.get('name', 'Unknown Restaurant')
        restaurant_address = restaurant_item.get('full_address', 'Address not available')

        # Construct email content
        subject = 'Your Reservation Details at ' + restaurant_name
        body_text = (f"Dear Customer,\n\n"
                     f"You have successfully made a reservation at {restaurant_name}.\n"
                     f"Address: {restaurant_address}\n"
                     f"Reservation Details:\n"
                    
                     f" - People: {people}\n"
                     f" - Date: {date}\n"
                     f" - Time: {time}\n\n"
                     f"Best regards,\n{restaurant_name}")

        # Send the email
        ses_client.send_email(
            Source=sender_email,
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )

    # Return a response
    return {
        'statusCode': 200,
        'body': json.dumps('Reservations processed and emails sent.')
    }
