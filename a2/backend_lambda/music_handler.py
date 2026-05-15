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
    title, year, artist, album = query_params.get('title'), query_params.get('year'), query_params.get('artist'), query_params.get('album')

    if not any([title, year, artist, album]):
        return {"statusCode": 400, "headers": headers, "body": json.dumps({"message": "At least one field must be completed."})}

    if artist:
        if year: query_kwargs = {"IndexName": "ArtistYearLSI", "KeyConditionExpression": Key('artist').eq(artist) & Key('year').eq(year)}
        else: query_kwargs = {"KeyConditionExpression": Key('artist').eq(artist)}
        f = None
        if title: f = Attr('title').eq(title)
        if album: f = f & Attr('album').eq(album) if f else Attr('album').eq(album)
        if f: query_kwargs['FilterExpression'] = f
        items = table.query(**query_kwargs).get('Items', [])
    elif year:
        query_kwargs = {"IndexName": "YearTitleGSI"}
        if title: query_kwargs["KeyConditionExpression"] = Key('year').eq(year) & Key('title').eq(title)
        else: query_kwargs["KeyConditionExpression"] = Key('year').eq(year)
        if album: query_kwargs['FilterExpression'] = Attr('album').eq(album)
        items = table.query(**query_kwargs).get('Items', [])
    else:
        f = None
        if title: f = Attr('title').eq(title)
        if album: f = f & Attr('album').eq(album) if f else Attr('album').eq(album)
        items = table.scan(FilterExpression=f).get('Items', [])

    if not items: return {"statusCode": 404, "headers": headers, "body": json.dumps({"message": "No result is retrieved. Please query again"})}
    for i in items: i['image_url'] = get_secure_url(i['image_url'])
    return {"statusCode": 200, "headers": headers, "body": json.dumps({"results": items})}
