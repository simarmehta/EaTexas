import json
import boto3

def check_user_logged_in(access_token):
    try:
        # Initialize Cognito client
        client = boto3.client('cognito-idp', region_name='us-east-1')  # Replace 'your-region' with your AWS region
        
        # Validate the access token
        response = client.get_user(
            AccessToken=access_token
        )
        
        # If the call to get_user doesn't throw an error, the token is valid
        return True
    except Exception as e:
        print("Error checking user login:", e)
        return False

# Usage example:

def lambda_handler(event, context):
    access_token = '116b36d0-5a44-4c6e-8ab0-ab647d37ae36'  # Replace with the actual access token
    is_logged_in = check_user_logged_in(access_token)
    
    if is_logged_in:
        print("User is logged in.")
    else:
        print("User is not logged in or the token is invalid.")
    # TODO implement
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
