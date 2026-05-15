import json
import boto3
import urllib.parse
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
table = dynamodb.Table('music')

def get_secure_url(s3_url):
    try:
        if "s3.amazonaws.com" in s3_url:
            bucket = s3_url.split(".s3.amazonaws.com")[0].replace("https://", "")
            key = urllib.parse.unquote(s3_url.split(".s3.amazonaws.com/")[1])
            return s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
    except: pass
    return s3_url

def handle_music(method, query_params, headers):
    if method != "GET": return None
    
    title = query_params.get('title')
    year = query_params.get('year')
    artist = query_params.get('artist')
    album = query_params.get('album')

    if not any([title, year, artist, album]):
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"message": "At least one field must be completed."})
        }

    # Query Logic (Matches EC2 logic)
    if year and not any([title, artist, album]):
        items = table.query(IndexName='YearTitleGSI', KeyConditionExpression=Key('year').eq(year)).get('Items', [])
    elif artist and year and not any([title, album]):
        # lsi fix
        items = table.query(IndexName='ArtistYearLSI', KeyConditionExpression=Key('artist').eq(artist) & Key('year').eq(year)).get('Items', [])
    elif artist and not any([title, year, album]):
        items = table.query(KeyConditionExpression=Key('artist').eq(artist)).get('Items', [])
    else:
        f = None
        if title: f = Attr('title').eq(title) if f is None else f & Attr('title').eq(title)
        if artist: f = Attr('artist').eq(artist) if f is None else f & Attr('artist').eq(artist)
        if year: f = Attr('year').eq(year) if f is None else f & Attr('year').eq(year)
        if album: f = Attr('album').eq(album) if f is None else f & Attr('album').eq(album)
        items = table.scan(FilterExpression=f).get('Items', [])

    if not items:
        return {
            "statusCode": 404,
            "headers": headers,
            "body": json.dumps({"message": "No result is retrieved. Please query again"})
        }

    for i in items:
        i['image_url'] = get_secure_url(i['image_url'])

    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps({"results": items})
    }
