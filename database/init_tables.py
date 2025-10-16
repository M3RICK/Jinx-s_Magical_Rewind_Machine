import boto3
from botocore.exceptions import ClientError
from db_handshake import get_dynamodb_reasources


dynamodb = get_dynamodb_reasources()

def create_players_table():
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

def create_match_table():
    table_name = "Matchs"

    try:
        existing_table = dynamodb.Table(table_name)
        existing_table.load()
        print(f"✓ Table '{table_name}' already exists. Skipping creation.")
        return existing_table

    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise

    print(f"Creating table '{table_name}'...")

    try:
        table = dynamodb.create_table(
            TableName=table_name,

            # We use a COMPOSITE KEY (partition + sort key)
            # This lets us query "all matches for a specific player"
            KeySchema=[
                {
                    'AttributeName': 'puuid',      # Partition key: which player
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'match_id',   # Sort key: unique match ID
                    'KeyType': 'RANGE'
                }
            ],

            # Define types for KEYS ONLY (other fields are flexible)
            AttributeDefinitions=[
                {
                    'AttributeName': 'puuid',
                    'AttributeType': 'S'           # String
                },
                {
                    'AttributeName': 'match_id',
                    'AttributeType': 'S'           # String (Riot match IDs are like "NA1_4567890123")
                }
            ],

            BillingMode='PAY_PER_REQUEST'

            # Other fields (champion, role, kills, deaths, assists, win/lose, timestamp, rank)
            # will be stored as flexible attributes - no need to define them here!
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
    create_match_table()

    # TODO: Add more tables here later (Matches, Insights, etc.)

    print("\n✓ Database initialization complete!")


if __name__ == "__main__":
    init_all_tables()
