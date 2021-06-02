import json
import boto3
import random

# def lambda_handler(event, context):
#     # TODO implement
#     return {
#         'statusCode': 200,
#         'body': json.dumps('Hello from Lambda!')
#     }

def lambda_handler(event, context):
    db = boto3.resource('dynamodb')
    table = db.Table('khoidb')
    k1 = random.randint(0,9)
    k2 = random.randint(0,9)
    response = table.put_item(Item={"id": str(k1), "val": str(k2)})