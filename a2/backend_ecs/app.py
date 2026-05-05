from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key, Attr

app = Flask(__name__)
# Enable CORS so the frontend can communicate with the backend
CORS(app) 

REGION = "us-east-1"
dynamodb = boto3.resource('dynamodb', region_name=REGION)

# ==========================================
# 1 & 2. LOGIN AND REGISTER ROUTES
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
            
    # Exact error message required by the assignment
    return jsonify({"message": "email or password is invalid"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    table = dynamodb.Table('login')
    
    # Validate unique email
    if 'Item' in table.get_item(Key={'email': data.get('email')}):
        # Exact error message required by the assignment
        return jsonify({"message": "The email already exists"}), 400
        
    table.put_item(Item={
        'email': data.get('email'), 
        'user_name': data.get('user_name'), 
        'password': data.get('password')
    })
    return jsonify({"message": "Registration successful"}), 201

# ==========================================
# 3. MAIN PAGE: QUERY ROUTE
# ==========================================
@app.route('/api/music', methods=['GET'])
def query_music():
    title = request.args.get('title')
    artist = request.args.get('artist')
    year = request.args.get('year')
    album = request.args.get('album')
    
    # Requirement: At least one field must be completed
    if not any([title, artist, year, album]):
        return jsonify({"message": "At least one field must be completed."}), 400
        
    table = dynamodb.Table('music')
    
    # Requirement: Query and Scan operations implemented appropriately
    if year and not artist and not title and not album:
        # Use Global Secondary Index if querying only by year
        response = table.query(IndexName='YearTitleGSI', KeyConditionExpression=Key('year').eq(year))
    elif artist and not title and not year and not album:
        # Use Partition Key if querying only by artist
        response = table.query(KeyConditionExpression=Key('artist').eq(artist))
    else:
        # Use Scan with FilterExpression for multiple conditions (ANDed by default)
        filter_exp = None
        if title: filter_exp = Attr('title').eq(title) if filter_exp is None else filter_exp & Attr('title').eq(title)
        if artist: filter_exp = Attr('artist').eq(artist) if filter_exp is None else filter_exp & Attr('artist').eq(artist)
        if year: filter_exp = Attr('year').eq(year) if filter_exp is None else filter_exp & Attr('year').eq(year)
        if album: filter_exp = Attr('album').eq(album) if filter_exp is None else filter_exp & Attr('album').eq(album)
        
        response = table.scan(FilterExpression=filter_exp)
        
    items = response.get('Items', [])
    if not items:
        # Exact error message required by the assignment
        return jsonify({"message": "No result is retrieved. Please query again"}), 404
        
    return jsonify({"results": items}), 200

# ==========================================
# 3. MAIN PAGE: SUBSCRIPTION ROUTES
# ==========================================
@app.route('/api/subscriptions', methods=['GET', 'POST', 'DELETE'])
def manage_subscriptions():
    table = dynamodb.Table('subscriptions')
    
    if request.method == 'GET':
        email = request.args.get('email')
        response = table.query(KeyConditionExpression=Key('email').eq(email))
        return jsonify({"subscriptions": response.get('Items', [])}), 200
        
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
    # Ensure web application runs on standard HTTP port 80
    app.run(host='0.0.0.0', port=80)
