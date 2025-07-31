import boto3
from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    AWS_S3_BUCKET_NAME
)

# Create Textract client
textract_client = boto3.client(
    'textract',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def extract_text_textract(s3_object_name):
    """
    Calls AWS Textract to detect text in a file stored in S3.
    """
    response = textract_client.detect_document_text(
        Document={
            'S3Object': {
                'Bucket': AWS_S3_BUCKET_NAME,
                'Name': s3_object_name
            }
        }
    )

    lines = []
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            lines.append(block['Text'])

    full_text = "\n".join(lines)
    return full_text
