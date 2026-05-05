import boto3
import json
import requests
import os
from botocore.exceptions import ClientError

STUDENT_ID = "s3955172"
REGION = "us-east-1"
S3_BUCKET_NAME = f"music-app-images-{STUDENT_ID}"

dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def setup_s3_and_upload():
    print("--- Step 4: Uploading Images to S3 ---")
    
    # 1. Create S3 Bucket
    try:
        print(f"Creating bucket: {S3_BUCKET_NAME}")
        if REGION == 'us-east-1': s3.create_bucket(Bucket=S3_BUCKET_NAME)
        else: s3.create_bucket(Bucket=S3_BUCKET_NAME, CreateBucketConfiguration={'LocationConstraint': REGION})
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            pass # Bucket already exists
        else: raise e

    # 2. Download from JSON and Upload to S3
    table = dynamodb.Table('music')
    with open('2026a2_songs.json', 'r') as f:
        songs = json.load(f)['songs']

    print("Downloading and uploading images. This may take a minute...")
    for song in songs:
        title, artist, album, img_url = song['title'], song['artist'], song['album'], song['img_url']
        img_name = os.path.basename(img_url)
        
        # Download
        resp = requests.get(img_url, stream=True)
        if resp.status_code == 200:
            # Upload to S3
            s3.upload_fileobj(resp.raw, S3_BUCKET_NAME, img_name)
            s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{img_name}"
            
            # Update DynamoDB with the new S3 link
            table.update_item(
                Key={'artist': artist, 'title_album': f"{title}#{album}"},
                UpdateExpression="set image_url = :u",
                ExpressionAttributeValues={':u': s3_url}
            )
            print(f"Uploaded: {img_name}")
            
    print("Success: All images uploaded to S3 and DynamoDB updated.")

if __name__ == "__main__":
    setup_s3_and_upload()
