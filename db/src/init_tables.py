import boto3
from botocore.exceptions import ClientError
from db_handshake import get_dynamodb_reasources

TABLE_CONFIGS = [
    {
        'name': 'Players',
        'description': 'Stores player profile information',
        'key_schema': [
            {'AttributeName': 'puuid', 'KeyType': 'HASH'}  # Partition key only
        ],
        'attribute_definitions': [
            {'AttributeName': 'puuid', 'AttributeType': 'S'}  # S = String
        ]
    },
    {
        'name': 'Matchs',
        'description': 'Stores individual match data per player',
        'key_schema': [
            {'AttributeName': 'puuid', 'KeyType': 'HASH'},      # Partition key: which player
            {'AttributeName': 'match_id', 'KeyType': 'RANGE'}   # Sort key: unique match ID
        ],
        'attribute_definitions': [
            {'AttributeName': 'puuid', 'AttributeType': 'S'},
            {'AttributeName': 'match_id', 'AttributeType': 'S'}  # Riot match IDs like "NA1_4567890123"
        ]
    },
    {
        'name': 'ai_feedback',
        'description': 'Stores AI-generated insights and feedback for players',
        'key_schema': [
            {'AttributeName': 'puuid', 'KeyType': 'HASH'},         # Partition key: which player
            {'AttributeName': 'feedback_id', 'KeyType': 'RANGE'}   # Sort key: unique feedback ID (timestamp-based)
        ],
        'attribute_definitions': [
            {'AttributeName': 'puuid', 'AttributeType': 'S'},
            {'AttributeName': 'feedback_id', 'AttributeType': 'S'}  # Format: "YYYY-MM-DD_HHMMSS" or UUID
        ]
    }
]


def create_table(table_config):
    dynamodb = get_dynamodb_reasources()
    table_name = table_config['name']

    # Check if table already exists
    try:
        existing_table = dynamodb.Table(table_name)
        existing_table.load()
        print(f"✓ Table '{table_name}' already exists. Skipping creation.")
        return existing_table

    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise

    print(f"Creating table '{table_name}' ({table_config.get('description', 'No description')})...")

    # Create the table
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=table_config['key_schema'],
            AttributeDefinitions=table_config['attribute_definitions'],
            BillingMode='PAY_PER_REQUEST'
        )

        print(f"Waiting for table '{table_name}' to be ready...")
        table.wait_until_exists()
        print(f"✓ Table '{table_name}' created successfully!")
        return table

    except ClientError as e:
        print(f"Error creating table '{table_name}': {e.response['Error']['Message']}")
        raise


def init_all_tables():
    print("Starting database initialization...\n")
    for config in TABLE_CONFIGS:
        create_table(config)

if __name__ == "__main__":
    init_all_tables()
