import json
import boto3
import urllib.parse
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
table = dynamodb.Table('subscriptions')

def get_secure_url(s3_url):
    try:
        if "s3.amazonaws.com" in s3_url:
            bucket = s3_url.split(".s3.amazonaws.com")[0].replace("https://", "")
            key = urllib.parse.unquote(s3_url.split(".s3.amazonaws.com/")[1])
            return s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
    except: pass
    return s3_url

def handle_subscriptions(method, query_params, body, headers):
    if method == "GET":
        email = query_params.get('email')
        subs = table.query(KeyConditionExpression=Key('email').eq(email)).get('Items', [])
        for s in subs:
            if 'song_data' in s and 'image_url' in s['song_data']:
                s['song_data']['image_url'] = get_secure_url(s['song_data']['image_url'])
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"subscriptions": subs})}

    elif method == "POST":
        table.put_item(Item={
            'email': body.get('email'),
            'title_album': body.get('title_album'),
            'song_data': body.get('song_data')
        })
        return {"statusCode": 201, "headers": headers, "body": json.dumps({"message": "Subscribed successfully"})}

    elif method == "DELETE":
        table.delete_item(Key={
            'email': body.get('email'),
            'title_album': body.get('title_album')
        })
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"message": "Subscription removed"})}
    
    return None
