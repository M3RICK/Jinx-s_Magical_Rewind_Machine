import boto3
from dotenv import load_dotenv
import os

load_dotenv()

def get_dynamodb_reasources():
    region = os.getenv('AWS_DEFAULT_REGION')

    if not region:
        raise ValueError(
            "AWS_DEFAULT_REGION not found in environment variables! "
            "Make sure .env file exists and contains the correct reigon"
        )
    return boto3.resource('dynamodb', region_name=region)

def test_dynamodb_connection():
    try:
        dynamodb = get_dynamodb_reasources()
        client = dynamodb.meta.client
        response = client.list_tables()

        print(f"Tables found: {len(response['TableNames'])}")
        if response['TableNames']:
            print("\nYour tables:")
            for table_name in response['TableNames']:
                print(f"  - {table_name}")
        else:
            print("No tables found")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_dynamodb_connection()