# import json
# import boto3

# def lambda_handler(event, context):
#     order_id = event.get('order_id')
    
#     # Construct the update query for the orders table
#     update_query = f"UPDATE orders SET status = 'Delivered' WHERE order_id = '{order_id}'"
#         # Initialize Lambda client
#     lambda_client = boto3.client('lambda')

#     # Name of the Lambda function to be invoked
#     invoked_function_name = 'getOrderDetailsBasedOnOrderIdWithCache'  # Replace with your second Lambda function's name

#     # Construct the payload to send to the second Lambda function
#     payload_to_second_function = {
#         'order_id': order_id
#     }

#     try:
#         # Invoke the second Lambda function
#         response = lambda_client.invoke(
#             FunctionName=invoked_function_name,
#             InvocationType='RequestResponse',  # Synchronous invocation
#             Payload=json.dumps(payload_to_second_function)
#         )

#         # Read the response from the second Lambda function
#         response_payload = json.loads(response['Payload'].read().decode("utf-8"))
#         order_details = response_payload.get('body')

#         # Print order details
#         print("Order Details:", order_details)
    
#     # Send the update query payload to an SQS queue
#     sqs_client = boto3.client('sqs')
#     queue_url = 'https://sqs.us-east-1.amazonaws.com/944218954103/updateQueries'  # Replace with your SQS queue URL
    
#     payload = {
#         'query': update_query
#     }

#     try:
#         # Send the payload to the SQS queue
#         sqs_client.send_message(
#             QueueUrl=queue_url,
#             MessageBody=json.dumps(payload)
#         )
        
#         return {
#             'statusCode': 200,
#             'body': json.dumps({'message': 'Update query sent to the SQS queue'}),
#         }
    
#     except Exception as e:
#         return {
#             'statusCode': 500,
#             'body': json.dumps({'error': 'Error sending query to SQS queue: ' + str(e)}),
#         }


import json
import boto3

def lambda_handler(event, context):
    order_id = event.get('order_id')
    
    # Construct the update query for the orders table
    update_query = f"UPDATE orders SET status = 'Delivered' WHERE order_id = '{order_id}'"

    # Initialize Lambda client
    lambda_client = boto3.client('lambda')
    invoked_function_name = 'getOrderDetailsBasedOnOrderIdWithCache'

    # Construct the payload for the second Lambda function
    payload_to_second_function = {'order_id': order_id}

    # Initialize SQS client
    sqs_client = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/944218954103/updateQueries'

    try:
        # Invoke the second Lambda function
        response = lambda_client.invoke(
            FunctionName=invoked_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload_to_second_function)
        )

        # Read and print the response from the second Lambda function
        response_payload = json.loads(response['Payload'].read().decode("utf-8"))
        # response_payload = json.loads(response['Payload'].read().decode("utf-8"))
        print("Type of response_payload:", type(response_payload))
        print("Content of response_payload:", response_payload)
        order_details_list = json.loads(response_payload)  # Parsing the JSON string

        # Assuming we're interested in the first order details
        if order_details_list:
            order_details = order_details_list[0]  # Access the first order in the list
            print("Order Details:", order_details)
        else:
            print("No order details found.")

        if order_details_list:
            order_details = order_details_list[0]  # First order in the list
            customer_email = order_details.get('customer_email')  # Extract customer email from order details
            delivery_address = order_details.get('delivery_address')  # Extract delivery address from order details

            # Initialize SES client
            ses_client = boto3.client('ses', region_name='us-east-1')

            # Email content
            subject = 'Your Order Has Been Delivered'
            body_text = (f"Dear Customer,\n\n"
                         f"Your order (Order ID: {order_id}) has been successfully delivered to {delivery_address}.\n\n"
                         f"Thank you for choosing us!\n\n"
                         f"Best regards,\nYour Service Team")

            # Send the email using SES
            ses_client.send_email(
                Source='ccprojectcp@gmail.com',  # Replace with your SES verified email
                Destination={'ToAddresses': [customer_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body_text}}
                }
            )

        else:
            print("No order details found.")

    except Exception as e:
        print(f"Error invoking Lambda function: {str(e)}")

    try:
        # Send the update query to the SQS queue
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody= update_query
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Update query sent to the SQS queue'}),
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error sending query to SQS queue: {str(e)}'}),
        }
