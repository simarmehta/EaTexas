import json
import re
import logging
from utils import *
import boto3
import csv
# import sys
from geopy.distance import geodesic
import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import date
from uszipcode import SearchEngine



logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda', region_name='us-east-1')

def invoke_lambda_function(function_name, payload):
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode('utf-8')
        )
        return json.loads(response['Payload'].read().decode('utf-8'))
    except Exception as e:
        print(f'Error invoking {function_name} Lambda:', e)
        return None



def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    intent_name = event['currentIntent']['name']
    slots = event['currentIntent']['slots']
    service_type = slots.get('ServiceTypeSlot')
    # Initialize or retrieve session attributes
    session_attributes = event.get('sessionAttributes') or {}
    order_data = session_attributes.get('order', {})
    order = Order.from_dict(order_data) if order_data else Order()



    # Check if the intent has changed since the last interaction
    previous_intent = session_attributes.get('previous_intent')
    if previous_intent and previous_intent != intent_name:
        # Intent has changed, reset session attributes
        session_attributes = {}  # Reset the session attributes
        logger.info("Intent has changed, resetting session attributes.")
    
    # Store the current intent name in session attributes for future reference
    session_attributes['previous_intent'] = intent_name

    # Update the event object with the modified session attributes
    event['sessionAttributes'] = session_attributes

    # Handle different service types
    if service_type == 'delivery':
        logger.info("Handling delivery flow")
        return handle_delivery_flow(event, slots, intent_name, session_attributes, order)
    elif service_type == 'reservation':
        logger.info("Handling reservation flow")
        return handle_reservation_flow(event, slots, intent_name, session_attributes)
    else:
        logger.info("Eliciting service type")
        return elicit_service_type(event, session_attributes)

def handle_delivery_flow(event, slots, intent_name, session_attributes, order):
    cuisine_type = slots.get('CuisineTypeSlot')
    zip_code = slots.get('ZipCodeSlot')
    restaurant_name = slots.get('RestaurantNameSlot')
    dish_name = slots.get('DishNameSlot')
    quantity = slots.get('QuantitySlot')
    customer_email = slots.get('EmailSlot')
    delivery_address = slots.get('StreetSlot')  
    confirmation = slots.get('ConfirmationSlot')
    input_transcript = event['inputTranscript']
    restaurants_map={}
    menu={}

    # Check if cuisine type is provided, otherwise elicit it
    logger.info("Delivery flow initiated")
    if not cuisine_type:
        logger.info(f"Eliciting cuisine type: {cuisine_type}")
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'CuisineTypeSlot', 'What type of cuisine would you like?')

    # Check if zip code is provided, otherwise elicit it
    if not zip_code:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'ZipCodeSlot', 'Please provide your zip code for delivery.')

    # If restaurant name is not provided, fetch and elicit
    if 'restaurants_map' not in session_attributes:
        restaurants_map = query_restaurants_by_cuisine(cuisine_type, zip_code)
        session_attributes['restaurants_map'] = json.dumps(restaurants_map)
    else:
        # Deserialize the restaurants map from the JSON string in session attributes
        restaurants_map = json.loads(session_attributes['restaurants_map'])
    if not restaurant_name:
        restaurant_names = list(restaurants_map.keys())
        numbered_restaurant_list = " - ".join(f"{i + 1}) {name}" for i, name in enumerate(restaurant_names))
        message = f"Please select a restaurant by number: {numbered_restaurant_list}"
        selected_index = int(input_transcript) - 1 if input_transcript.isdigit() else None

        if selected_index is not None and 0 <= selected_index < len(restaurant_names):
            slots['RestaurantNameSlot'] = restaurant_names[selected_index]
            logger.info(f"User selected restaurant: {slots['RestaurantNameSlot']}")
            input_transcript = None
            # ... proceed with handling the selected restaurant ...
        else:
            # Input is not a digit or is out of range, ask to choose by number
            return elicit_confirmation(session_attributes, intent_name, slots, message)
    restaurant_id = restaurants_map.get(slots['RestaurantNameSlot'])
    order.update_restaurant_id(restaurant_id)

    if 'menu' not in session_attributes:
        menu = fetch_menu(restaurant_id)
        session_attributes['menu'] = json.dumps(menu)
    else:
        menu = json.loads(session_attributes['menu'])
    if not dish_name:    
        # menu = fetch_menu(restaurant_id)  
        dish_names = list(menu.keys())
        numbered_dish_list =  " - ".join(f"{i + 1}. {name} : {menu[name]['price']}" for i, name in enumerate(dish_names))

        # Convert input_transcript to a string and check if it is a digit
        selected_index = int(input_transcript) - 1 if input_transcript and input_transcript.isdigit() else None

        if selected_index is not None and 0 <= selected_index < len(dish_names):
            selected_dish_name = dish_names[selected_index]
            slots['DishNameSlot'] = selected_dish_name
            logger.info(f"User selected dish: {selected_dish_name}")
            # ... proceed with handling the selected dish ...
        else:
            message = f"Please select a dish from the menu by number:\n{numbered_dish_list}"
            return elicit_confirmation(session_attributes, intent_name, slots, message)
    selected_dish = menu[slots['DishNameSlot']]

    # Elicit quantity if not provided
    if not quantity:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'QuantitySlot', 'How many servings of ' + slots['DishNameSlot'] + ' would you like?')
    logger.info(f"Confirmed slot: {slots['ConfirmationSlot']}")


    if not slots.get('EmailSlot'):
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'EmailSlot', "Please provide your email address for the order confirmation.")
    
    order.update_customer_email(slots.get('EmailSlot'))
    if not slots.get('StreetSlot'):
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'StreetSlot', "Please provide the delivery address for your order.")

    confirmation_message = (
    f"You have selected the following:\n"
    f"Cuisine Type: {cuisine_type}\n"
    f"Zip Code: {zip_code}\n"
    f"Restaurant: {restaurant_name}\n"
    f"Dish: {dish_name}\n"
    f"Quantity: {quantity}\n"
    f"Email: {customer_email}\n"
    f"Delivery Address: {delivery_address}\n\n"
    "Is this correct?"
    )
    if not confirmation or confirmation.lower() == 'no':
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'ConfirmationSlot', confirmation_message)

    if confirmation.lower() == 'yes':
        order_item = OrderItem()
        order_item.update_menu_item_id(selected_dish['row_id'])
        logger.info(f"Updated menu item ID: {selected_dish['row_id']}")
        order_item.update_menu_item_name(slots['DishNameSlot'])
        order_item.update_quantity(slots['QuantitySlot'])
        logger.info(f"Updated menu item name: {slots['DishNameSlot']}")
        price_str = selected_dish['price']
        price_num = price_str.split()[0]  
        order_item.update_cost(float(price_num))    
        order.add_order_item(order_item)
        order.update_delivery_address(slots.get('StreetSlot'))
        session_attributes['order'] = order.to_dict()
        session_attributes.clear()
        event['sessionAttributes'] = {}
        response = push_order_to_sqs(json.dumps(order.to_dict()), delivery_queue_url)
        print("SQS Response:", response)
         # Implement this function to place the order
        return close_with_session_attributes(session_attributes, 'Fulfilled', 'Your order has been placed.')

def handle_reservation_flow(event, slots, intent_name, session_attributes):
    cuisine_type = slots.get('CuisineTypeSlot')
    zip_code = slots.get('ZipCodeSlot')
    location = slots.get('LocationSlot')
    restaurant_name = slots.get('RestaurantNameSlot')
    email = slots.get('EmailSlot')
    number_of_people = slots.get('NumberOfPeopleSlot')
    date = slots.get('DateSlot')
    time = slots.get('TimeSlot')
    input_transcript = event['inputTranscript']
    confirmation = slots.get('ConfirmationSlot')
    restaurants_map={}

    # Elicit each slot in turn, if not already provided
    logger.info("Reservation flow initiated")
    if not cuisine_type:
        logger.info(f"Eliciting cuisine type: {cuisine_type}")
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'CuisineTypeSlot', 'What type of cuisine would you like for your reservation?')
    
    if not zip_code:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'ZipCodeSlot', 'Please provide the zip code for the restaurant location.')

    if not location:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'LocationSlot', 'Which location do you prefer for dining?')
    
    if 'restaurants_map' not in session_attributes:
        restaurants_map = query_restaurants_by_cuisine(cuisine_type, zip_code)
        session_attributes['restaurants_map'] = json.dumps(restaurants_map)
    else:
        restaurants_map = json.loads(session_attributes['restaurants_map'])
    if not restaurant_name:
        restaurant_names = list(restaurants_map.keys())
        numbered_restaurant_list =  " - ".join(f"{i + 1}. {name}" for i, name in enumerate(restaurant_names))
        message = f"Please select a restaurant by number:\n{numbered_restaurant_list}"
        selected_index = int(input_transcript) - 1 if input_transcript.isdigit() else None
    
        if selected_index is not None and 0 <= selected_index < len(restaurant_names):
            slots['RestaurantNameSlot'] = restaurant_names[selected_index]
            logger.info(f"User selected restaurant: {slots['RestaurantNameSlot']}")
            input_transcript = None
            # ... proceed with handling the selected restaurant ...
        else:
            # Input is not a digit or is out of range, ask to choose by number
            return elicit_confirmation(session_attributes, intent_name, slots, message)


    rest_id = restaurants_map.get(slots['RestaurantNameSlot'])
    if not email:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'EmailSlot', 'Please provide your email for reservation confirmation.')

    if not number_of_people:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'NumberOfPeopleSlot', 'For how many people should I make the reservation?')
    
    if not date:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'DateSlot', 'What date would you like to make the reservation for?')

    if not time:
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'TimeSlot', 'At what time would you like to make the reservation?')

    confirmation_message = (
        "You have selected the following for your restaurant reservation:\n"
        f"Cuisine Type: {cuisine_type}\n"
        f"Location: {location}\n"
        f"Restaurant Name: {restaurant_name}\n"
        f"Number of People: {number_of_people}\n"
        f"Date: {date}\n"
        f"Time: {time}\n"
        f"Email: {email}\n"
        f"Zip Code: {zip_code}\n\n"
        "Is this correct?"
    )

    if not confirmation or confirmation.lower() == 'no':
        return elicit_slot(event['sessionAttributes'], intent_name, slots, 'ConfirmationSlot', confirmation_message)

    if confirmation.lower() == 'yes':  
        response = push_order_to_sqs(json.dumps(create_message_body(rest_id, email, number_of_people, date, time)), reservation_queue_url)
        print("SQS Response:", response)
        return close_with_session_attributes(session_attributes, 'Fulfilled', 'Your reservation has been made.')

def elicit_service_type(event):
    logger.info("Eliciting service type from user")
    return elicit_slot(event['sessionAttributes'], 'FullServiceOrder', event['currentIntent']['slots'], 'ServiceTypeSlot', 'Would you like "delivery" or "reservation"?')


