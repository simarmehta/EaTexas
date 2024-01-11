import json
import boto3

def lambda_handler(event, context):
    print(event)
    sqs = boto3.client('sqs')
    update_queue_url = 'https://sqs.us-east-1.amazonaws.com/944218954103/updateQueries'
    order_prepared_queue = "https://sqs.us-east-1.amazonaws.com/944218954103/order_prepared_queue"

    try:
        # Extract the order_id from the SQS event
        order_id = int(event['Records'][0]['body'])
        # Construct the update query
        update_query = f"UPDATE Orders SET status = 'Preparing' WHERE order_id = {order_id}"
        # Send the update query to the updateQueries queue
        response = sqs.send_message(
            QueueUrl=update_queue_url,
            MessageBody=update_query
        )
        response = sqs.send_message(
            QueueUrl=order_prepared_queue,
            MessageBody=str(order_id)
        )
        print(f"Sent update query for order {order_id} to the queue 'updateQueries'")
        return {
            'statusCode': 200,
            'body': json.dumps('Update query sent successfully')
        }
    except Exception as e:
        print(str(e))
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }
