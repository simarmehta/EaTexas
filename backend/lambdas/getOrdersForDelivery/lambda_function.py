import json
import datetime
import boto3
import logging


lambda_client = boto3.client('lambda', region_name='us-east-1')

def lambda_handler(event, context):
    print(event)
    query_string_parameters = event.get('queryStringParameters')
    user_id = query_string_parameters.get('user_id') if query_string_parameters else None
    key= f"Order_User_{user_id}"
    
    print(key)
    if user_id:
        # Attempt to get data from the cache using order_id
        cache_response = invoke_lambda_function('getfromcacahe', {'key': key})
        print(cache_response)
        if cache_response:
            print("Data Fetched from Cache")
            # Data retrieved from cache
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps(cache_response)
            }
        
        # Data not found in cache, fetch it from the database
        db_response = invoke_lambda_function('NodeGetOrdersOnUserId', {'emailId': user_id})
        print(db_response)
        if db_response and db_response['statusCode'] == 200:
            # Set data to cache
            set_to_cache_response = invoke_lambda_function('setToCache', {'key': key, 'value': db_response['body']})
            print("Data Set to Cache")

            if set_to_cache_response:
                return {
                    'statusCode': 200,
                    'body': db_response['body']
                }

    # Construct a JSON response
    response = {
        'statusCode': 500,
        'body': "User_id not found"
    }

    return response

def invoke_lambda_function(function_name, payload):
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode('utf-8')
        )
        return json.loads(response['Payload'].read().decode('utf-8'))
    except Exception as e:
        print(f'Error invoking {function_name} Lambda:', e)
        return None
        
    
    
