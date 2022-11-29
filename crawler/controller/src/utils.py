import uuid

from datetime import datetime


def generate_crawl_id():
    ts = datetime.fromtimestamp(datetime.timestamp(datetime.now()), tz=None)
    uid = uuid.uuid4()

    return str(ts) + '-' + str(uid)
