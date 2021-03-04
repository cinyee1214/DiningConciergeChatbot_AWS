import json
import boto3
import logging

def lambda_handler(event, context):
    client = boto3.client('lex-runtime')
    
    # print(event['messages'][0])
    # print(event['messages'][0]['unstructured'])
    # print(event['messages'][0]['unstructured']['text'])
    
    response = client.post_text(
        botName='chatbot',
        botAlias='cb',
        userId='admin',
        inputText=event['messages'][0]['unstructured']['text']
        )
    
    
    return {
        'statusCode': 200,
        'body': json.dumps(response['message']),
        'headers': {
            'Access-Control-Allow-Headers' : 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }
    }