import json
import boto3
import pytz
from datetime import datetime
from dateutil import tz  # Import necessary tz module for date conversions

location_service = boto3.client('location')

def get_ny_time():
    # Get the timezone for New York (Eastern Time)
    ny_timezone = pytz.timezone('America/New_York')

    # Get the current time in UTC
    utc_now = datetime.utcnow()

    # Convert UTC time to New York time
    ny_time = utc_now.astimezone(ny_timezone)

    # Convert the datetime object to a string for JSON serialization
    formatted_time = ny_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    return formatted_time

def lambda_handler(event, context):
    order_id = event["order_id"]
    response = location_service.get_device_position_history(
        DeviceId=order_id,
        EndTimeExclusive=get_ny_time(),
        MaxResults=40,
        StartTimeInclusive=datetime(2015, 1, 1),
        TrackerName='DeliveryPeopleTrackingData'
    )
    print(response)
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(response, default=str)  # Serialize with default=str
    }
