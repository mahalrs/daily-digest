import json
import os

import boto3
from botocore.exceptions import ClientError

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = os.environ['REGION']
METADATA_TABLE = os.environ['METADATA_TABLE']

HOST = os.environ['OPENSEARCH_ENDPOINT']
INDEX = os.environ['OPENSEARCH_INDEX']


def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event))

    items = query()

    results = []
    for item in items:
        results.append({
            'title': item['title'],
            'key': item['UrlHash'],
            'tags': item['tags']
        })

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps({'results': results})
    }


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


def query():
    q = {
        'size': 20,
        'fields': ['timestamp'],
        'sort': [{
            'timestamp': {
                'order': 'desc'
            }
        }]
    }

    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)

    res = client.search(index=INDEX, body=q)
    print(res)
    hits = res['hits']['hits']
    results = []

    for hit in hits:
        results.append(hit['_source'])

    return results


def get_top_results():
    db = boto3.resource('dynamodb')
    table = db.Table(METADATA_TABLE)

    response = table.scan(TableName=METADATA_TABLE, Limit=10)
    print('@scan: response', response)
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
