import boto3

from utils import url_is_from_any_domain

BUCKET = 'daily-digest-v1-crawled-content'

WHITELIST = [
    'cnn.com',
    'usatoday.com',
    'reuters.com',
    'foxnews.com',
    'cbssports.com',
    'espn.com',
    'androidpolice.com',
    'nydailynews.com',
    'politico.com',
    'theguardian.com',
    'news.yahoo.com',
    'digitaltrends.com',
    'gizmodo.com',
    'techradar.com',
    '9to5mac.com',
    'macworld.com',
    'people.com',
    'nfl.com',
    '247sports.com',
    'space.com',
    'vice.com',
    'ndtv.com',
    'msn.com',
    'indiatoday.in',
    'politifact.com',
]


def save_content(key, url, content):
    print(url)

    if not url_is_from_any_domain(url, WHITELIST):
        return

    print('SAVING content...')

    s3client = boto3.client('s3')
    response = s3client.put_object(Body=content.html_content,
                                   Bucket=BUCKET,
                                   Key=key,
                                   Metadata={'url': url})
    print(response)
