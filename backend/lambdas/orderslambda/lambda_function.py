import json
import boto3

def get_order_ids(user_id):
    lambda_client = boto3.client('lambda')
    function_name = 'getOrdersForDeliveryPersonnelFromAvailableDeliveryPersonnel'  # Replace with your Lambda function name

    payload = {
        'user_id': user_id
    }

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    return json.loads(response['Payload'].read().decode('utf-8'))

def get_order_details(order_id):
    lambda_client = boto3.client('lambda')
    function_name = 'getOrderDetailsBasedOnOrderIdWithCache'  # Replace with your Lambda function name

    payload = {
        'order_id': order_id
    }

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    payload = response['Payload'].read().decode('utf-8')

    return json.loads(payload)

def lambda_handler(event, context):
    print(event['queryStringParameters']['user_id'])
    user_id = event['queryStringParameters']['user_id']
    response_body = get_order_ids(user_id)  # Call Lambda function to get order_ids based on user_id
    order_ids = json.loads(response_body['body'])[0]['order_ids']
    orders = []
    order_ids_list = order_ids.split(',')
    for order_id in order_ids_list:
        order_details = get_order_details(order_id)  # Call Lambda function to get order details
        orders.append(order_details)
    
    return {
        'statusCode': 200,
        'body': json.dumps(orders)
    }