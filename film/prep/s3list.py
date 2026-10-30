"""Minimal anonymous S3 ListObjectsV2 over HTTPS (no credentials needed for public buckets)."""
import re
import urllib.parse
import urllib.request


def list_keys(bucket, prefix, delimiter=None):
    keys, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if delimiter:
            q["delimiter"] = delimiter
        if token:
            q["continuation-token"] = token
        url = f"https://{bucket}.s3.amazonaws.com/?" + urllib.parse.urlencode(q)
        xml = urllib.request.urlopen(url, timeout=60).read().decode()
        keys += re.findall(r"<Key>([^<]+)</Key>", xml)
        keys += re.findall(r"<Prefix>([^<]+)</Prefix>", xml)[1:] if delimiter else []
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", xml)
        if not m:
            return keys
        token = m.group(1)
