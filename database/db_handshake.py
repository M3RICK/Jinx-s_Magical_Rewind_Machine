import boto3
import os
from dotenv import load_dotenv
from boto3.resources.base import ServiceResource
from botocore.exceptions import ClientError, EndpointConnectionError

def get_dynamodb_reasources() -> ServiceResource:
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION"))

    if not dynamodb:
        raise ValueError("Can't connect to Database")
    return dynamodb

def test_connection(dynamodb: ServiceResource) -> bool:
    try:
        print(list(dynamodb.tables.all()))
        print("Connection succes")
        return True
    except EndpointConnectionError:
        print("Connection Error")
    except ClientError as e:
        print(f"AWS : {e.response['Error']['Message']}")
    except Exception as e:
        print(f"Error: {e}")
    return False

if __name__ == '__main__':
    load_dotenv()
    db = get_dynamodb_reasources()
    test_connection(db)
