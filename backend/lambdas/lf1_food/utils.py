import json
from utils import *
from datetime import date
import re
import logging
import boto3
import csv
# import sys
from geopy.distance import geodesic
import os
import requests
from requests.auth import HTTPBasicAuth
from uszipcode import SearchEngine

# --- Helpers that build all of the responses ---
# Elasticsearch configuration
es_host = 'https://search-domain1-sa27yjmuybcvsq5dwmq456qsbu.us-east-1.es.amazonaws.com'
es_username = 'master'
es_password = 'Master@123'
index_url = f'{es_host}/cloud_index/_search/'
# Configuration for DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('table_restaurant')
menu_items_table_name = 'menu_items'
sqs = boto3.client('sqs')
# URL of your Delivery SQS queue
delivery_queue_url = 'https://sqs.us-east-1.amazonaws.com/944218954103/insertOrderAndOrderItems' 
# URL of your Reservation SQS queue
reservation_queue_url = 'https://sqs.us-east-1.amazonaws.com/944218954103/Create_reservation' 
valid_cuisines = ["american", "asian", "chinese", "italian", "korean", "Indian"]
valid_locations = ["austin", "houston", "dallas"]

def load_zip_code_data(file_path):
    """Load zip code data from a CSV file."""
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        return {row['zip']: (float(row['lat']), float(row['lng'])) for row in reader}

def find_nearby_zip_codes(target_zip, radius_miles, zip_code_data):
    """Find zip codes within a specified radius of a target zip code."""
    if target_zip not in zip_code_data:
        raise ValueError(f"Zip code {target_zip} not found in data.")

    target_coords = zip_code_data[target_zip]
    nearby_zip_codes = []

    for zipcode, coords in zip_code_data.items():
        if geodesic(target_coords, coords).miles <= radius_miles:
            nearby_zip_codes.append(zipcode)

    return nearby_zip_codes

def push_order_to_sqs(message, queue_url):
    sqs = boto3.client('sqs')
    print(message)
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=message
    )

    return response
def query_restaurants_by_cuisine(cuisine_type, input_zipcode):
    # zip_code_data = load_zip_code_data('zipcodes.csv')
    # zip_codes_within_5_miles = find_nearby_zip_codes(input_zipcode, 5, zip_code_data)
    input_zipcode = int(input_zipcode)
    
    # Calculate the range of zip codes
    zip_code_start = input_zipcode - 3
    zip_code_end = input_zipcode + 3

    es_query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {"match": {"restaurant_category": cuisine_type}},
                    {
                        "range": {
                            "zip_code": {
                                "gte": zip_code_start,
                                "lte": zip_code_end
                            }
                        }
                    }
                ]
            }
        },
        "aggs": {
            "unique_restaurant_ids": {
                "terms": {
                    "field": "restaurant_id.keyword",
                    "size": 1000
                }
            }
        }
    }


    # Execute the Elasticsearch query
    es_response = requests.get(index_url, auth=HTTPBasicAuth(es_username, es_password), headers={"Content-Type": "application/json"}, data=json.dumps(es_query))
    if es_response.status_code == 200:
        # Extract restaurant IDs from the Elasticsearch response
        es_results = es_response.json()
        restaurant_ids = [bucket['key'] for bucket in es_results['aggregations']['unique_restaurant_ids']['buckets']]
        # Query DynamoDB for each restaurant ID to get the names and zip codes
        restaurants_in_zipcode = {}
        for restaurant_id in restaurant_ids:
            if len(restaurants_in_zipcode) >= 5:
                break
            response = table.get_item(Key={'id': str(restaurant_id)})
            if 'Item' in response:
                restaurant_data = response['Item']
                # Check if the restaurant's zip code matches the input zip code
                restaurant_name = restaurant_data['name']
                restaurants_in_zipcode[restaurant_name] = restaurant_id
        return restaurants_in_zipcode
    else:
        # Handle error
        print(f'Error executing Elasticsearch query: {es_response.status_code}')
        return None

def fetch_menu(restaurant_id):
    key= f"Restaurant_v2_{restaurant_id}"
    # Attempt to get data from the cache using order_id
    # cache_response = invoke_lambda_function('getfromcacahe', {'key': key})
    # if cache_response:
    #     cache_response = json.loads(cache_response) 
    region_name = 'us-east-1'
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table('menu_items')

    try:
        response = table.query(
            IndexName='restaurant_id-index',
            KeyConditionExpression='restaurant_id = :id',
            ExpressionAttributeValues={':id': restaurant_id},
            Limit=5  # Limit the number of items returned
        )

        menu_items = {item['name']: {'price': item['price'], 'row_id': item['row_id']}
                      for item in response.get('Items', [])}

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    return menu_items


    # set_to_cache_response = invoke_lambda_function('setToCache', {'key': key, 'value': menu_items})


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': {
                'contentType': 'PlainText',
                'content': message
            }
        }
    }


def confirm_intent( intent_name, slots):
    return {
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots
        }
    }


def close(fulfillment_state, message):
    response = {
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            "message": {
              "contentType": "PlainText",
              "content": message
            },
        }
    }

    return response
def close_with_session_attributes(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': {
                'contentType': 'PlainText',
                'content': message
            }
        }
    }
    return response


def delegate(slots):
    return {
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None
        
def elicit_confirmation(session_attributes, intent_name, slots, message):
    print(message)
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',  # or 'ConfirmIntent' if you need confirmation
            'intentName': intent_name,
            'slots': slots,
            'message': {
                'contentType': 'PlainText',
                'content': message
            }        }
    }


class OrderItem:
    def __init__(self, menu_item_id="", menu_item_name="", quantity=0, cost=0.0):
        self.menu_item_id = menu_item_id
        self.menu_item_name = menu_item_name
        self.quantity = quantity
        self.cost = cost
    def to_dict(self):
        return {
            "menu_item_id": self.menu_item_id,
            "menu_item_name": self.menu_item_name,
            "quantity": self.quantity,
            "cost": self.cost
        }
    def __str__(self):
        return f"OrderItem(menu_item_id='{self.menu_item_id}', menu_item_name='{self.menu_item_name}', quantity={self.quantity}, cost={self.cost})"

    def update_menu_item_id(self, menu_item_id):
        self.menu_item_id = menu_item_id

    def update_menu_item_name(self, menu_item_name):
        self.menu_item_name = menu_item_name

    def update_quantity(self, quantity):
        self.quantity = quantity

    def update_cost(self, cost):
        self.cost = cost
    
    def update_details(self, menu_item_id, menu_item_name, cost):
        self.cost = cost
        self.menu_item_name = menu_item_name
        self.menu_item_id = menu_item_id

    def get_total_cost(self):
        numeric_cost = float(self.cost) if isinstance(self.cost, str) else self.cost
        numeric_quantity = int(self.quantity) if isinstance(self.quantity, str) else self.quantity

        return numeric_cost * numeric_quantity

class Order:
    def __init__(self, customer_email="", restaurant_id=None, delivery_address=""):
        self.customer_email = customer_email
        self.restaurant_id = restaurant_id
        self.order_date = date.today().isoformat()  # Sets the current date in YYYY-MM-DD format
        self.delivery_address = delivery_address
        self.order_items = []
        self.total_amount = 0.0

    def __str__(self):
        order_items_str = ', '.join(str(item) for item in self.order_items)
        return f"{{\n  \"customer_email\": \"{self.customer_email}\",\n  \"restaurant_id\": {self.restaurant_id},\n  \"order_date\": \"{self.order_date}\",\n  \"delivery_address\": \"{self.delivery_address}\",\n  \"total_amount\": {self.total_amount},\n  \"order_items\": [{order_items_str}]\n}}"
    
    def to_dict(self):
        return {
            "customer_email": self.customer_email,
            "restaurant_id": self.restaurant_id,
            "order_date": self.order_date,
            "delivery_address": self.delivery_address,
            "total_amount": self.total_amount,  # Use the existing total_amount
            "order_items": [item.to_dict() for item in self.order_items]
        }
    def from_dict(data):
        order = Order()
        order.customer_email = data.get("customer_email", "")
        order.restaurant_id = data.get("restaurant_id")
        order.order_date = data.get("order_date", date.today().isoformat())
        order.delivery_address = data.get("delivery_address", "")
        order.total_amount = data.get("total_amount", 0.0)
        order.order_items = [OrderItem.from_dict(item) for item in data.get("order_items", [])]
        return order
    def update_customer_email(self, customer_email):
        self.customer_email = customer_email

    def update_restaurant_id(self, restaurant_id):
        self.restaurant_id = restaurant_id

    def update_order_date(self, order_date):
        self.order_date = order_date

    def update_delivery_address(self, delivery_address):
        self.delivery_address = delivery_address

    def add_order_item(self, order_item):
        self.order_items.append(order_item)
        self.total_amount += order_item.get_total_cost()

    def get_total_amount(self):
        return self.total_amount
    
def create_message_body(rest_id, email, people, date, time):
    return {
        'rest_id': rest_id,
        'email': email,
        'people': people,
        'date': date,
        'time': time
    }

