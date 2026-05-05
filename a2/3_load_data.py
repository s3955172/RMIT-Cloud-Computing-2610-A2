import boto3
import json
import os

REGION = "us-east-1"
dynamodb = boto3.resource('dynamodb', region_name=REGION)

def load_music_data():
    print("--- Step 3: Loading Data to DynamoDB ---")
    if not os.path.exists('2026a2_songs.json'):
        print("Error: 2026a2_songs.json file not found!")
        return

    table = dynamodb.Table('music')
    
    with open('2026a2_songs.json', 'r') as f:
        songs = json.load(f)['songs']

    print(f"Loading {len(songs)} songs into DynamoDB...")
    with table.batch_writer() as batch:
        for song in songs:
            # We create the composite key here to ensure lossless representation
            title_album = f"{song['title']}#{song['album']}"
            
            batch.put_item(Item={
                'artist': song['artist'],
                'title_album': title_album,
                'title': song['title'],
                'year': song['year'],
                'album': song['album'],
                'image_url': song['img_url'] # Initial raw URL, will be updated in Step 4
            })
    print("Success: All data loaded into music table.")

if __name__ == "__main__":
    load_music_data()
