import json
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
TABLE_NAME = "music"
JSON_FILE = "2026a2_songs.json"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)


def make_song_key(title, album, year):
    return f"{title}#{album}#{year}"


def load_music_data():
    print("Starting music data loading...")

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        print(f"Could not find {JSON_FILE}. Make sure it is in the same folder.")
        return

    songs = data["songs"]

    inserted_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Found {len(songs)} songs in the JSON file.")

    for song in songs:
        title = song["title"]
        artist = song["artist"]
        year = str(song["year"])
        album = song["album"]
        image_url = song["img_url"]

        title_album_year = make_song_key(title, album, year)

        item = {
            "artist": artist,
            "title_album_year": title_album_year,
            "title": title,
            "year": year,
            "album": album,
            "image_url": image_url
        }

        try:
            table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(artist) AND attribute_not_exists(title_album_year)"
            )

            inserted_count += 1
            print(f"Inserted: {title} by {artist}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                skipped_count += 1
                print(f"Skipped duplicate: {title} by {artist}")
            else:
                error_count += 1
                print(f"Error inserting: {title} by {artist}")
                print(e)

    print()
    print("Music data loading finished.")
    print(f"Inserted songs: {inserted_count}")
    print(f"Skipped duplicates: {skipped_count}")
    print(f"Errors: {error_count}")


if __name__ == "__main__":
    load_music_data()