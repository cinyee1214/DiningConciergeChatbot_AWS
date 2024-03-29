import json
import os
import math
import dateutil.parser
import datetime
import time
import logging
import boto3
from botocore.vendored import requests


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Utility function to return slot
def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    
    return response
    
def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }
    
def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


""" --- Functions that control the bot's behavior --- """

def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

# Action Functions

def sendSQSMessage(requestData):
    
    print("Line 85: sending SQS Message with request Data of")
    print(requestData)
    
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/167422833486/Q1'
    
    messageAttributes = {
        'Cuisine': {
            'DataType': 'String',
            'StringValue': requestData['cuisine']
        },
        'Location': {
            'DataType': 'String',
            'StringValue': requestData['location']
        },
        'Categories': {
            'DataType': 'String',
            'StringValue': requestData['categories']
        },
        "DiningTime": {
            'DataType': "String",
            'StringValue': requestData['Time']
        },
        "DiningDate": {
            'DataType': "String",
            'StringValue': requestData['Date']
        },
        'PeopleNum': {
            'DataType': 'Number',
            'StringValue': requestData['peoplenum']
        },
        'Phone': {
            'DataType': 'String',
            'StringValue': requestData['phone']
        }
        
    }
    #mesAtrributes = json.dumps(messageAttributes)
    messageBody=('Slots for the Restaurant')

    
    response = sqs.send_message(
        QueueUrl = queue_url,
        DelaySeconds = 2,
        MessageAttributes = messageAttributes,
        MessageBody = messageBody
        )
    

    print("line 132: successfully sent out SQS message with messageAttributes of ")
    print(messageAttributes)
    print("The response is")
    print(response)
    
    return response['MessageId']
    
""" --- Intents --- """

def validateIntentSlots(location, cuisine, num_people, date, time, phoneNumber):
    """
    Perform basic validations to make sure that user has entered expected values for intent slots.
    """
    locations = ['new york', 'manhattan']
    if location is not None and location.lower() not in locations:
        return build_validation_result(False,
                                       'location',
                                       'We do not have suggestions for {}. Currentlt we can only recommend restaurants in Manhattan. '
                                       'Please enter a valid location'
                                       .format(location))
                                       
    cuisines = ['chinese cuisine', 'american cuisine', 'indian cuisine', 'korean cuisine', 'japanese cuisine']
    if cuisine is not None and cuisine.lower() not in cuisines:
        return build_validation_result(False,
                                       'cuisine',
                                       'Sorry, we do not have suggestions for {}. '
                                       'Please enter a valid cuisine, such as, Chinese cuisine, American cuisine, Indian cuisine, Korean cuisine, Japanese cuisine.'
                                       .format(cuisine))
    if date is not None:
        if not isvalid_date(date) or datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'date', 'Sorry, please enter a valid date.')
            
    
    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'time', 'Please enter a valid time.')

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'time', 'Please enter a valid time.')

        if hour < 10 or hour > 24:
            # Outside of business hours
            return build_validation_result(False, 'time', 'Our business hours are from 10 AM to 11 PM. Can you give me a valid time during this range?')
    
    if num_people is not None:
        num_people = int(num_people)
        if num_people > 20 or num_people <= 0:
            return build_validation_result(False,
                                      'num_people',
                                      'Number of people can only be between 0 and 20')

    
    # if date:
    #     # invalid date
    #     if not isvalid_date(date):
    #         return build_validation_result(False, 'date', 'I did not understand that, what date would you like to add?')
    #     # user entered a date before today
    #     elif datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
    #         return build_validation_result(False, 'date', 'You can search restaurant from today onwards. What day would you like to search?')

    # if given_time:
    #     hour, minute = given_time.split(':')
    #     hour = parse_int(hour)
    #     minute = parse_int(minute)
    #     if math.isnan(hour) or math.isnan(minute):
    #         # Not a valid time; use a prompt defined on the build-time model.
    #         return build_validation_result(False, 'given_time', 'Not a valid time')

    
        # if email and '@' not in email:
        #     return build_validation_result(
        #         False,
        #         'email',
        #         'Sorry, {} is not a valid email address. Please provide a valid email address.'.format(email)
        #     )
        
        if phoneNumber is not None:
            if not phoneNumber.isnumeric() or len(phoneNumber) != 10:
                return build_validation_result(False,
                                           'phone',
                                           'Please enter a valid phone number.'.format(phoneNumber))    
                                       
    print("function validateIntentSlots enters the final return statement")
    return build_validation_result(True, None, None)

def dining_suggestion_intent(intent_request):
    '''
    1. Suggests restaurants based on the slot values that user gave to LEX.
    2. Perform basic validations on the slot values.
    '''
    
    location = get_slots(intent_request)["location"]
    cuisine = get_slots(intent_request)["cuisine"]
    num_people = get_slots(intent_request)["num_people"]
    date = get_slots(intent_request)["date"]
    given_time = get_slots(intent_request)["given_time"]
    phone = get_slots(intent_request)["phone"]
    
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    requestData = {
                    "cuisine": cuisine,
                    "location":location,
                    "categories":cuisine,
                    "limit":"3",
                    "peoplenum": num_people,
                    "Date": date,
                    "Time": given_time,
                    "phone": phone
                }
                
    print(requestData)

    session_attributes['requestData'] = json.dumps(requestData)
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        slots = get_slots(intent_request)
        
        validation_result = validateIntentSlots(location, cuisine, num_people, date, given_time, phone)
        # If validation fails, elicit the slot again 
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(session_attributes,
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
        return delegate(session_attributes, intent_request['currentIntent']['slots'])
    
    messageId = sendSQSMessage(requestData)
    print (messageId)

    return close(intent_request['sessionAttributes'],
             'Fulfilled',
             {'contentType': 'PlainText',
              'content': 'You are all set. Expect my suggestions shortly! We will send you the recommendations by text when they are generated.'})

def dispatch(intent_request):
    """
    Dispatches the to the appropriate intent 
    """
    print(intent_request)
    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return dining_suggestion_intent(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')

# Lambda Handler

def lambda_handler(event, context):
    ''' Send the request to the appropriate intent. '''
    print("loading LF1_v2")
    print("the input event is")
    print(event)
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    
    return dispatch(event)
