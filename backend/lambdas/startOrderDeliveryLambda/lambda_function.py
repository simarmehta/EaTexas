import json
import boto3
from datetime import datetime, timedelta
import pytz

def get_current_time_ny():
    ny_timezone = pytz.timezone('America/New_York')
    current_time_ny = datetime.now(ny_timezone).strftime('%Y-%m-%d %H:%M:%S')
    return current_time_ny

def send_update_query_to_queue(update_query):
    sqs = boto3.client('sqs', region_name='us-east-1')  # Replace 'YOUR_REGION' with your AWS region
    queue_url = 'https://sqs.us-east-1.amazonaws.com/944218954103/updateQueries'  # Replace 'YOUR_SQS_QUEUE_URL' with your SQS queue URL

    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=update_query
        )
        print('Update query sent to the SQS queue')
    except Exception as e:
        print('Error sending update query to SQS:', e)
        raise e

def lambda_handler(event, context):
    delivery_person_id = event.get('delivery_person_id')
    order_id = event.get('order_id')
    current_time_ny = get_current_time_ny()

    # Construct the update query for the orders table with current time in NY and status as "Out For Delivery"
    update_query = f'''
        UPDATE orders 
        SET 
            delivery_person_email = '{delivery_person_id}',
            delivery_start_time = '{current_time_ny}',
            status = 'Out For Delivery'
        WHERE 
            order_id = '{order_id}';
    '''

    try:
        send_update_query_to_queue(update_query)
        payload = event  # Pass the same event to the other Lambda function
        lambda_client = boto3.client('lambda')
        function_name = 'removeOrderFromAvailableDeliveryPersonnel'
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',
            Payload=json.dumps(event)
        )
        return {'statusCode': 200, 'body': json.dumps({'message': 'Update query sent to the SQS queue'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': f'Error processing event: {str(e)}'})}
