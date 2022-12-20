import json
import os

import boto3
from botocore.exceptions import ClientError

REGION = os.environ['REGION']
METADATA_TABLE = os.environ['METADATA_TABLE']
HISTORY_TABLE = os.environ['HISTORY_TABLE']


def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event))

    key = event['queryStringParameters']['key']
    userid = event['headers']['userid']

    data = get_item({'UrlHash': key}, METADATA_TABLE)['Item']

    liked_res = get_item({'key': userid + key + 'like'}, HISTORY_TABLE)
    liked = False
    if 'Item' in liked_res:
        liked = liked_res['Item']['read']

    body = {
        'title': data['title'],
        'key': data['UrlHash'],
        'text': data['summary'],
        'source': data['url'],
        'tags': data['tags'],
        'liked': liked
    }

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps(body)
    }


def get_item(key, table):
    db = boto3.resource('dynamodb')
    table = db.Table(table)

    try:
        response = table.get_item(Key=key)
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        print('@get_item: response', response)
        return response
