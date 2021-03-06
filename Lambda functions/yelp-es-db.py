'''
    Scrap 5000+ random restaurants in Manhattan
    Get restaurants by your self-defined cuisine types
    Each cuisine type should have 1,000 restaurants or so.
'''

import json
import boto3
import datetime
import requests
from elasticsearch import Elasticsearch, RequestsHttpConnection
import csv
from io import BytesIO
from requests_aws4auth import AWS4Auth
import os

def lambda_handler(event, context):
    """
    This lambda function calls the yelp api to fetch restaurants in DynamoDB table
    yelp-restaurants and indexes it in elastic search service.
    """
    resultData = []
    yelp_limit = 50
    # Supported Cuisines
    cuisines = ['chinese', 'american', 'indian', 'korean', 'japanese']
    # cuisines = ['indian']
    target_cuisine = cuisines[0]
    # Change this location to New York, Manhattan.
    locations = ["manhattan"]
    # locations = ["new york"]

    restaurantIterations = 20
    for cuisine in cuisines:
        # this is to make sure that each cuisine has 1000 restaurants in total
        for i in range(restaurantIterations):
            for loc in locations:
                requestData = {
                            "term": cuisine + " restaurants",
                            "location": loc,
                            "limit": yelp_limit,
                            "offset": yelp_limit*i
                            #"peoplenum": num_people,
                            #"Date": date,
                            #"Time": given_time,
                            #"EmailId": emailId
                        }
                yelp_rest_endpoint = "https://api.yelp.com/v3/businesses/search"
    
                querystring = requestData
    
                payload = ""
                headers = {
                    "Authorization": "Bearer PRXmaf5TjkmZ01_xwmYa5ufX4wgzmYZwtEpg5zKVJlnLmaEzsY-vkYbGV1xtfgbchQmvlEVzZxmmnP6Vh0lSVXQ-8qBzBTs195sLs9ODqG1Pl8-VU48_e5irY5I-YHYx",
                    'cache-control': "no-cache"
                }
    
                response = requests.get(yelp_rest_endpoint, data=payload, headers=headers, params=querystring)
                message = json.loads(response.text)
                result = message["businesses"]
                resultData = resultData + result

    # Add data to DynamoDB
    print("Starting to insert into DynamoDB")
    dynamoInsert(resultData)

    # Add index data to the ElasticSearch
    print("Starting to add Elastic Index")
    addElasticIndex(resultData, target_cuisine)

    return {
        'statusCode': 200,
        'body': json.dumps('success')
    }

def dynamoInsert(restaurants):

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp-restaurants')


    for restaurant in restaurants:
        print("the restaurant we have is")
        print(restaurant)
        tableEntry = {
            'id': restaurant['id'],
            'alias': restaurant['alias'],
            'name': restaurant['name'],
            'is_closed': restaurant['is_closed'],
            'categories': restaurant['categories'],
            'rating': int(restaurant['rating']),
            'review_count': int(restaurant['review_count']),
            'address': restaurant['location']['display_address']
        }

        if (restaurant['coordinates'] and restaurant['coordinates']['latitude'] and restaurant['coordinates']['longitude']):
            tableEntry['latitude'] = str(restaurant['coordinates']['latitude'])
            tableEntry['longitude'] = str(restaurant['coordinates']['longitude'])

        if (restaurant['location']['zip_code']):
            tableEntry['zip_code'] = restaurant['location']['zip_code']

        # Add necessary attributes to the yelp-restaurants table
        table.put_item(
            Item={
                'insertedTimestamp': str(datetime.datetime.now()),
                'id': tableEntry['id'],
                'name': tableEntry['name'],
                'address': tableEntry['address'],
                'latitude': tableEntry.get('latitude', None),
                'longitude': tableEntry.get('longitude', None),
                'review_count': tableEntry['review_count'],
                'rating': tableEntry['rating'],
                'zip_code': tableEntry.get('zip_code', None),
                'categories': tableEntry['categories']
               }
            )

# Add elastic search indeices after DB has been added
def addElasticIndex(restaurants, target_cuisine):
    # host = "search-restaurants-sezax3xuf3rcldgfxlnn3oqe7i.us-east-1.es.amazonaws.com/restaurants/{}"
    host = "search-restaurants-sezax3xuf3rcldgfxlnn3oqe7i.us-east-1.es.amazonaws.com"
    region = "us-east-1"
    service = "es"
    credentials = boto3.Session().get_credentials()
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    awsauth = AWS4Auth(access_key, secret_key, region, service, session_token=credentials.token)

    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        use_ssl = True,
        http_auth = awsauth,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    count = 0
    for restaurant in restaurants:

        index_data = {
            'id': restaurant['id'],
            'categories': target_cuisine
        }
        # print("indexing restaurant id of ", restaurant['id'])
        print(restaurant['categories'])
        count += 1
        print(count)
        es.index(index="restaurants", doc_type="Restaurant", id=restaurant['id'], body=index_data)

    
