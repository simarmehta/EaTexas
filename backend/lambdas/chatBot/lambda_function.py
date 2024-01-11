import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging
import base64
import uuid
import re

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

bucket_name = 'user-images-upload'
file_name = 'image.png'

def store_image(image_data):
    s3_client = boto3.client('s3')
    s3_client.put_object(Bucket=bucket_name, Key=file_name, Body=image_data)
    
def get_labels():
    rekognition = boto3.client('rekognition')
    response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': file_name}},
            MaxLabels=10,
            MinConfidence=85
        )
    logger.info(response)
    labels = [label['Name'].lower() for label in response['Labels']]
    
    return labels

def send_message(connection_id, labels):
    sqs = boto3.client("sqs")

    # Convert list to string
    message_to_send = {
        'Cuisines': ', '.join(labels),
        'ConnectionId': connection_id
    }
    
    message_to_send = json.dumps(message_to_send)
    # Log the message
    logger.info(f"message: {message_to_send}")

    sqs_p = sqs.get_queue_url(QueueName='msgSQS.fifo').get('QueueUrl')
    message_group_id = "foodRecommend"
    message_deduplication_id = str(uuid.uuid4())
    try:
        # Send the message
        response = sqs.send_message(
            QueueUrl=sqs_p,
            MessageBody=message_to_send,
            MessageGroupId=message_group_id,
            MessageDeduplicationId=message_deduplication_id
        )
        message_status = f"Message sent! Message ID: {response['MessageId']}"
        return message_status

    except Exception as e:
        error_message = f"An error occurred: {e}"
        return error_message
    
def lambda_handler(event, context):
    try:
        # Parse the JSON body from the event
        connection_id = event.get("requestContext", {}).get("connectionId")
        body = json.loads(event['body'])
        body = body['body']
        
        logger.info(body)
        # Extract fields from the body
        userMessage = body.get('text', '')
        sender = body.get('sender', '')
        base64Image = body.get('image', '')
        cleaned_mail = sender.split('@')[0]
        print(cleaned_mail)

        logger.info(f"user message:{userMessage}")
        
        msg = []
        botResponse = ""
        statusCode = 200
        # Check if the text message is present
        if userMessage:
            client = boto3.client('lex-runtime')
            # Send the message to Lex (assuming Lex handles only text)
            lex_msg = client.post_text(botName="GetRestaurants", botAlias="version_one", userId=cleaned_mail, inputText=userMessage)
            logger.info(lex_msg)
            # Check if 'message' key exists in the response from Lex
            if 'message' not in lex_msg:
                raise ValueError("No 'message' returned from Lex")
            
            if lex_msg['messageFormat'] == "PlainText":
                msg = [lex_msg['message']]
                
            else:
                message_content = json.loads(lex_msg['message'])
                logger.info(message_content)
                
                if isinstance(message_content.get('messages'), list):
                    msg = [i['value'] for i in message_content['messages']]
            
            botResponse = msg
            statusCode = 200
        # Process the base64 image if present
        if base64Image:
            # Decode and process the image here
            base64Image = base64Image.split(',')[1]
            image_data = base64.b64decode(base64Image)
            logger.info(f"image_data: {image_data}")
            
            #store the image 
            store_image(image_data)
            
            #get the label from rekognition
            labels = get_labels()
            logger.info(f"labels: {labels}")
            
            #send message to sqs
            if labels: 
                response = send_message(connection_id, labels)
                logger.info(response)
                if "Message sent!" in response:
                    botResponse = f"I will output the food recommendation for your preference ({labels})!"
                else:
                    botResponse = response  
            else:
                botResponse = "Please provide an image or text for analysis."
            
            statusCode = 200
            
        if not userMessage and not base64Image:
            raise ValueError("Missing 'text' and 'image' in the event data")
           

    except ValueError as ve:
        # Handle missing data or validation errors
        botResponse = f"Error: {str(ve)}"
        statusCode = 400  # Bad request

    except (BotoCoreError, ClientError) as error:
        # Handle AWS client related errors
        botResponse = "Sorry, we encountered an error processing your request."
        statusCode = 500  # Internal Server Error

    except Exception as e:
        # Handle other unforeseen errors
        logger.info(f"exception:{e}")
        botResponse = "An unexpected error occurred."
        statusCode = 500

    # Create the response message
    responseMessage = {
        'sender': 'bot',
        'text': botResponse,
    }
    
    api_gateway_management_api = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url="https://gnzcvg3d4l.execute-api.us-east-1.amazonaws.com/test"
    )
    
    try:
        api_gateway_management_api.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(responseMessage)
        )
    except ClientError as e:
        print("Error sending message to client:", e)


    return {
        'statusCode': statusCode
    }

