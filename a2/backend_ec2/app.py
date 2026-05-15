from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key, Attr
import urllib.parse

app = Flask(__name__)
CORS(app) 

REGION = "us-east-1"
dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)

def get_secure_image_url(s3_url):
    try:
        if "s3.amazonaws.com" in s3_url:
            bucket_name = s3_url.split(".s3.amazonaws.com")[0].replace("https://", "")
            object_key = urllib.parse.unquote(s3_url.split(".s3.amazonaws.com/")[1])
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=3600 
            )
            return presigned_url
    except Exception:
        pass
    return s3_url

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    table = dynamodb.Table('login')
    response = table.get_item(Key={'email': data.get('email')})
    if 'Item' in response and response['Item']['password'] == data.get('password'):
        return jsonify({"message": "Login successful", "user_name": response['Item']['user_name'], "email": response['Item']['email']}), 200
    return jsonify({"message": "email or password is invalid"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    table = dynamodb.Table('login')
    if 'Item' in table.get_item(Key={'email': data.get('email')}):
        return jsonify({"message": "The email already exists"}), 400
    table.put_item(Item={'email': data.get('email'), 'user_name': data.get('user_name'), 'password': data.get('password')})
    return jsonify({"message": "Registration successful"}), 201

@app.route('/api/music', methods=['GET'])
def query_music():
    title = request.args.get('title')
    artist = request.args.get('artist')
    year = request.args.get('year')
    album = request.args.get('album')
    
    if not any([title, artist, year, album]):
        return jsonify({"message": "At least one field must be completed."}), 400
        
    table = dynamodb.Table('music')
    
    # Optimized Query Routing
    if artist:
        if year:
            query_kwargs = {"IndexName": "ArtistYearLSI", "KeyConditionExpression": Key('artist').eq(artist) & Key('year').eq(year)}
        else:
            query_kwargs = {"KeyConditionExpression": Key('artist').eq(artist)}
        f = None
        if title: f = Attr('title').eq(title)
        if album: f = f & Attr('album').eq(album) if f else Attr('album').eq(album)
        if f: query_kwargs['FilterExpression'] = f
        items = table.query(**query_kwargs).get('Items', [])
    elif year:
        query_kwargs = {"IndexName": "YearTitleGSI"}
        if title:
            query_kwargs["KeyConditionExpression"] = Key('year').eq(year) & Key('title').eq(title)
            if album: query_kwargs['FilterExpression'] = Attr('album').eq(album)
        else:
            query_kwargs["KeyConditionExpression"] = Key('year').eq(year)
            if album: query_kwargs['FilterExpression'] = Attr('album').eq(album)
        items = table.query(**query_kwargs).get('Items', [])
    else:
        f = None
        if title: f = Attr('title').eq(title)
        if album: f = f & Attr('album').eq(album) if f else Attr('album').eq(album)
        items = table.scan(FilterExpression=f).get('Items', [])
        
    if not items:
        return jsonify({"message": "No result is retrieved. Please query again"}), 404
    for item in items:
        if 'image_url' in item: item['image_url'] = get_secure_image_url(item['image_url'])
    return jsonify({"results": items}), 200

@app.route('/api/subscriptions', methods=['GET', 'POST', 'DELETE'])
def manage_subscriptions():
    table = dynamodb.Table('subscriptions')
    if request.method == 'GET':
        email = request.args.get('email')
        response = table.query(KeyConditionExpression=Key('email').eq(email))
        subs = response.get('Items', [])
        for sub in subs:
            if 'song_data' in sub and 'image_url' in sub['song_data']:
                sub['song_data']['image_url'] = get_secure_image_url(sub['song_data']['image_url'])
        return jsonify({"subscriptions": subs}), 200
    data = request.json
    if request.method == 'POST':
        table.put_item(Item={'email': data.get('email'), 'title_album': data.get('title_album'), 'song_data': data.get('song_data')})
        return jsonify({"message": "Subscribed successfully"}), 201
    if request.method == 'DELETE':
        table.delete_item(Key={'email': data.get('email'), 'title_album': data.get('title_album')})
        return jsonify({"message": "Subscription removed"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
