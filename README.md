# **Dining Concierge Chatbot**
## About
This project is our assignment one for the course - Cloud Computing and Big Data (CS-GY 9223, New York University).

"Dining Concierge Chatbot" is a serverless, microservice driven web-based application. It is an intelligent natural language powered chatbot that is designed using multiple AWS components, such as: S3-Buckets, AWS Lex,  APIGateway, Lambda Functions, SQS, Cloud Watch, ElasticSearch, DynamoDB and SES.

This chatbot can recommend you restaurant suggestions based on your requirements such as City, Cuisine, Number of people, Date and Time. The bot uses the yelp API to fetch relevant suggestions and mails the suggestions on the emailId that the user provides.

## Frontend (HTML/JS/CSS)
![](/frontend.png)
The frontend is hosted in AWS S3 and provides an user interface to interact with the chat bot.

## Backend (Python 3.8)
The frontend is implemented by AWS Lambda functions/Lex/SQS/ElasticSearch/DynamoDB/SES.

## Architechture
![](/Architechture.png)

## Example Interaction
![](/example.png)