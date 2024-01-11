import json
import boto3

def create_order_insert_query(event):
    try:
        # Extract data from the event for orders table
        customer_email = event['customer_email']
        restaurant_id = event['restaurant_id']
        order_date = event['order_date']
        delivery_address = event['delivery_address']
        total_amount = event['total_amount']

        # Set default status as 'Placed'
        status = 'Placed'

        # Construct the INSERT query for orders table
        insert_query = f'''
            INSERT INTO orders (
                customer_email,
                restaurant_id,
                order_date,
                delivery_address,
                total_amount,
                status
            )
            VALUES ('{customer_email}', {restaurant_id}, '{order_date}', '{delivery_address}',
                    {total_amount}, '{status}')
            RETURNING order_id;
        '''

        return insert_query

    except Exception as e:
        return f'Error creating insert query for orders table: {str(e)}'

def create_order_items_insert_queries(order_id, order_items):
    try:
        insert_queries = []
        for item in order_items:
            menu_item_id = item['menu_item_id']
            menu_item_name = item['menu_item_name']
            quantity = item['quantity']
            cost = item['cost']

            # Construct the INSERT query for order_items table
            insert_query = f'''
                INSERT INTO order_items (
                    order_id,
                    menu_item_id,
                    menu_item_name,
                    quantity,
                    cost
                )
                VALUES ({order_id}, {menu_item_id}, '{menu_item_name}', {quantity}, {cost});
            '''

            insert_queries.append(insert_query)

        return insert_queries

    except Exception as e:
        return [f'Error creating insert query for order_items table: {str(e)}']

def lambda_handler(event, context):
    try:
        print(event)
        for record in event['Records']:
        # Parse the message body
            message_body = json.loads(record['body'])
            # Create the INSERT query for orders table
            order_insert_query = create_order_insert_query(message_body)
    
            # Extract order_items from event
            order_items = message_body.get('order_items', [])
    
            # Pass the insert query for orders to another Lambda function
            lambda_client = boto3.client('lambda')
            function_name = 'insertQueryProcessor'
            
            order_payload = {
                'query': order_insert_query
            }
            # Invoke the other Lambda function for orders table
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(order_payload)
            )
    
            # Get the order_id from the response
            response_payload = json.loads(response['Payload'].read().decode('utf-8'))
            order_id = json.loads(response_payload['body'])['insertedId']
            sqs_client = boto3.client('sqs')
            print("a")
            queue_url = 'https://sqs.us-east-1.amazonaws.com/944218954103/order_placed_queue'
            response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=str(order_id)
            )
            print("b")
            print(response)
            # Create the INSERT queries for order_items table
            order_items_insert_queries = create_order_items_insert_queries(order_id, order_items)
    
            # Pass the insert queries for order_items to another Lambda function
            order_items_function_name = 'insertQueryProcessor'
    
            for query in order_items_insert_queries:
                order_items_payload = {
                    'query': query
                }
    
                # Invoke the other Lambda function for order_items table
                response = lambda_client.invoke(
                    FunctionName=order_items_function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(order_items_payload)
                )
        # ... your existing lambda_handler code ...

# Fetch restaurant details
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        ses_client = boto3.client('ses', region_name='us-east-1')

    # DynamoDB tables
        
        restaurant_table = dynamodb.Table('table_restaurant')
    
    # Sender's email - must be verified in Amazon SES
        sender_email = 'ccprojectcp@gmail.com'
        restaurant_table = dynamodb.Table('table_restaurant')
        print(message_body)
        print('abcd')
        restaurant_response = restaurant_table.get_item(Key={'id': str(message_body['restaurant_id'])})
        print("Restaurant ID:", message_body['restaurant_id'])
        restaurant_item = restaurant_response.get('Item', {})
        restaurant_name = restaurant_item.get('name', 'Unknown Restaurant')
        restaurant_email = 'ccprojectcp@gmail.com' # Assuming restaurant email is stored in DynamoDB
        # ... continuing from your existing lambda_handler code ...

        if restaurant_email:
            restaurant_subject = 'New Order Placed'
            restaurant_body_text = (f"Dear {restaurant_name},\n\n"
                                    f"A new order has been placed.\n"
                                    f"Order Details:\n"
                                    f" - Customer Email: {message_body['customer_email']}\n"
                                    f" - Total Amount: {message_body['total_amount']}\n"
                                    f" - Delivery Address: {message_body['delivery_address']}\n\n")
                                    # f"Please prepare the order for delivery.\n\n"
                                    # f"Best regards,\nYour Order Processing System")
            for item in message_body.get('order_items', []):
                restaurant_body_text += (f"   - {item['menu_item_name']} (ID: {item['menu_item_id']}), "
                                   f"Quantity: {item['quantity']}, Cost: ${item['cost']}\n")
    
            restaurant_body_text += "\nPlease prepare the order for delivery.\n\nBest regards,\nYour Order Processing Syste"
            ses_client.send_email(
                Source=sender_email,  # Replace with your SES verified email
                Destination={'ToAddresses': [restaurant_email]},
                Message={
                    'Subject': {'Data': restaurant_subject},
                    'Body': {'Text': {'Data': restaurant_body_text}}
                }
            )
        # ... continuing from your existing lambda_handler code ...

# Assuming customer_email is extracted from the message_body
        customer_email = message_body['customer_email']
        print(customer_email)
        
        # Construct email content
        subject = 'Your Order Confirmation'
        body_text = (f"Dear Customer,\n\n"
                     f"Thank you for your order from {restaurant_name}.\n"
                     f"Order Details:\n"
                     
                     f" - Total Amount: {message_body['total_amount']}\n"
                     f" - Delivery Address: {message_body['delivery_address']}\n\n")
                    #  f"We are preparing your order and will deliver it soon.\n\n"
                    #  f"Best regards,\nYour Favorite Restaurant")
        for item in message_body.get('order_items', []):
            body_text += (f"   - {item['menu_item_name']} (ID: {item['menu_item_id']}), "
                                   f"Quantity: {item['quantity']}, Cost: ${item['cost']}\n")
    
        body_text += "\nWe are preparing your order and will deliver it soon.\n\nBest regards,\nYour Favorite Restaurant"
        # Send the email using SES
        ses_client.send_email(
            Source=sender_email,  # Replace with your SES verified email
            Destination={'ToAddresses': [customer_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )

# ... rest of your lambda_handler code ...
    

# ... rest of your lambda_handler code ...

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Insert queries sent to Lambda functions'}),
        }

    except Exception as e:
        print(str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error executing function: ' + str(e)}),
        }
