import boto3
from botocore.exceptions import ClientError

STUDENT_ID = "s3955172"
STUDENT_NAME = "Egor Zvyagin"
REGION = "us-east-1"

dynamodb = boto3.resource('dynamodb', region_name=REGION)

def create_tables():
    # ==========================================
    # 1. Create Login Table
    # ==========================================
    print("--- Step 1a: Creating Login Table ---")
    try:
        login_table = dynamodb.create_table(
            TableName='login',
            KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("Waiting for 'login' table to be created...")
        login_table.wait_until_exists()
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Login table already exists.")
            login_table = dynamodb.Table('login')
        else: raise e

    print("Populating 10 users...")
    passwords = ["012345", "123456", "234567", "345678", "456789", "567890", "678901", "789012", "890123", "901234"]
    
    with login_table.batch_writer() as batch:
        for i in range(10):
            batch.put_item(Item={
                'email': f"{STUDENT_ID}{i}@student.rmit.edu.au",
                'user_name': f"{STUDENT_NAME}{i}",
                'password': passwords[i]
            })
    print("Success: 10 users added to login table.")

    # ==========================================
    # 2. Create Subscriptions Table
    # ==========================================
    print("--- Step 1b: Creating Subscriptions Table ---")
    try:
        sub_table = dynamodb.create_table(
            TableName='subscriptions',
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}, 
                {'AttributeName': 'title_album', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'}, 
                {'AttributeName': 'title_album', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("Waiting for 'subscriptions' table to be created...")
        sub_table.wait_until_exists()
        print("Success: Subscriptions table created.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Subscriptions table already exists.")
        else: raise e

if __name__ == "__main__":
    create_tables()
