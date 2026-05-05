import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
dynamodb = boto3.resource('dynamodb', region_name=REGION)

def create_music_table():
    print("--- Step 2: Creating Music Table ---")
    try:
        # Key Schema Strategy:
        # Partition Key: artist
        # Sort Key: title_album (We combine title and album to prevent duplicate songs overwriting each other)
        table = dynamodb.create_table(
            TableName='music',
            KeySchema=[
                {'AttributeName': 'artist', 'KeyType': 'HASH'},
                {'AttributeName': 'title_album', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'artist', 'AttributeType': 'S'},
                {'AttributeName': 'title_album', 'AttributeType': 'S'},
                {'AttributeName': 'year', 'AttributeType': 'S'},
                {'AttributeName': 'title', 'AttributeType': 'S'}
            ],
            LocalSecondaryIndexes=[{
                'IndexName': 'ArtistYearLSI',
                'KeySchema': [{'AttributeName': 'artist', 'KeyType': 'HASH'}, {'AttributeName': 'year', 'KeyType': 'RANGE'}],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            GlobalSecondaryIndexes=[{
                'IndexName': 'YearTitleGSI',
                'KeySchema': [{'AttributeName': 'year', 'KeyType': 'HASH'}, {'AttributeName': 'title', 'KeyType': 'RANGE'}],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            }],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("Waiting for 'music' table to be created...")
        table.wait_until_exists()
        print("Success: Music table created with LSI and GSI.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Music table already exists.")
        else: raise e

if __name__ == "__main__":
    create_music_table()
