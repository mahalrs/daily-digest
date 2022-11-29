import json
import os

import boto3

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

    output_loc = response['OutputLocation']
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
    # TODO: extract using keyBert
    #

    kws = ['covid', 'china']
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
    # TODO: Ignore HTML parsing for now
    #

    title = 'Zero-Covid protests are spreading across China – but a violent crackdown will follow'
    source = 'The Guardian'
    pdate = 'Mon 28 Nov 2022 11.00 EST'
    text = '''
    Zero-Covid protests are spreading across China – but a violent crackdown will follow
China’s heavy-handed zero-Covid policy was intended to save lives. Now, it’s having devastating consequences. Last week, a fire killed at least 10 people, including children, in a tower block in Urumqi, the capital of Xinjiang. As ever in China, official numbers are unreliable, and the true number of casualties may be much higher. It’s clear that the citizens now protesting across China blame the tragedy on the lockdown, despite the claims of local officials that fire escapes in the building were not locked. Horrific videos of the fire show emergency services attempting in vain to douse the flames from beyond a roadblock, while victims scream from the windows pleading for somebody to open the doors of their apartments.
For once, the suffering of Xinjiang’s people seems to have evoked widespread empathy among China’s wider populace.
    '''

    metadata = {
        'title': title,
        'source': source,
        'published_date': pdate,
    }

    return metadata, text
