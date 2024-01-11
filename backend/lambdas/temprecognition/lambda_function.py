# import json
# import re
# import logging
# from utils import *
# import boto3
# import logging

# # Configure logging
# sqs = boto3.client("sqs")
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)
        
# valid_location = ["texas"]
# valid_cuisine = ["american", "asian", "chinese",
#     "latin american", "dessert", "new mexican", 
#     "mexican", "greek", "mediterranean", "halal", 
#     "healthy", "indian", "vegetarian", "italian", 
#     "japanese", "korean", "thai", "vietnamese"]

# # logger = logging.getLogger()
# # logger.setLevel(logging.DEBUG)


# def build_validation_result(isvalid, violated_slot, message_content):
#     return {
#         'isValid': isvalid,
#         'violatedSlot': violated_slot,
#         'message': {'contentType': 'PlainText', 'content': message_content}
#     }

# def validate_values(intent_request):
#     location = intent_request['currentIntent']['slots']['Location']
#     cuisines = intent_request['currentIntent']['slots']['Cuisines']
#     email = intent_request['currentIntent']['slots']['Email']
    
#     # logger.debug(type(location))
    
#     if location is not None and location.lower() not in valid_location:
#         return build_validation_result(
#             False,
#             'Location',
#             'Invalid location provided. Choose from {}.'.format(', '.join(valid_location))
#         )
    
#     if cuisines is not None and cuisines.lower() not in valid_cuisine:
#         return build_validation_result(
#             False,
#             'Cuisines',
#             'Invalid cuisine provided. Choose from {}.'.format(', '.join(valid_cuisine))
#         )
    
#     email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
#     if email is not None and not re.match(email_pattern, email):
#         return build_validation_result(
#             False,
#             'Email',
#             'Invalid email format.'
#         )
        
#     return {'isValid':True}

# def lambda_handler(event, context):
    
#     cur_intent = event['currentIntent']['name'] 
#     if cur_intent == "ChooseService":
#         # Check if 'ServiceTypeSlot' slot has been set in the event
#         service_type = event['currentIntent']['slots'].get('ServiceTypeSlot')
#         if service_type:
#             print("Response being returned to Lex 0:", service_type)
#             service_type = service_type.lower()  # Convert to lowercase only if it's not None
#             print("Response being returned to Lex 0:", type(service_type))
#             if service_type == "reservation":
#                 # Continue with the existing 'DiningSuggestion' flow
#                 return elicit_slot(
#                     intent_name="DiningSuggestion",
#                     slots=event['currentIntent']['slots'],  # pass the current slots
#                     slot_to_elicit="DiningTime",
#                     message="What time would you like to make a reservation for?"
#                 )
#             elif service_type == "delivery":
#                 # Start the delivery flow
#                 return elicit_slot(
#                     intent_name="SelectCuisine",
#                     slots=event['currentIntent']['slots'],  # pass the current slots
#                     slot_to_elicit="CuisineType",
#                     message="What type of cuisine would you like to have delivered?"
#                 )
#             else:
#                 # Handle unexpected service type
#                 print("Response being returned to Lex 1:")
#                 return elicit_slot(
#                     intent_name="ChooseService",
#                     slots=event['currentIntent']['slots'],
#                     slot_to_elicit="ServiceTypeSlot",
#                     message="Please choose either 'delivery' or 'reservation'."
#                 )
#         else:
#             # If 'ServiceTypeSlot' slot is not set, elicit for it
#             print("Response being returned to Lex 2:")
#             return elicit_slot(
#                 intent_name="ChooseService",
#                 slots=event['currentIntent']['slots'],
#                 slot_to_elicit="ServiceTypeSlot",
#                 message="Would you like delivery or dine-in?"
#             )

#     if cur_intent == "DiningSuggestion":
#         #Checking all the values in the intent
#         if event['invocationSource'] == 'DialogCodeHook':
#             valid_res = validate_values(event)
            
#             # If any value has invalid value
#             if not valid_res['isValid']:
#                 slots = event['currentIntent']['slots']
#                 slots[valid_res['violatedSlot']] = None
                
#                 return elicit_slot(
#                     intent_name=event['currentIntent']['name'],
#                     slots=slots,
#                     slot_to_elicit=valid_res['violatedSlot'],
#                     message=valid_res['message']
#                 )
                
#              # All values have the valid value
#             if event['currentIntent']['confirmationStatus'] == 'Confirmed':
#                 try:
#                     sqs_p = sqs.get_queue_url(QueueName='msgSQS').get('QueueUrl')
#                     resp = sqs.send_message(
#                         MessageBody=json.dumps(event['currentIntent']['slots']),
#                         QueueUrl=sqs_p
#                     )
#                     logger.info(resp)
#                 except Exception as e:
#                     raise e
                    
#                 return close(
#                   "Fulfilled",
#                   message="I'll proceed with the dining suggestions based on your preferences!"
#                   )
#             else:
#                 return delegate(
#                         slots=event['currentIntent']['slots']
#                     )
        
#         return close(
#             "Fulfilled",
#             message="I'll proceed with the dining suggestions based on your preferences!"
#             )

import json
import re
import logging
from utils import *
import boto3
import logging
import requests
from requests.auth import HTTPBasicAuth
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from elasticsearch import Elasticsearch


# Elasticsearch configuration
es_host = 'https://search-domain1-sa27yjmuybcvsq5dwmq456qsbu.us-east-1.es.amazonaws.com'
es_username = 'master'
es_password = 'Master@123'
index_url = f'{es_host}/rest_index/_search/'
# Configuration for DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('table_restaurant')
# Define your valid cuisines, locations, and other necessary data
valid_cuisines = ["american", "asian", "chinese", "italian", ...]
valid_locations = ["downtown", "uptown", ...]
logger = logging.getLogger()
logger.setLevel(logging.INFO)
geolocator = Nominatim(user_agent="geoapiExercises")

def query_restaurants_by_cuisine(cuisine_type, input_zipcode):
    # Elasticsearch query to get the restaurant IDs
    es_query = {
        "size": 1000,  # Assuming you want to check all restaurants of the given cuisine type, adjust the size accordingly
        "query": {
            "match": {
                "restaurant_category": cuisine_type
            }
        },
        "_source": ["restaurant_id"]
    }

    # Execute the Elasticsearch query
    es_response = requests.get(index_url, auth=HTTPBasicAuth(es_username, es_password), headers={"Content-Type": "application/json"}, data=json.dumps(es_query))
    
    if es_response.status_code == 200:
        # Extract restaurant IDs from the Elasticsearch response
        es_results = es_response.json()
        restaurant_ids = [hit['_source']['restaurant_id'] for hit in es_results['hits']['hits']]
        
        # Get the location for the input zipcode
        location = geolocator.geocode({'postalcode': input_zipcode})
        input_location = (location.latitude, location.longitude)

        # Query DynamoDB for each restaurant ID to get the names and coordinates

        restaurants_within_radius = []
        for restaurant_id in restaurant_ids:
            # Make sure restaurant_id is the actual ID value as a string
            response = table.get_item(Key={'id': str(restaurant_id)})  # Adjusted 'restaurant_id' to 'id' to match your table schema
            if 'Item' in response:
                restaurant_data = response['Item']
                restaurant_location = (restaurant_data['latitude'], restaurant_data['longitude'])
                distance = great_circle(input_location, restaurant_location).miles  # Also, make sure to import great_circle, not geodesic
                if distance <= 5:
                    restaurants_within_radius.append(restaurant_data['name'])  # Adjusted 'restaurant_name' to 'name' to match your table attribute
        return restaurants_within_radius

    else:
        # Handle error
        print(f'Error executing Elasticsearch query: {es_response.status_code}')
        return None

# Dummy implementation of fetch_menu
def fetch_menu(restaurant_name):
    # Replace this with your actual logic or API calls in the future
    return ["pizza", "biriyani", "chicken over rice"]


def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    intent_name = event['currentIntent']['name']
    slots = event['currentIntent']['slots']
    service_type = slots.get('ServiceTypeSlot')

    logger.info(f"Current intent: {intent_name}")
    logger.info(f"Service type slot value: {service_type}")

    if service_type == 'delivery':
        logger.info("Handling delivery flow")
        return handle_delivery_flow(event, slots, intent_name)
    elif service_type == 'reservation':
        logger.info("Handling reservation flow")
        return handle_reservation_flow(event, slots, intent_name)
    else:
        logger.info("Eliciting service type")
        return elicit_service_type(event)

def handle_delivery_flow(event, slots, intent_name):
    cuisine_type = slots.get('CuisineTypeSlot')
    zip_code = slots.get('ZipCodeSlot')
    restaurant_name = slots.get('RestaurantNameSlot')
    dish_name = slots.get('DishNameSlot')
    quantity = slots.get('QuantitySlot')
    confirmation = slots.get('ConfirmationSlot')
    input_transcript = event['inputTranscript']

    # Check if cuisine type is provided, otherwise elicit it
    logger.info("Delivery flow initiated")
    if not cuisine_type or cuisine_type not in valid_cuisines:
        logger.info(f"Eliciting cuisine type: {cuisine_type}")
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'CuisineTypeSlot', 'What type of cuisine would you like?')

    # Check if zip code is provided, otherwise elicit it
    if not zip_code:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'ZipCodeSlot', 'Please provide your zip code for delivery.')
    logger.info("after zip1")
    logger.info(f"after zip : {input_transcript} {restaurant_name}")

    # If restaurant name is not provided, fetch and elicit
    restaurants = fetch_restaurants(slots.get('CuisineTypeSlot'), slots.get('ZipCodeSlot'))
    
    if not restaurant_name:
        if input_transcript in restaurants:
            print("restt")
            print(restaurants)
            print(input_transcript)
            # User has already chosen a restaurant, validate the choice
            logger.info(f"User selected lol: {input_transcript}")
            # If valid, set the slot value
            slots['RestaurantNameSlot'] = input_transcript
            logger.info(f"User selected slot: {slots['RestaurantNameSlot']}")
        else:
            logger.info(f"in 1 rest :{restaurant_name}")
            return elicit_confirmation(
                session_attributes=event['sessionAttributes'],
                intent_name=intent_name,
                slots=slots,
                message='Please choose a restaurant: ' + ', '.join(restaurants)
            )

    menu = fetch_menu(slots.get('RestaurantNameSlot'))    
    print("started dish")
    print(menu)
    print(input_transcript)
    if not dish_name:
        if input_transcript in menu:
            print("in else dish")
            print(menu)
            print(input_transcript)
            logger.info(f"User selected dish lol: {input_transcript}")
            # If valid, set the slot value
            slots['DishNameSlot'] = input_transcript
            logger.info(f"User selected menu slot: {slots['DishNameSlot']}")
        else:
            logger.info(f"User selected dish: {menu}")
            logger.info(f"in 1 dish :")
            # Fetch restaurants based on cuisine and zip code
            logger.info(f"User selected dish: {menu}")
            return elicit_confirmation(
                session_attributes=event['sessionAttributes'],
                intent_name=intent_name,
                slots=slots,
                message='Please select a dish from the menu: ' + ', '.join(menu)
            )

    # Elicit quantity if not provided
    if not quantity:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'QuantitySlot', 'How many servings of ' + slots['DishNameSlot'] + ' would you like?')
    logger.info(f"Confirmed slot: {slots['ConfirmationSlot']}")

    # Check if user has confirmed their order, if not confirmed, repeat the menu
    if not confirmation or confirmation.lower() == 'no':
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'ConfirmationSlot', 'Is your order correct?')

    # Place order logic should go here Ok. I have that you want suggestions for {Cuisine} restaurants in {Location} at {DiningTime} for {NumPeople} people. Is that correct?
    if confirmation.lower() == 'yes':
         # Implement this function to place the order
        return close(event['sessionAttributes'], 'Fulfilled', 'Your order has been placed.')

def handle_reservation_flow(event, slots, intent_name):
    cuisine_type = slots.get('CuisineTypeSlot')
    location = slots.get('LocationSlot')
    email = slots.get('EmailSlot')
    number_of_people = slots.get('NumberOfPeopleSlot')
    confirmation = slots.get('ConfirmationSlot')

    # Elicit each slot in turn, if not already provided
    logger.info("Reservation flow initiated")
    if not cuisine_type or cuisine_type not in valid_cuisines:
        logger.info(f"Eliciting cuisine type: {cuisine_type}")
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'CuisineTypeSlot', 'What type of cuisine would you like for your reservation?')

    if not location or location not in valid_locations:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'LocationSlot', 'Which location do you prefer for dining?')

    if not email:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'EmailSlot', 'Please provide your email for reservation confirmation.')

    if not number_of_people:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'NumberOfPeopleSlot', 'For how many people should I make the reservation?')

    if not confirmation or confirmation.lower() == 'no':
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'ConfirmationSlot', 'Can you confirm the reservation details are correct?')

    # Make reservation logic should go here
    if confirmation.lower() == 'yes':
        # make_reservation(slots)  # Implement this function to make the reservation
        return close(event['sessionAttributes'], 'Fulfilled', 'Your reservation has been made.')

def elicit_service_type(event):
    logger.info("Eliciting service type from user")
    return elicit_slot(event['sessionAttributes'], 'FullServiceOrder', event['currentIntent']['slots'], 'ServiceTypeSlot', 'Would you like "delivery" or "reservation"?')

# Define your utility functions here, such as elicit_slot, elicit_confirmation, close, etc.

# Define your functions to interact with the database/API, such as fetch_restaurants, fetch_menu, place_order, make_reservation, etc.


# import boto3
# import json

# def lambda_handler(event, context):
#     # Create Lambda client
#     lambda_client = boto3.client('lambda')

#     # Payload to send to Lambda B
#     payload = {
#         "query": "SELECT * FROM Orders LIMIT 1"
#         # Add any other data you want to pass to Lambda B
#     }

#     # Invoke Lambda B
#     response = lambda_client.invoke(
#         FunctionName='arn:aws:lambda:us-east-1:944218954103:function:selectOrders',  # Replace with Lambda B function name
#         InvocationType='RequestResponse',  # Change based on your invocation needs
#         Payload=json.dumps(payload)
#     )

#     # Parse and use the response from Lambda B
#     response_payload = json.loads(response['Payload'].read())
#     # Process the response_payload as needed

#     return {
#         'statusCode': 200,
#         'body': json.dumps('Lambda A invoked Lambda B and received: ' + str(response_payload))
        
#     }