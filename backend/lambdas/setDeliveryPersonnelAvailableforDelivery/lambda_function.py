import json
import boto3

def lambda_handler(event, context):
    deliverypersonnelid = event.get('deliverypersonnelid')
    pincode = event.get('pincode')

    # Construct the INSERT statement
    insert_statement = f"INSERT INTO AvailableDeliveryPersonnel (deliverypersonnelid, pincode, order_ids) VALUES ('{deliverypersonnelid}', '{pincode}', '');"

    # Send the insert statement to another Lambda function
    lambda_client = boto3.client('lambda')
    function_name = 'insertQueryProcessor'  # Replace with your Lambda function name
    payload = {
        'query': insert_statement
    }

    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Insert statement sent to the Lambda function'}),
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error executing function: ' + str(e)}),
        }
