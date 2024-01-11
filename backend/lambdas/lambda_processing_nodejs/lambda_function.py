import json
import boto3

def lambda_handler(event, context):
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    print(event)
    order_id = int(event['Records'][0]['body'])

    # Prepare the payload
    payload = json.dumps({'order_id': order_id})

    try:
        # Invoke the Lambda function
        response = lambda_client.invoke(
            FunctionName='selectOrders',
            InvocationType='RequestResponse',
            Payload=payload.encode('utf-8')
        )

        # Process the response
        response_payload = json.loads(response['Payload'].read())
        print("Response received from selectOrders function:", response_payload)

        # Parse the 'body' of the response
        orders = json.loads(response_payload['body'])
        
        

        # Assuming you are interested in the first order's restaurant_id
        if orders:
            restaurant_id = orders[0]['restaurant_id']
            print(restaurant_id)
        else:
            return {
                'statusCode': 404,
                'body': json.dumps('No orders found')
            }

        # Initialize a DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Specify the table name
        table = dynamodb.Table('table_restaurant')

        # Retrieve the item from DynamoDB
        restaurant_response = table.get_item(
            Key={
                'id': str(restaurant_id)
            }
        )

        # Check if item exists
        if 'Item' in restaurant_response:
            restaurant_data = restaurant_response['Item']
            
            print(restaurant_data['zip_code'])
            lambda_client = boto3.client('lambda', region_name='us-east-1')
            payload = json.dumps({'pincode': restaurant_data['zip_code']})
            print(payload)
            response = lambda_client.invoke(
                FunctionName='getAvailableDeliveryPersonnel',
                InvocationType='RequestResponse',
                Payload=payload.encode('utf-8')
            )
            
            # Process the response to get the delivery personnel ID
            response_payload = response['Payload'].read().decode("utf-8")
            response_payload = json.loads(response_payload)
            delivery_personnel_data = json.loads(response_payload['body'])
            
            # Assuming we want the first available delivery personnel
            if delivery_personnel_data:
                delivery_personnel_id = delivery_personnel_data[0]['deliverypersonnelid']
            else:
                # Handle the case where no delivery personnel is found
                return {
                    'statusCode': 404,
                    'body': json.dumps('No available delivery sda personnel found')
                }
                
            
            # Use the extracted delivery personnel ID in the next payload
            payload = json.dumps({'deliverypersonnelid': delivery_personnel_id, 'order_id': order_id})
            response = lambda_client.invoke(
                FunctionName='setDeliveryOrderToPersonnel',
                InvocationType='RequestResponse',
                Payload=payload.encode('utf-8')
            )
            print(payload)
            sqs = boto3.client('sqs', region_name='us-east-1')

            # Specify your SQS queue URL
            queue_url = 'https://sqs.us-east-1.amazonaws.com/944218954103/checkDeliveryPersonnelAssigned'
        
            # Assuming payload is the one you want to send to SQS
            payload = json.dumps({'deliverypersonnelid': delivery_personnel_id, 'order_id': order_id})
            
            # Send message to SQS queue
            response = sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=payload
            )
        
            # You might want to print the response or handle it as needed
            print(response)
            
            return {
                'statusCode': 200,
                # 'body': json.dumps(restaurant_data)
            }

            # lambda_client = boto3.client('lambda', region_name='us-east-1')
            # payload = json.dumps({'zipcode': restaurant_data['zip_code']})
            # response = lambda_client.invoke(
            #     FunctionName='getAvailableDeliveryPersonnel',
            #     InvocationType='RequestResponse',
            #     Payload=payload.encode('utf-8')
            # )
            
            # # Correctly process the response to get the delivery personnel ID
            # response_payload = response['Payload'].read().decode("utf-8")
            # response_payload = json.loads(response_payload)
            # print(response_payload)
            # deliverypersonnelid = response_payload['deliverypersonnelid']  # Adjust this key based on actual response structure
            
            # # Now, use the correct delivery personnel ID in the next payload
            # payload = json.dumps({'deliverypersonnelid': deliverypersonnelid, 'order_id': order_id})
            # response = lambda_client.invoke(
            #     FunctionName='setDeliveryOrderToPersonnel',
            #     InvocationType='RequestResponse',
            #     Payload=payload.encode('utf-8')
            # )
            
            # return {
            #     'statusCode': 200,
            #     'body': json.dumps(restaurant_data)
            # }

        #     lambda_client = boto3.client('lambda', region_name='us-east-1')
        #     payload = json.dumps({'zipcode': restaurant_data['zip_code']})
        #     response = lambda_client.invoke(
        #         FunctionName='getAvailableDeliveryPersonnel',
        #         InvocationType='RequestResponse',
        #         Payload=payload.encode('utf-8')
        # )
        #     payload = json.dumps({'deliverypersonnelid': response, 'order_id': order_id})
        #     response = lambda_client.invoke(
        #         FunctionName='setDeliveryOrderToPersonnel',
        #         InvocationType='RequestResponse',
        #         Payload=payload.encode('utf-8')
        # )
        #     return {
        #         'statusCode': 200,
        #         'body': json.dumps(restaurant_data)
        #     }
            
        else:
            return {
                'statusCode': 404,
                'body': json.dumps('Restaurant not found')
            }

    except Exception as e:
        print("Error:", e)
        return {
            'statusCode': 500,
            'body': json.dumps('Error occurred while processing')
        }