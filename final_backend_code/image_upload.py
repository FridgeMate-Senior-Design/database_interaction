import json
import base64
import boto3
import uuid

def lambda_handler(event, context):
    # TODO implement
    s3 = boto3.client("s3")

    get_file_content = event["content"]
    
    print("file content")
    print(get_file_content)
    
    decode_content = base64.b64decode(get_file_content)
    print("decode content")
    print(decode_content)
    
    hex_string = decode_content.decode('utf-8')
    print("hex string")
    print(hex_string)

    binary = bytes.fromhex(hex_string)
    print("binary")
    print(binary)
    
    image_uuid = str(uuid.uuid4())
    # Specify the file extension/type if it's known, e.g., '.jpg' for JPEG images
    file_extension = ".jpg"  # Adjust this based on the actual image type if necessary
    
    # Upload the decoded content to S3, using the UUID (and optional file extension) as the file name
    s3_upload = s3.put_object(
        Bucket="fridgemate-images", 
        Key=f"{image_uuid}{file_extension}", 
        ContentType='image/jpg',           # Set the MIME type for a PDF file
        ContentDisposition='inline',             # Suggests to the browser to open rather than download
        Body=binary
    )

    return {
        'statusCode': 200,
        'body': {'message': 'The Object is Uploaded successfully!', 'file_name': image_uuid}
    }
    