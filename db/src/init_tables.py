import boto3
from botocore.exceptions import ClientError
from db_handshake import get_dynamodb_reasources

TABLE_CONFIGS = [
    {
        'name': 'Players',
        'description': 'Stores player profile information (PUUID, riot_id, region, main_role, main_champions, winrate, current_rank)',
        'key_schema': [
            {'AttributeName': 'puuid', 'KeyType': 'HASH'}  # Partition key
        ],
        'attribute_definitions': [
            {'AttributeName': 'puuid', 'AttributeType': 'S'}  # S = String
        ],
        'global_secondary_indexes': [
            {
                'IndexName': 'RiotIdIndex',
                'KeySchema': [
                    {'AttributeName': 'riot_id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'riot_id', 'AttributeType': 'S'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    {
        'name': 'MatchHistory',
        'description': 'Stores individual match data per player (last 20 matches for hackathon, expandable to 100+)',
        'key_schema': [
            {'AttributeName': 'puuid', 'KeyType': 'HASH'},      # Partition key: which player
            {'AttributeName': 'match_id', 'KeyType': 'RANGE'}   # Sort key: unique match ID
        ],
        'attribute_definitions': [
            {'AttributeName': 'puuid', 'AttributeType': 'S'},
            {'AttributeName': 'match_id', 'AttributeType': 'S'},  # Riot match IDs like "NA1_4567890123"
            {'AttributeName': 'timestamp', 'AttributeType': 'N'}  # Unix timestamp for sorting
        ],
        'local_secondary_indexes': [
            {
                'IndexName': 'TimestampIndex',
                'KeySchema': [
                    {'AttributeName': 'puuid', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    },
    {
        'name': 'Conversations',
        'description': 'Stores AI chat conversation history per player',
        'key_schema': [
            {'AttributeName': 'puuid', 'KeyType': 'HASH'},              # Partition key: which player
            {'AttributeName': 'conversation_id', 'KeyType': 'RANGE'}    # Sort key: timestamp-based ID
        ],
        'attribute_definitions': [
            {'AttributeName': 'puuid', 'AttributeType': 'S'},
            {'AttributeName': 'conversation_id', 'AttributeType': 'S'}  # Format: ISO timestamp or UUID
        ]
    },
    {
        'name': 'Sessions',
        'description': 'Maps session tokens to player PUUIDs for authentication',
        'key_schema': [
            {'AttributeName': 'session_token', 'KeyType': 'HASH'}  # Partition key: UUID session token
        ],
        'attribute_definitions': [
            {'AttributeName': 'session_token', 'AttributeType': 'S'}  # UUID format
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

    # Build create_table parameters
    create_params = {
        'TableName': table_name,
        'KeySchema': table_config['key_schema'],
        'AttributeDefinitions': table_config['attribute_definitions'],
        'BillingMode': 'PAY_PER_REQUEST'
    }

    # Add Global Secondary Indexes if defined
    if 'global_secondary_indexes' in table_config:
        gsi_list = []
        for gsi in table_config['global_secondary_indexes']:
            # Add GSI attributes to main attribute definitions if not already present
            for attr_def in gsi.get('AttributeDefinitions', []):
                if attr_def not in create_params['AttributeDefinitions']:
                    create_params['AttributeDefinitions'].append(attr_def)

            gsi_list.append({
                'IndexName': gsi['IndexName'],
                'KeySchema': gsi['KeySchema'],
                'Projection': gsi['Projection']
            })
        create_params['GlobalSecondaryIndexes'] = gsi_list

    # Add Local Secondary Indexes if defined
    if 'local_secondary_indexes' in table_config:
        lsi_list = []
        for lsi in table_config['local_secondary_indexes']:
            # Add LSI attributes to main attribute definitions if not already present
            for attr_def in lsi.get('AttributeDefinitions', []):
                if attr_def not in create_params['AttributeDefinitions']:
                    create_params['AttributeDefinitions'].append(attr_def)

            lsi_list.append({
                'IndexName': lsi['IndexName'],
                'KeySchema': lsi['KeySchema'],
                'Projection': lsi['Projection']
            })
        create_params['LocalSecondaryIndexes'] = lsi_list

    # Create the table
    try:
        table = dynamodb.create_table(**create_params)

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
