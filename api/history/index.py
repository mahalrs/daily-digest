import json
import os
import decimal

import boto3
from botocore.exceptions import ClientError

REGION = os.environ['REGION']
METADATA_TABLE = os.environ['METADATA_TABLE']
HISTORY_TABLE = os.environ['HISTORY_TABLE']


def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event))

    userid = event['headers']['userid']
    data = json.loads(event['body'])

    handle_event(userid, data['key'], data['event'])

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps({'ok': True})
    }


def handle_event(userid, key, event):
    if event == 'like':
        insert_item({'key': userid + key + 'like', 'read': True}, HISTORY_TABLE)
        handle_counter(userid, key, True)
    elif event == 'dislike':
        insert_item({
            'key': userid + key + 'like',
            'read': False
        }, HISTORY_TABLE)
        handle_counter(userid, key, False)
    elif event == 'read' or event == 'readmore':
        handle_counter(userid, key, True)


def handle_counter(userid, key, increase):
    tags = get_item({'UrlHash': key}, METADATA_TABLE)['Item']['tags']
    for t in tags:
        update_counter(userid + t, HISTORY_TABLE, increase)

    update_counter('totalsum', HISTORY_TABLE, increase)

    res = get_item({'key': 'tags'}, HISTORY_TABLE)
    old_tags = []
    if 'Item' in res:
        old_tags = res['Item']['tags']

    old_tags.extend(tags)
    old_tags = list(set(old_tags))

    insert_item({'key': 'tags', 'tags': old_tags}, HISTORY_TABLE)


def update_counter(key, table, increase):
    db = boto3.resource('dynamodb')
    table = db.Table(table)

    exp = 'set ct = if_not_exists(ct, :val0) + :val'
    if not increase:
        exp = 'set ct = if_not_exists(ct, :val0) - :val'

    response = table.update_item(Key={'key': key},
                                 UpdateExpression=exp,
                                 ExpressionAttributeValues={
                                     ':val': decimal.Decimal(1),
                                     ':val0': decimal.Decimal(0)
                                 },
                                 ReturnValues='UPDATED_NEW')

    print(response)


def insert_item(item, table):
    db = boto3.resource('dynamodb')
    table = db.Table(table)

    response = table.put_item(Item=item)

    print('@insert_item: response', response)
    return response


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
