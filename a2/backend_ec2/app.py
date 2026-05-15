from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key, Attr
import urllib.parse

app = Flask(__name__)
# Enable CORS so the frontend can communicate with the backend
CORS(app) 

REGION = "us-east-1"
dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)

# ==========================================
# REQUIREMENT: Secure S3 Access (Presigned URLs)
# ==========================================
def get_secure_image_url(s3_url):
    """ Converts a private S3 URL into a secure, temporary Presigned URL """
    try:
        if "s3.amazonaws.com" in s3_url:
            bucket_name = s3_url.split(".s3.amazonaws.com")[0].replace("https://", "")
            object_key = urllib.parse.unquote(s3_url.split(".s3.amazonaws.com/")[1])
            
            # Generate a presigned URL valid for 1 hour
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=3600 
            )
            return presigned_url
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
    return s3_url

# ==========================================
# LOGIN AND REGISTER ROUTES
# ==========================================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    table = dynamodb.Table('login')
    response = table.get_item(Key={'email': data.get('email')})
    
    if 'Item' in response and response['Item']['password'] == data.get('password'):
        return jsonify({
            "message": "Login successful", 
            "user_name": response['Item']['user_name'], 
            "email": response['Item']['email']
        }), 200
            
    return jsonify({"message": "email or password is invalid"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    table = dynamodb.Table('login')
    
    if 'Item' in table.get_item(Key={'email': data.get('email')}):
        return jsonify({"message": "The email already exists"}), 400
        
    table.put_item(Item={
        'email': data.get('email'), 
        'user_name': data.get('user_name'), 
        'password': data.get('password')
    })
    return jsonify({"message": "Registration successful"}), 201

# ==========================================
# MAIN PAGE: QUERY ROUTE
# ==========================================
@app.route('/api/music', methods=['GET'])
def query_music():
    title = request.args.get('title')
    artist = request.args.get('artist')
    year = request.args.get('year')
    album = request.args.get('album')
    
    if not any([title, artist, year, album]):
        return jsonify({"message": "At least one field must be completed."}), 400
        
    table = dynamodb.Table('music')
    
    if year and not artist and not title and not album:
        response = table.query(IndexName='YearTitleGSI', KeyConditionExpression=Key('year').eq(year))
    elif artist and not title and not year and not album:
        response = table.query(KeyConditionExpression=Key('artist').eq(artist))
    else:
        filter_exp = None
        if title: filter_exp = Attr('title').eq(title) if filter_exp is None else filter_exp & Attr('title').eq(title)
        if artist: filter_exp = Attr('artist').eq(artist) if filter_exp is None else filter_exp & Attr('artist').eq(artist)
        if year: filter_exp = Attr('year').eq(year) if filter_exp is None else filter_exp & Attr('year').eq(year)
        if album: filter_exp = Attr('album').eq(album) if filter_exp is None else filter_exp & Attr('album').eq(album)
        response = table.scan(FilterExpression=filter_exp)
        
    items = response.get('Items', [])
    if not items:
        return jsonify({"message": "No result is retrieved. Please query again"}), 404
        
    # Apply secure Presigned URLs to all search results
    for item in items:
        if 'image_url' in item:
            item['image_url'] = get_secure_image_url(item['image_url'])
            
    return jsonify({"results": items}), 200

# ==========================================
# MAIN PAGE: SUBSCRIPTION ROUTES
# ==========================================
@app.route('/api/subscriptions', methods=['GET', 'POST', 'DELETE'])
def manage_subscriptions():
    table = dynamodb.Table('subscriptions')
    
    if request.method == 'GET':
        email = request.args.get('email')
        response = table.query(KeyConditionExpression=Key('email').eq(email))
        subs = response.get('Items', [])
        
        # Apply secure Presigned URLs to subscriptions list
        for sub in subs:
            if 'song_data' in sub and 'image_url' in sub['song_data']:
                sub['song_data']['image_url'] = get_secure_image_url(sub['song_data']['image_url'])
                
        return jsonify({"subscriptions": subs}), 200
        
    data = request.json
    if request.method == 'POST':
        table.put_item(Item={
            'email': data.get('email'),
            'title_album': data.get('title_album'),
            'song_data': data.get('song_data')
        })
        return jsonify({"message": "Subscribed successfully"}), 201
        
    if request.method == 'DELETE':
        table.delete_item(Key={'email': data.get('email'), 'title_album': data.get('title_album')})
        return jsonify({"message": "Subscription removed"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
