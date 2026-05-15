import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('login')

def handle_auth(path, method, body, headers):
    if path == "/login" and method == "POST":
        item = table.get_item(Key={'email': body.get('email')}).get('Item')
        if item and item['password'] == body.get('password'):
            return {"statusCode": 200, "headers": headers, "body": json.dumps({"user_name": item['user_name'], "email": item['email']})}
        return {"statusCode": 401, "headers": headers, "body": json.dumps({"message": "email or password is invalid"})}

    elif path == "/register" and method == "POST":
        email = body.get('email')
        if 'Item' in table.get_item(Key={'email': email}):
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"message": "The email already exists"})}
        table.put_item(Item={'email': email, 'user_name': body.get('user_name'), 'password': body.get('password')})
        return {"statusCode": 201, "headers": headers, "body": json.dumps({"message": "Registration successful"})}
    return None
