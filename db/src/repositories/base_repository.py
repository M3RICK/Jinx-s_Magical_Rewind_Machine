from typing import Dict, Optional, Any
from botocore.exceptions import ClientError


class BaseRepository:
    """Base repository class with common DynamoDB operations"""

    def __init__(self, dynamodb_resource, table_name: str):
        """
        Initialize repository with DynamoDB resource and table name.

        Args:
            dynamodb_resource: boto3 DynamoDB resource
            table_name: Name of the DynamoDB table
        """
        self.dynamodb = dynamodb_resource
        self.table_name = table_name
        self.table = dynamodb_resource.Table(table_name)

    def get_item(self, key: Dict) -> Optional[Dict]:
        """
        Get a single item by key.

        Args:
            key: Dictionary containing partition key (and sort key if applicable)

        Returns:
            Item dictionary or None if not found
        """
        try:
            response = self.table.get_item(Key=key)
            return response.get('Item')
        except ClientError as e:
            print(f"Error getting item from {self.table_name}: {e}")
            raise

    def put_item(self, item: Dict) -> bool:
        """
        Put (create or overwrite) an item.

        Args:
            item: Item dictionary to store

        Returns:
            True if successful
        """
        try:
            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            print(f"Error putting item to {self.table_name}: {e}")
            raise

    def update_item(self, key: Dict, update_expression: str,
                   expression_attribute_values: Dict,
                   expression_attribute_names: Optional[Dict] = None) -> Dict:
        """
        Update an item with an update expression.

        Args:
            key: Dictionary containing partition key (and sort key if applicable)
            update_expression: DynamoDB update expression
            expression_attribute_values: Values for the update expression
            expression_attribute_names: Optional attribute name mappings

        Returns:
            Updated item attributes
        """
        try:
            params = {
                'Key': key,
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_attribute_values,
                'ReturnValues': 'ALL_NEW'
            }

            if expression_attribute_names:
                params['ExpressionAttributeNames'] = expression_attribute_names

            response = self.table.update_item(**params)
            return response.get('Attributes', {})
        except ClientError as e:
            print(f"Error updating item in {self.table_name}: {e}")
            raise

    def delete_item(self, key: Dict) -> bool:
        """
        Delete an item by key.

        Args:
            key: Dictionary containing partition key (and sort key if applicable)

        Returns:
            True if successful
        """
        try:
            self.table.delete_item(Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting item from {self.table_name}: {e}")
            raise

    def query(self, key_condition_expression, **kwargs) -> list:
        """
        Query items with a key condition.

        Args:
            key_condition_expression: boto3 Key condition expression
            **kwargs: Additional query parameters (FilterExpression, Limit, etc.)

        Returns:
            List of items matching the query
        """
        try:
            params = {
                'KeyConditionExpression': key_condition_expression,
                **kwargs
            }

            response = self.table.query(**params)
            items = response.get('Items', [])

            # Handle pagination if needed
            while 'LastEvaluatedKey' in response:
                params['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.table.query(**params)
                items.extend(response.get('Items', []))

            return items
        except ClientError as e:
            print(f"Error querying {self.table_name}: {e}")
            raise

    def scan(self, **kwargs) -> list:
        """
        Scan table (use sparingly - prefer query when possible).

        Args:
            **kwargs: Scan parameters (FilterExpression, Limit, etc.)

        Returns:
            List of all items matching the scan
        """
        try:
            response = self.table.scan(**kwargs)
            items = response.get('Items', [])

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.table.scan(**kwargs)
                items.extend(response.get('Items', []))

            return items
        except ClientError as e:
            print(f"Error scanning {self.table_name}: {e}")
            raise
