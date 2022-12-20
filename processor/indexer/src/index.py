import json
import os
import datetime

import boto3
from botocore.exceptions import ClientError

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = os.environ['REGION']
INF_METADATA_TABLE = os.environ['INF_METADATA_TABLE']
METADATA_TABLE = os.environ['METADATA_TABLE']
CLASSIFY_BUCKET = os.environ['CLASSIFICATION_BUCKET']
SUMMARY_BUCKET = os.environ['SUMMARY_BUCKET']

HOST = os.environ['OPENSEARCH_ENDPOINT']
INDEX = os.environ['OPENSEARCH_INDEX']


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))

    object_key = event['Records'][0]['s3']['object']['key']
    bucket = event['Records'][0]['s3']['bucket']['name']

    data = get_data(object_key, bucket)

    key = get_item({'OutputLocation': object_key},
                   INF_METADATA_TABLE)['Item']['UrlHash']
    metadata = get_item({'UrlHash': key}, METADATA_TABLE)['Item']

    metadata['timestamp'] = datetime.datetime.now().isoformat()

    if bucket == CLASSIFY_BUCKET:
        tags = extract_tags(data)
        metadata['tags'] = tags
        insert_item(metadata, METADATA_TABLE)
        index_item(key, metadata)
    else:
        summary = data[0]['summary_text']
        metadata['summary'] = summary
        insert_item(metadata, METADATA_TABLE)
        index_item(key, metadata)

    return {'statusCode': 200, 'body': json.dumps('Hello from Index Lambda!')}


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


def index_item(key, data):
    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)

    # # Delete the index
    # print('Deleting index')
    # print(client.indices.delete(index=INDEX))

    body = {'doc': data, 'doc_as_upsert': True}
    client.index(index=INDEX, id=key, body=body, refresh=True)
    print(client.get(index=INDEX, id=key))


def extract_tags(data):
    tags = []

    for e in data:
        tags.append(e['label'])

    return tags


def get_data(object_key, bucket):
    s3client = boto3.client('s3')
    obj = s3client.get_object(Bucket=bucket, Key=object_key)
    data = obj['Body'].read().decode('utf-8')

    return json.loads(data)


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
