import json
import boto3
from botocore.exceptions import ClientError
import logging
import random
import requests
from boto3.dynamodb.types import TypeDeserializer


apigateway_management_client = boto3.client('apigatewaymanagementapi', endpoint_url='https://gnzcvg3d4l.execute-api.us-east-1.amazonaws.com/test')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def search(cuisine, zipcode):
    es_host='search-domain1-sa27yjmuybcvsq5dwmq456qsbu.us-east-1.es.amazonaws.com'
    region = 'us-east-1' 
    service = 'es'
    username = 'master'
    password = 'Master@123'
    url = f'https://{es_host}/rest_index/_search'
    query = {}
    query = {
        "size": 3,
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "query_string": {
                                    "default_field": "restaurant_category",
                                    "query": f"*{cuisine}*"
                                }
                            }
                        ]
                    }
                },
                "functions": [
                    {
                        "random_score": {"seed": random.randint(0, 1000)}
                    }
                ],
                "boost_mode": "replace"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Make the search request to Elasticsearch
    response = requests.post(url, auth=(username, password), headers=headers, data=json.dumps(query))

    # Check for request failure
    if response.status_code != 200:
        print(f"Failed to retrieve data: {response.content}")
        return []

    # Parse and return the hits (restaurants) from the response
    return response.json()["hits"]["hits"]

def get_resaurants_by_keys(ids):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'table_restaurant'
    
    table = dynamodb.Table(table_name)
    
    restaurants = []
    for id in ids:
        response = table.get_item(
            Key={
                'id': id
            }
        )
        item = response['Item']
        
        restaurants.append(item)
        
    return restaurants

def get_restaurants_and_menus(restaurant_ids):
    deserializer = TypeDeserializer()
    region_name = 'us-east-1'
    restaurant_table_name = 'table_restaurant'
    menu_items_table_name = 'menu_items'
    
    # Initialize a DynamoDB client
    dynamodb = boto3.client('dynamodb', region_name=region_name)
    restaurant_table = boto3.resource('dynamodb', region_name=region_name).Table(restaurant_table_name)
    
    combined_data = []
    
    for restaurant_id in restaurant_ids:
        # Fetch the restaurant details
        restaurant_response = restaurant_table.get_item(Key={'id': restaurant_id})
        restaurant = restaurant_response.get('Item', {})

        if restaurant:
            # Query the menu items for this restaurant using PartiQL
            statement = f"SELECT * FROM \"{menu_items_table_name}\" WHERE \"restaurant_id\" = '{restaurant_id}'"
            menu_response = dynamodb.execute_statement(Statement=statement)
            menu_items = menu_response.get('Items', [])

            
            # Convert the DynamoDB items to a regular dictionary
            menu_items = [deserializer.deserialize({'M': item}) for item in menu_items]
            # Add the menu items to the restaurant data
            restaurant['menu_items'] = menu_items
            
            # Append the combined data to the results list
            combined_data.append(restaurant)
    
    logger.debug(combined_data)
    return combined_data

def send_to_websocket(connection_id, message):
    try:
        # Convert the message to a JSON string
        message_json = json.dumps(message)

        # Post the message to the specified connection
        apigateway_management_client.post_to_connection(
            ConnectionId=connection_id,
            Data=message_json
        )
    except Exception as e:
        # Handle exceptions, which can occur if the connection is no longer available
        logger.info(f"Error sending message to WebSocket: {e}")
    
def lambda_handler(event, context):
    top_n = 3
    cuisine = ""
    location = ""
    connect_id = ""
    zipcode = ""
    logger.info(event)
    
    '''
    sqs = boto3.client('sqs')
    queue_url = sqs.get_queue_url(QueueName='msgSQS.fifo').get('QueueUrl')
    
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,  
        WaitTimeSeconds=5    
    )
    logger.info(f"response from sqs:{response}")
    
    messages = response.get('Messages', [])
    '''
    
    messages = event.get('Records', [])
    if messages:
        for message in messages:
            # Process each message
            body_str = message.get('body', '{}')
            body = json.loads(body_str)
            receipt_handle = message.get('receiptHandle', '')
    
            # Extract information from message, with defaults if keys are missing
            cuisine = body.get('Cuisines', 'Asian')  
            location = body.get('Location', 'texas')
            connect_id = body.get('ConnectionId', '')
            zipcode = body.get('Zipcode', '')
    
            # Log the extracted values (optional)
            logger.info(f" Cuisine: {cuisine}, connect_id: {connect_id}, Zipcode: {zipcode}")
    else:
        # No message in the sqs, set the cuisine to default
        cuisine = "Asian"
    
    logger.info(f"CUISINE: {cuisine}")
    # Search restaurant based on cuisine using Elastic Search
    restaurants_info = search(cuisine, zipcode)
    
    restaurant_id = [item['_source']['restaurant_id'] for item in restaurants_info]
    
    logger.info(f"restaurants_id:{restaurant_id}")
    #restaurant_info = get_resaurants_by_keys(restaurant_id)
    restaurant_info = get_restaurants_and_menus(restaurant_id)
    
    responseMessage = {
        'sender': 'foodRecommend',
        'text': json.dumps(restaurant_info),
    }
    
    logger.info(f"responseMessage:{responseMessage}")
    
   
    if connect_id:
         #Food recommendation with image
        send_to_websocket(connect_id, responseMessage)
    else:
            
        # Return response for Lambda execution
        return {
            'statusCode': 200,
            'body': json.dumps(restaurant_info)
        }
    
    return {'statusCode': 200}