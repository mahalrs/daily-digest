import json
import os

import boto3
from botocore.exceptions import ClientError

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = os.environ['REGION']
METADATA_TABLE = os.environ['METADATA_TABLE']
HISTORY_TABLE = os.environ['HISTORY_TABLE']

HOST = os.environ['OPENSEARCH_ENDPOINT']
INDEX = os.environ['OPENSEARCH_INDEX']


def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event))

    userid = event['headers']['userid']

    top_tags = get_top_tags(userid)
    results = query_results(top_tags)
    print(results)

    # TODO:
    #       remove already read from results
    #

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


def query_results(tags):
    r = []

    if len(tags) == 0:
        hits = query_latest()
        for hit in hits:
            r.append({
                'title': hit['title'],
                'key': hit['UrlHash'],
                'tags': hit['tags']
            })

    for t in tags:
        hits = query(t)
        for hit in hits:
            r.append({
                'title': hit['title'],
                'key': hit['UrlHash'],
                'tags': hit['tags']
            })

    return r


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


def query(term):
    q = {
        'size': 30,
        'query': {
            'multi_match': {
                'query': term,
                'fields': ['tags']
            }
        }
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


def query_latest():
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


def get_top_tags(userid):
    it = calc_interest(userid)
    if it is None:
        return []

    it.sort(key=lambda tup: tup[1], reverse=True)
    print(it)

    it = it[:3]
    ret = []
    for i in it:
        ret.append(i[0])

    return ret


def calc_interest(userid):
    user_clicks, totalsum = get_clicks(userid)

    if len(user_clicks) == 0:
        return

    total = 0
    for c in user_clicks:
        total += c[1]

    cat_by_total = []
    for c in user_clicks:
        i = float(c[1]) / float(total)
        cat_by_total.append((c[0], i))

    pt_click = total / totalsum
    pt_click = float(pt_click)

    interest = []
    for c in cat_by_total:
        i = c[1] * pt_click / 0.2
        interest.append((c[0], i))

    print(interest)
    return interest


def get_clicks(userid):
    res = get_item({'key': 'tags'}, HISTORY_TABLE)
    tags = []
    if 'Item' in res:
        tags = res['Item']['tags']

    print(tags)

    clicks = []
    for t in tags:
        res = get_item({'key': userid + t}, HISTORY_TABLE)
        if 'Item' in res:
            c = res['Item']['ct']
            clicks.append((t, c))

    print(clicks)

    total_clicks = 0
    res = get_item({'key': 'totalsum'}, HISTORY_TABLE)
    if 'Item' in res:
        total_clicks = res['Item']['ct']

    print(total_clicks)

    return clicks, total_clicks


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
