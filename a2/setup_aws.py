import boto3
import json
import requests
import os

# --- CONFIGURED FOR YOU ---
STUDENT_ID = "s3955172"
STUDENT_NAME = "Egor Zvyagin"
# --------------------------

REGION = "us-east-1"
S3_BUCKET_NAME = f"music-app-images-{STUDENT_ID}"

dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def setup():
    print("1. Creating Login Table...")
    login_table = dynamodb.create_table(
        TableName='login',
        KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
    login_table.wait_until_exists()
    
    print("   Adding 10 users...")
    passwords = ["012345", "123456", "234567", "345678", "456789", "567890", "678901", "789012", "890123", "901234"]
    with login_table.batch_writer() as batch:
        for i in range(10):
            batch.put_item(Item={'email': f"{STUDENT_ID}{i}@student.rmit.edu.au", 'user_name': f"{STUDENT_NAME}{i}", 'password': passwords[i]})

    print("2. Creating Music Table (with required indexes)...")
    music_table = dynamodb.create_table(
        TableName='music',
        KeySchema=[{'AttributeName': 'artist', 'KeyType': 'HASH'}, {'AttributeName': 'title_album', 'KeyType': 'RANGE'}],
        AttributeDefinitions=[
            {'AttributeName': 'artist', 'AttributeType': 'S'},
            {'AttributeName': 'title_album', 'AttributeType': 'S'},
            {'AttributeName': 'year', 'AttributeType': 'S'},
            {'AttributeName': 'title', 'AttributeType': 'S'}
        ],
        LocalSecondaryIndexes=[{'IndexName': 'ArtistYearLSI', 'KeySchema': [{'AttributeName': 'artist', 'KeyType': 'HASH'}, {'AttributeName': 'year', 'KeyType': 'RANGE'}], 'Projection': {'ProjectionType': 'ALL'}}],
        GlobalSecondaryIndexes=[{'IndexName': 'YearTitleGSI', 'KeySchema': [{'AttributeName': 'year', 'KeyType': 'HASH'}, {'AttributeName': 'title', 'KeyType': 'RANGE'}], 'Projection': {'ProjectionType': 'ALL'}, 'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
    
    print("3. Creating Subscriptions Table...")
    try:
        sub_table = dynamodb.create_table(
            TableName='subscriptions',
            KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}, {'AttributeName': 'title_album', 'KeyType': 'RANGE'}],
            AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}, {'AttributeName': 'title_album', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        sub_table = dynamodb.Table('subscriptions')

    print("4. Creating S3 Bucket for Images...")
    try:
        if REGION == 'us-east-1': s3.create_bucket(Bucket=S3_BUCKET_NAME)
        else: s3.create_bucket(Bucket=S3_BUCKET_NAME, CreateBucketConfiguration={'LocationConstraint': REGION})
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass

    print("   Waiting for tables to be ready...")
    music_table.wait_until_exists()
    sub_table.wait_until_exists()

    print("5. Downloading images and saving to AWS...")
    with open('2026a2_songs.json', 'r') as f:
        songs = json.load(f)['songs']
    
    for song in songs:
        title, artist, year, album, img_url = song['title'], song['artist'], song['year'], song['album'], song['img_url']
        img_name = os.path.basename(img_url)
        
        resp = requests.get(img_url, stream=True)
        if resp.status_code == 200:
            s3.upload_fileobj(resp.raw, S3_BUCKET_NAME, img_name)
            s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{img_name}"
            
            music_table.put_item(Item={
                'artist': artist,
                'title_album': f"{title}#{album}", # Lossless key
                'title': title,
                'year': year,
                'album': album,
                'image_url': s3_url
            })
            print(f"   Uploaded: {title} by {artist}")

if __name__ == "__main__":
    try:
        setup()
        print("\nSUCCESS! Phase 1 is completely done.")
    except Exception as e:
        print(f"\nERROR: {e}")
