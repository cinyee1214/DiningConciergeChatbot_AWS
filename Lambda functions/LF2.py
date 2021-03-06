import json
import boto3
from botocore.exceptions import ClientError
from elasticsearch import Elasticsearch, RequestsHttpConnection
from boto3.dynamodb.conditions import Key, Attr
import random
import os
import requests
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    if 'Records' not in event:
        return {
            'statusCode': 200,
            'body': "No enter to LF2_v2"
        }
            
    print("enter LF2_v2")
    print("event is:")
    print(event)

    print('event[Records][0][messageAttributes] is')
    print(event['Records'][0]['messageAttributes'])
    
    print('event[Records][0][body] is')
    print(event['Records'][0]['body'])
    
    print("line 26: received response is")
    # response = event['Records'][0]['body']
    response = event['Records'][0]['messageAttributes']
    print(response)
    
    
    es_endpoint = 'search-restaurants-sezax3xuf3rcldgfxlnn3oqe7i.us-east-1.es.amazonaws.com' 
    
    region = "us-east-1"
    service = "es"
    credentials = boto3.Session().get_credentials()
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    awsauth = AWS4Auth(access_key, secret_key, region, service, session_token=credentials.token)
    

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp-restaurants')

    # Get the food category from queue message attributes.
    index_category = response['Categories']['stringValue']
    index_category = index_category[:-8]
    print("line 50---the resulting substring is:")
    print(index_category)
    
    # ------------------------------------------------
    
    searchData = get_restaurants_from_es(index_category)
    print("line 155, searchData")
    print(searchData)
    

    restaurantIds = searchData

    randomRestaurantIds = random.sample(restaurantIds, k=3)
    
    print("line 63---randomRestaurantIds")
    print(randomRestaurantIds)

    getContent = getDynamoDbData(table, response, randomRestaurantIds)
    
    print("line 158, text message")
    print(getContent)
    phone_num = response['Phone']['stringValue']
    sendSMS(phone_num, getContent)

    # sqsclient.delete_message(
    #     QueueUrl=queue_url,
    #     ReceiptHandle=receipt_handle
    # )
    
    return {
        'statusCode': 200,
        'body': response
    }

def getDynamoDbData(table, requestData, businessIds):
    if len(businessIds) <= 0:
        return 'We can not find any restaurant under this description, please try again.'

    textString = "Hello! Here are your " + requestData['Categories']['stringValue'] + " restaurant suggestions for " + requestData['PeopleNum']['stringValue'] +" people, for " + requestData['DiningDate']['stringValue'] + " at " + requestData['DiningTime']['stringValue'] + ":"
    count = 1
    
    for business in businessIds:
        # responseData = table.query(KeyConditionExpression=Key('id').eq(business))
        responseData = table.scan(FilterExpression=Attr('id').eq(business))
        if responseData and len(responseData['Items']) >= 1:
            print("the response data is")
            print(responseData)
            responseData = responseData['Items'][0]
            address = responseData['address'] 
            textString = textString + ", " + str(count) + ". " + str(responseData['name']) + ", located at " + str(address[0]) + " " + str(address[1])
            count+=1
    return textString

def sendSMS(phone_num, message):
    print("sending message now")
    phone_num = "+1" + phone_num
    print(phone_num)
    client = boto3.client('sns')
    response = client.publish(
        # TopicArn='arn:aws:sns:us-east-1:167422833486:TextSender',
        PhoneNumber = phone_num,
        Message = message
    )
    print(response)


def send_signed(method, url, service='es', region='us-east-1', body=None):
    credentials = boto3.Session().get_credentials()
    auth = AWS4Auth(credentials.access_key, credentials.secret_key, 
                  region, service, session_token=credentials.token)

    fn = getattr(requests, method)
    if body and not body.endswith("\n"):
        body += "\n"
    try:
        response = fn(url, auth=auth, data=body, 
                        headers={"Content-Type":"application/json"})
        if response.status_code != 200:
            raise Exception("{} failed with status code {}".format(method.upper(), response.status_code))
        return response.content
    except Exception:
        raise

def es_search(criteria):
    URL = 'https://search-restaurants-sezax3xuf3rcldgfxlnn3oqe7i.us-east-1.es.amazonaws.com/restaurants/{}'
    url = URL.format('_search')
    return send_signed('get', url, body=json.dumps(criteria))

def get_restaurants_from_es(category):
    """Given a category, return a list of restaurant ids in that category"""
    criteria = {
        "query": { "match": {'categories': category} },
    }
    content = es_search(criteria)
    content = json.loads(content)
    return [rstr['_source']['id'] for rstr in content['hits']['hits']]