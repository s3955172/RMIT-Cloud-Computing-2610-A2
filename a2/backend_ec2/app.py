from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

app = Flask(__name__)
# Enable CORS so our frontend can communicate with this backend
CORS(app)

REGION = "us-east-1"
dynamodb = boto3.resource('dynamodb', region_name=REGION)

# ==========================================
# SETUP: Ensure Subscriptions table exists
# ==========================================
def ensure_subscription_table():
    try:
        table = dynamodb.create_table(
            TableName='subscriptions',
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'},
                {'AttributeName': 'title_album', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'},
                {'AttributeName': 'title_album', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        table.wait_until_exists()
    except ClientError as e:
        pass # Table already exists

ensure_subscription_table()

# ==========================================
# ROUTES: Authentication
# ==========================================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    table = dynamodb.Table('login')
    response = table.get_item(Key={'email': email})
    
    if 'Item' in response:
        user = response['Item']
        if user['password'] == password:
            return jsonify({"message": "Login successful", "user_name": user['user_name'], "email": user['email']}), 200
    
    return jsonify({"message": "email or password is invalid"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    user_name = data.get('user_name')
    password = data.get('password')
    
    table = dynamodb.Table('login')
    
    # Check if exists
    if 'Item' in table.get_item(Key={'email': email}):
        return jsonify({"message": "The email already exists"}), 400
        
    table.put_item(Item={'email': email, 'user_name': user_name, 'password': password})
    return jsonify({"message": "Registration successful"}), 201

# ==========================================
# ROUTES: Music & Subscriptions
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
    
    # Implementation of Query vs Scan as per requirements
    if year and not artist and not title and not album:
        # Use GSI (Global Secondary Index) if only year is provided
        response = table.query(
            IndexName='YearTitleGSI',
            KeyConditionExpression=Key('year').eq(year)
        )
        items = response.get('Items', [])
    elif artist and not title and not year and not album:
        # Use Base Table Query if only artist is provided
        response = table.query(KeyConditionExpression=Key('artist').eq(artist))
        items = response.get('Items', [])
    else:
        # Use Scan with FilterExpression for complex/multiple conditions
        filter_exp = None
        if title: filter_exp = Attr('title').eq(title) if filter_exp is None else filter_exp & Attr('title').eq(title)
        if artist: filter_exp = Attr('artist').eq(artist) if filter_exp is None else filter_exp & Attr('artist').eq(artist)
        if year: filter_exp = Attr('year').eq(year) if filter_exp is None else filter_exp & Attr('year').eq(year)
        if album: filter_exp = Attr('album').eq(album) if filter_exp is None else filter_exp & Attr('album').eq(album)
        
        response = table.scan(FilterExpression=filter_exp)
        items = response.get('Items', [])
        
    if not items:
        return jsonify({"message": "No result is retrieved. Please query again"}), 404
        
    return jsonify({"results": items}), 200

@app.route('/api/subscriptions', methods=['GET', 'POST', 'DELETE'])
def manage_subscriptions():
    table = dynamodb.Table('subscriptions')
    email = request.args.get('email') if request.method == 'GET' else request.json.get('email')
    
    if request.method == 'GET':
        response = table.query(KeyConditionExpression=Key('email').eq(email))
        return jsonify({"subscriptions": response.get('Items', [])}), 200
        
    title_album = request.json.get('title_album')
    
    if request.method == 'POST':
        song_data = request.json.get('song_data') # Store full song info to display easily
        table.put_item(Item={
            'email': email,
            'title_album': title_album,
            'song_data': song_data
        })
        return jsonify({"message": "Subscribed!"}), 201
        
    if request.method == 'DELETE':
        table.delete_item(Key={'email': email, 'title_album': title_album})
        return jsonify({"message": "Removed!"}), 200

if __name__ == '__main__':
    # Listen on all interfaces, port 80
    app.run(host='0.0.0.0', port=80)
