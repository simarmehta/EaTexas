import json
import boto3
import pytz
from datetime import datetime
def get_ny_time():
    # Get the timezone for New York (Eastern Time)
    ny_timezone = pytz.timezone('America/New_York')

    # Get the current time in UTC
    utc_now = datetime.utcnow()

    # Convert UTC time to New York time
    ny_time = utc_now.astimezone(ny_timezone)

    # Format the time as required for AWS Location Service
    return ny_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

# Initialize AWS Location Service client
location_service = boto3.client('location', region_name='us-east-1')

def lambda_handler(event, context):
    try:
        print(event)
        longitude = event['location']["longitude"] # Assuming delivery data is in the request body
        latitude = event['location']["latitude"] # Assuming delivery data is in the request body
        order_id = event['order_id']
        # Create a place object using the delivery data
        
        # Call AWS Location Service to put the place (store delivery data)
        response = location_service.batch_update_device_position(
            TrackerName='DeliveryPeopleTrackingData',  # Replace with your tracker name
            Updates=[
                {
                    'DeviceId': order_id,  # Replace with your device ID
                    'Position': [longitude, latitude],
                    'SampleTime': get_ny_time()
                }
            ]
        )
        # Construct a response indicating successful storage
        response = {
            'statusCode': 200,
            'body': json.dumps({'message': 'Delivery data stored in AWS Location Service successfully.'})
        }
        return response
    except Exception as e:
        # Handle errors and construct an appropriate error response
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
        return response
