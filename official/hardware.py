import sys
import logging
import pymysql
import json
import os
import uuid
import datetime

# rds settings
user_name = os.environ['USER_NAME']
password = os.environ['PASSWORD']
rds_proxy_host = os.environ['RDS_PROXY_HOST']
db_name = os.environ['DB_NAME']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.
try:
    conn = pymysql.connect(host=rds_proxy_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit(1)

logger.info("SUCCESS: Connection to RDS for MySQL instance succeeded")

def add_data(data):
    """
    {
        "fridge_id": "fridge1",
        "items": [
            {
                "barcode": "1234567890",
                "image_url": "https://example.com/image1.jpg",
                "expiration_date": "01/01/2022"
            },
            {
                "barcode": "0987654321",
                "image_url": "https://example.com/image2.jpg",
                "expiration_date": "01/01/2022"
            }
        ]
    }
    """
    
    base_image_url = "https://fridgemate-images.s3.us-east-2.amazonaws.com/{}.jpg"
    
    fridge_id = data.get('fridge_id')
    items = data.get('items', [])

    with conn.cursor() as cur:
        # Fetch barcode-name pairs from the saved_map table and store them in a dictionary
        barcode_name_map = {}
        cur.execute("SELECT barcode, name FROM saved_map WHERE fridge_id = %s", (fridge_id,))
        rows = cur.fetchall()
        for row in rows:
            barcode_name_map[row[0]] = row[1]
    
        for item in items:
            barcode = item.get('barcode')
            image_name = item.get('image_url')
            image_url = base_image_url.format(image_name)
            expiration_date_str = item.get('expiration_date')
    
            # Generate UUID for the item
            item_uuid = str(uuid.uuid4())
    
            # Convert expiration_date string to a datetime object
            expiration_date = datetime.datetime.strptime(expiration_date_str, "%m/%d/%Y").date()
    
            # Check if the barcode has a name in the barcode_name_map dictionary
            name = barcode_name_map.get(barcode)
    
            # Add the item to the item_info table
            cur.execute("INSERT INTO item_info (uuid, fridge_id, expiration_date, barcode, image_url, name) VALUES (%s, %s, %s, %s, %s, %s)",
                              (item_uuid, fridge_id, expiration_date, barcode, image_url, name))
            
            conn.commit()

    return {"success": True, "message": "Items added successfully"}, 200


def delete_data(data):
    """
    {
        "fridge_id": "fridge1",
        "barcode": "1234567890"
    }
    """
    fridge_id = data.get('fridge_id')
    barcode = data.get('barcode')

    with conn.cursor() as cur:
        # Check if there's an item with the specified fridge_id and barcode
        cur.execute("SELECT uuid, MIN(expiration_date) FROM item_info WHERE fridge_id = %s AND barcode = %s", (fridge_id, barcode))
        row = cur.fetchone()
    
    
        if row == (None, None):
            return {"success": False, "message": "No item found with the specified fridge_id and barcode"}, 200
    
        item_uuid, latest_expiration_date = row
    
        # Delete the row with the latest expiration date
        cur.execute("DELETE FROM item_info WHERE uuid = %s", (item_uuid,))
        
        conn.commit()

    return {"success": True, "message": f"Item with barcode {barcode} deleted successfully"}, 200

def add_env_data(data):
    """
    {
        "fridge_id": "fridge1",
        "temperature": 33,
        "humidity": 15
    }
    """
    
    fridge_id = data.get('fridge_id')
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO env_info (fridge_id, temperature, humidity)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE temperature = VALUES(temperature), humidity = VALUES(humidity)
            """, 
        (fridge_id, temperature, humidity))
   
        conn.commit()
    
    return {"success": True, "message": f"Fridge: {fridge_id} updated with temperature: {temperature} and humidity: {humidity}"}, 200

def generate_response(body, status):
    response = {
        'statusCode': status,
        'body': json.dumps(body),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
    }
    return response

def lambda_handler(event, context):
    """
    This function creates a new RDS database table and writes records to it
    """

    # with conn.cursor() as cur:
    #     cur.execute("create table if not exists Inventory ( UUID varchar(255) NOT NULL, Barcode varchar(255) NOT NULL, Name varchar(255), FridgeID varchar(255) NOT NULL, Image varchar(255) NOT NULL, ExpiryDate DATE NOT NULL, PRIMARY KEY (UUID) )")
    #     cur.execute("create table if not exists SavedNames ( Barcode varchar(255) NOT NULL, Name varchar(255) NOT NULL, FridgeID varchar(255) NOT NULL, PRIMARY KEY (Barcode) )")
    #     cur.execute("create table if not exists UsersMap ( UserID varchar(255) NOT NULL, FridgeID varchar(255) NOT NULL, PRIMARY KEY (UserID) )")
    #     conn.commit()
    # conn.commit()
    
    path = event["path"].split('/')[-1]
    body = json.loads(event["body"])
    
    return_body = None
    return_status = None
    if path == "add_data":
        return_body, return_status = add_data(body)
    elif path == "delete_data":
        return_body, return_status = delete_data(body)
    elif path == "add_env_data":
        return_body, return_status = add_env_data(body)
    else:
        return_body, return_status = {"message": "Invalid path"}, 500 
    
    return generate_response(return_body, return_status)
    