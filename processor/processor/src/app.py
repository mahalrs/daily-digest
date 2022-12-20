import json
import os

import boto3

from keybert import KeyBERT

REGION = os.environ['REGION']
INF_METADATA_TABLE = os.environ['INF_METADATA_TABLE']
METADATA_TABLE = os.environ['METADATA_TABLE']
PAYLOAD_BUCKET = os.environ['PAYLOAD_BUCKET']
CLASSIFICATION_ENDPOINT = os.environ['CLASSIFICATION_ENDPOINT']
SUMMARY_ENDPOINT = os.environ['SUMMARY_ENDPOINT']


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))

    metadata, content = get_page_content(event)

    keywords = get_keywords(content)
    metadata['keywords'] = keywords
    print(metadata)

    insert_item(metadata, METADATA_TABLE)
    put_payload(metadata['UrlHash'], PAYLOAD_BUCKET, content)

    # async inference endpoint
    out_c = run_inference(content, metadata['UrlHash'], PAYLOAD_BUCKET,
                          CLASSIFICATION_ENDPOINT)
    out_s = run_inference(content, metadata['UrlHash'], PAYLOAD_BUCKET,
                          SUMMARY_ENDPOINT)

    inf_metadata = {'UrlHash': metadata['UrlHash']}

    inf_metadata['OutputLocation'] = out_c
    insert_item(inf_metadata, INF_METADATA_TABLE)

    inf_metadata['OutputLocation'] = out_s
    insert_item(inf_metadata, INF_METADATA_TABLE)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Content Processor!')
    }


def run_inference(text, key, bucket, endpoint_name):
    smr_client = boto3.client('sagemaker-runtime')

    response = smr_client.invoke_endpoint_async(EndpointName=endpoint_name,
                                                InputLocation='s3://' + bucket +
                                                '/' + key,
                                                ContentType='application/json')

    print(response)

    output_loc = response['OutputLocation'].split('/')[-1]
    return output_loc


def put_payload(key, bucket, data):
    body = json.dumps({'inputs': data})

    s3client = boto3.client('s3')
    response = s3client.put_object(Body=body, Bucket=bucket, Key=key)

    print(response)
    return response


def insert_item(item, table):
    db = boto3.resource('dynamodb')
    table = db.Table(table)

    response = table.put_item(Item=item)

    print('@insert_item: response', response)
    return response


def get_keywords(text):
    kw_model = KeyBERT('./keybert')
    keywords = kw_model.extract_keywords(text,
                                         stop_words='english',
                                         keyphrase_ngram_range=(1, 2),
                                         use_maxsum=True,
                                         use_mmr=True,
                                         diversity=0.7,
                                         nr_candidates=20,
                                         top_n=10)

    kws = []
    for k in keywords:
        kws.append(k[0])
    return kws


def get_page_content(event):
    key, url, raw_content = get_data(event)

    metadata, content = parse_data(raw_content)
    metadata['url'] = url
    metadata['UrlHash'] = key

    return metadata, content


def get_data(event):
    object_key = event['Records'][0]['s3']['object']['key']
    bucket = event['Records'][0]['s3']['bucket']['name']

    s3client = boto3.client('s3')
    obj = s3client.get_object(Bucket=bucket, Key=object_key)
    url = obj['ResponseMetadata']['HTTPHeaders']['x-amz-meta-url']
    data = obj['Body'].read().decode('utf-8')

    return object_key, url, data


def parse_data(raw_content):
    # TODO:
    #       Do HTML parsing to retrieve required data
    #       For now, assume raw_content is json

    content = json.loads(raw_content)

    title = content['title']
    source = content['source']
    pdate = content['date']
    text = content['text']

    metadata = {
        'title': title,
        'source': source,
        'published_date': pdate,
    }

    return metadata, text
