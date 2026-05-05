import boto3
import json
import requests
import os
from botocore.exceptions import ClientError

# --- CONFIGURATION (Update these with your actual details) ---
REGION = "us-east-1"  
S3_BUCKET_NAME = "music-app-images-s31234567"  # Replace with your student ID
STUDENT_ID = "s31234567"                       # Replace with your student ID
STUDENT_NAME = "John Doe"                      # Replace with your Name
SONGS_FILE = "2026a2_songs.json"

# --- AWS CLIENTS ---
# In AWS Academy, use 'LabRole' if running on an EC2, or your CLI credentials locally
dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def create_login_table():
    """Creates the login table for user authentication."""
    print(">>> Creating 'login' table...")
    try:
        table = dynamodb.create_table(
            TableName='login',
            KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        table.wait_until_exists()
        print("Success: 'login' table created.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Notice: 'login' table already exists.")
        else: raise e

def populate_login_table():
    """Adds the 10 required student login entities."""
    print(">>> Populating 'login' table...")
    table = dynamodb.Table('login')
    passwords = ["012345", "123456", "234567", "345678", "456789", "567890", "678901", "789012", "890123", "901234"]
    
    with table.batch_writer() as batch:
        for i in range(10):
            batch.put_item(
                Item={
                    'email': f"{STUDENT_ID}{i}@student.rmit.edu.au",
                    'user_name': f"{STUDENT_NAME}{i}",
                    'password': passwords[i]
                }
            )
    print(f"Success: 10 users added for {STUDENT_NAME}.")

def create_music_table():
    """Creates the music table with required GSI and LSI."""
    print(">>> Creating 'music' table...")
    try:
        # Schema: Artist (PK), Title (SK)
        # LSI: Artist (PK), Year (SK) - To sort an artist's songs by year
        # GSI: Year (PK), Title (SK) - To find all songs from a specific year across all artists
        table = dynamodb.create_table(
            TableName='music',
            KeySchema=[
                {'AttributeName': 'artist', 'KeyType': 'HASH'},
                {'AttributeName': 'title', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'artist', 'AttributeType': 'S'},
                {'AttributeName': 'title', 'AttributeType': 'S'},
                {'AttributeName': 'year', 'AttributeType': 'S'}
            ],
            LocalSecondaryIndexes=[
                {
                    'IndexName': 'ArtistYearIndex',
                    'KeySchema': [
                        {'AttributeName': 'artist', 'KeyType': 'HASH'},
                        {'AttributeName': 'year', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'YearTitleIndex',
                    'KeySchema': [
                        {'AttributeName': 'year', 'KeyType': 'HASH'},
                        {'AttributeName': 'title', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        table.wait_until_exists()
        print("Success: 'music' table created with indexes.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Notice: 'music' table already exists.")
        else: raise e

def create_subscriptions_table():
    """Creates a table to store user subscriptions (Email + SongTitle)."""
    print(">>> Creating 'subscriptions' table...")
    try:
        table = dynamodb.create_table(
            TableName='subscriptions',
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'},
                {'AttributeName': 'artist_title', 'KeyType': 'RANGE'} # Composite SK: "Artist|Title"
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'},
                {'AttributeName': 'artist_title', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        table.wait_until_exists()
        print("Success: 'subscriptions' table created.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Notice: 'subscriptions' table already exists.")
        else: raise e

def create_s3_bucket():
    """Creates the S3 bucket to host artist images."""
    print(f">>> Creating S3 bucket: {S3_BUCKET_NAME}...")
    try:
        if REGION == 'us-east-1':
            s3.create_bucket(Bucket=S3_BUCKET_NAME)
        else:
            s3.create_bucket(
                Bucket=S3_BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
        print("Success: Bucket created.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print("Notice: Bucket already owned by you.")
        elif e.response['Error']['Code'] == 'BucketAlreadyExists':
            print("Error: Bucket name is taken globally. Choose a more unique name.")
        else: raise e

def migrate_songs():
    """Downloads images, uploads to S3, and populates the music table."""
    print(">>> Migrating songs and images...")
    if not os.path.exists(SONGS_FILE):
        print(f"Error: {SONGS_FILE} not found!")
        return

    with open(SONGS_FILE, 'r') as f:
        data = json.load(f)
    
    table = dynamodb.Table('music')
    
    for song in data['songs']:
        # Download Image
        img_url = song['img_url']
        img_name = os.path.basename(img_url)
        
        try:
            print(f"Processing: {song['title']} - {song['artist']}")
            img_data = requests.get(img_url, stream=True).raw
            s3.upload_fileobj(img_data, S3_BUCKET_NAME, img_name)
            
            # Construct S3 Object URL
            s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{img_name}"
            
            # Write to DynamoDB
            table.put_item(
                Item={
                    'artist': song['artist'],
                    'title': song['title'],
                    'year': song['year'],
                    'album': song['album'],
                    'image_url': s3_url
                }
            )
        except Exception as e:
            print(f"Failed to process {song['title']}: {e}")

if __name__ == "__main__":
    create_login_table()
    populate_login_table()
    create_music_table()
    create_subscriptions_table()
    create_s3_bucket()
    migrate_songs()
    print("\nInitialization Complete. You are ready for Phase 2!")
