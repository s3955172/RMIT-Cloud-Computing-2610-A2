import json
import boto3

REGION = "us-east-1"
TABLE_NAME = "music"
JSON_FILE = "2026a2_songs.json"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)


def make_song_key(title, album, year):
    return f"{title}#{album}#{year}"


def get_all_dynamodb_items():
    items = []

    response = table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    return items


def verify_music_data():
    print("Checking music data...")

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        print(f"Could not find {JSON_FILE}. Make sure it is in the same folder.")
        return

    songs = data["songs"]
    dynamodb_items = get_all_dynamodb_items()

    expected_keys = set()
    actual_keys = set()

    for song in songs:
        artist = song["artist"]
        title = song["title"]
        album = song["album"]
        year = str(song["year"])

        title_album_year = make_song_key(title, album, year)
        expected_keys.add((artist, title_album_year))

    for item in dynamodb_items:
        artist = item.get("artist")
        title_album_year = item.get("title_album_year")

        if artist and title_album_year:
            actual_keys.add((artist, title_album_year))

    missing_songs = expected_keys - actual_keys
    extra_songs = actual_keys - expected_keys

    print(f"Songs in JSON file: {len(expected_keys)}")
    print(f"Songs in DynamoDB: {len(actual_keys)}")

    if not missing_songs and not extra_songs:
        print("Verification passed. All songs were loaded correctly.")
    else:
        print("Verification found some issues.")

        if missing_songs:
            print()
            print("Missing songs:")
            for artist, key in list(missing_songs)[:10]:
                print(f"{artist} - {key}")

        if extra_songs:
            print()
            print("Extra songs in DynamoDB:")
            for artist, key in list(extra_songs)[:10]:
                print(f"{artist} - {key}")


if __name__ == "__main__":
    verify_music_data()