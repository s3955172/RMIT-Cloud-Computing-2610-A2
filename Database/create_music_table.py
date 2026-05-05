import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
TABLE_NAME = "music"

dynamodb = boto3.resource("dynamodb", region_name=REGION)


def create_music_table():
    print("Creating music table...")

    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "artist", "KeyType": "HASH"},
                {"AttributeName": "title_album_year", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "artist", "AttributeType": "S"},
                {"AttributeName": "title_album_year", "AttributeType": "S"},
                {"AttributeName": "year", "AttributeType": "S"},
                {"AttributeName": "title", "AttributeType": "S"}
            ],
            LocalSecondaryIndexes=[
                {
                    "IndexName": "ArtistYearLSI",
                    "KeySchema": [
                        {"AttributeName": "artist", "KeyType": "HASH"},
                        {"AttributeName": "year", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "TitleYearGSI",
                    "KeySchema": [
                        {"AttributeName": "title", "KeyType": "HASH"},
                        {"AttributeName": "year", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )

        print("Waiting for the table to become active...")
        table.wait_until_exists()
        print("Music table created successfully.")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("Music table already exists.")
        else:
            print("Could not create the music table.")
            print(e)


if __name__ == "__main__":
    create_music_table()