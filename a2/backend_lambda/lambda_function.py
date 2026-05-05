import json
from auth_handler import handle_auth
from music_handler import handle_music
from subscription_handler import handle_subscriptions

def lambda_handler(event, context):
    method = event.get('httpMethod')
    path = event.get('path')
    query_params = event.get('queryStringParameters') or {}
    
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event.get('body'))
        except:
            pass

    # Standard CORS headers required for API Gateway proxy integration
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,GET,POST,DELETE"
    }

    # Handle Preflight OPTIONS requests
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    response = None

    # Routing logic
    if path in ["/login", "/register"]:
        response = handle_auth(path, method, body, headers)
    elif path == "/music":
        response = handle_music(method, query_params, headers)
    elif path == "/subscriptions":
        response = handle_subscriptions(method, query_params, body, headers)

    if response:
        return response

    return {
        "statusCode": 404,
        "headers": headers,
        "body": json.dumps({"message": "Resource not found"})
    }
