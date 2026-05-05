import boto3
from botocore.exceptions import ClientError

STUDENT_ID = "s3955172"
STUDENT_NAME = "Egor Zvyagin"
REGION = "us-east-1"

dynamodb = boto3.resource('dynamodb', region_name=REGION)

def create_and_populate_login():
    print("--- Step 1: Creating Login Table ---")
    try:
        table = dynamodb.create_table(
            TableName='login',
            KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("Waiting for 'login' table to be created...")
        table.wait_until_exists()
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Login table already exists.")
            table = dynamodb.Table('login')
        else: raise e

    print("Populating 10 users...")
    passwords = ["012345", "123456", "234567", "345678", "456789", "567890", "678901", "789012", "890123", "901234"]
    
    with table.batch_writer() as batch:
        for i in range(10):
            batch.put_item(Item={
                'email': f"{STUDENT_ID}{i}@student.rmit.edu.au",
                'user_name': f"{STUDENT_NAME}{i}",
                'password': passwords[i]
            })
    print("Success: 10 users added to login table.")

if __name__ == "__main__":
    create_and_populate_login()
