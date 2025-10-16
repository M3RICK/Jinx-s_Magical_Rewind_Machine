import boto3
from botocore.exceptions import ClientError
from db_handshake import get_dynamodb_reasources


def create_players_table():
    dynamodb = get_dynamodb_reasources()
    table_name = "Players"

    try:
        existing_table = dynamodb.Table(table_name)
        existing_table.load()  # This will throw an exception if table doesn't exist
        print(f"✓ Table '{table_name}' already exists. Skipping creation.")
        return existing_table

    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise

    print(f"Creating table '{table_name}'...")

    try:
        table = dynamodb.create_table(
            TableName=table_name,

            KeySchema=[
                {
                    'AttributeName': 'puuid',  # The attribute name
                    'KeyType': 'HASH'          # HASH = partition key, RANGE = sort key
                }
            ],

            AttributeDefinitions=[
                {
                    'AttributeName': 'puuid',
                    'AttributeType': 'S'       # S = String, N = Number, B = Binary
                }
            ],

            BillingMode='PAY_PER_REQUEST'
        )

        print(f"Waiting for table '{table_name}' to be ready...")
        table.wait_until_exists()
        print(f"✓ Table '{table_name}' created successfully!")
        return table

    except ClientError as e:
        print(f"Error: {e.response['Error']['Message']}")
        raise


def init_all_tables():
    print("Starting database initialization...\n")
    create_players_table()

    # TODO: Add more tables here later (Matches, Insights, etc.)

    print("\n✓ Database initialization complete!")


if __name__ == "__main__":
    init_all_tables()
