import sys
import logging
import pymysql
import json
import uuid
import datetime
import os

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

def get_user_mapping(data):
    """
    {
        "user_id": "user1"
    }
    """
    # Extract user_id from the request
    user_id = data.get('user_id')

    fridge_id = None

    with conn.cursor() as cur:
        # Check if user_id exists in user_map table
        cur.execute("SELECT fridge_id FROM user_map WHERE user_id = %s", (user_id,))
        fridge_id_row = cur.fetchone()

        if fridge_id_row is None:
            return {"success": False, "message": "User does not have a fridge associated"}, 200

        fridge_id = fridge_id_row[0]
        
        conn.commit()

    return {"success": True, "user_id": user_id, "fridge_id": fridge_id}, 200

def add_user_mapping(data):
    """
    {   
        "user_id": "user_1",
        "fridge_id": "fridge_1"
    }
    """
    # Extract user_id and fridge_id from the request
    user_id = data.get('user_id')
    fridge_id = data.get('fridge_id')

    with conn.cursor() as cur:
        # Check if the mapping already exists
        cur.execute("SELECT * FROM user_map WHERE user_id = %s", (user_id,))
        existing_mapping = cur.fetchone()

        if existing_mapping:
            return {"success": False, "message": "Mapping for user already exists"}, 200

        # Add the user mapping to user_map table
        cur.execute("INSERT INTO user_map (user_id, fridge_id) VALUES (%s, %s)", (user_id, fridge_id))
        
        conn.commit()

    return {"success": True, "user_id": user_id, "fridge_id": fridge_id}, 200

def get_data(data):
    """
    {
        "user_id": "user1"
    }
    """
    # Extract user_id from the request
    user_id = data.get('user_id')
    fridge_id = None
    labeled_items, unlabeled_items = [], []
    
    with conn.cursor() as cur:
        # Check if user_id exists in user_map table
        cur.execute("SELECT fridge_id FROM user_map WHERE user_id = %s", (user_id,))
        fridge_id_row = cur.fetchone()

        if fridge_id_row is None:
            return {"success": False, "message": "User does not have a fridge associated"}, 200
            
        fridge_id = fridge_id_row[0]

        # Fetch labeled items
        cur.execute("SELECT uuid, expiration_date, name FROM item_info WHERE fridge_id = %s AND name IS NOT NULL", (fridge_id,))
        labeled_items = [{"uuid": row[0], "expiration_date": row[1].strftime("%m/%d/%Y"), "name": row[2]} for row in cur.fetchall()]

        # Fetch unlabeled items with barcode
        cur.execute("SELECT uuid, expiration_date, barcode, image_url FROM item_info WHERE fridge_id = %s AND name IS NULL", (fridge_id,))
        unlabeled_items = [{"uuid": row[0], "expiration_date": row[1].strftime("%m/%d/%Y"), "barcode": row[2], "image_url": row[3]} for row in cur.fetchall()]
        
        conn.commit()

    return {"success": True, "labeled_items": labeled_items, "unlabeled_items": unlabeled_items}, 200

def update_unlabeled_data(data):
    """
    {
        "user_id": "user1",
        "item": {
            "uuid": "1234",
            "name": "Milk",
            "expiration_date": "12/31/2020"
        }
    }
    """
    # Extract user_id and item data from the request
    user_id = data.get('user_id')
    item = data.get('item')

    # Extract item details
    uuid = item.get('uuid')
    name = item.get('name')
    expiration_date_str = item.get('expiration_date')
    
    with conn.cursor() as cur:
        # Check if user_id exists in user_map table
        cur.execute("SELECT fridge_id FROM user_map WHERE user_id = %s", (user_id,))
        fridge_id_row = cur.fetchone()

        if fridge_id_row is None:
            return {"success": False, "message": "User does not have a fridge associated"}, 200
    
        fridge_id = fridge_id_row[0]
    
        # Check if the item exists and is unlabeled
        cur.execute("SELECT name FROM item_info WHERE uuid = %s AND name IS NULL", (uuid,))
        existing_item = cur.fetchone()
    
        if existing_item is None:
            return {"success": False, "message": "Item with specified UUID does not exist or is labeled"}, 200
    
        # Convert expiration_date string to a datetime object
        expiration_date = datetime.datetime.strptime(expiration_date_str, "%m/%d/%Y").date()
    
        # Update the item in item_info table
        cur.execute("UPDATE item_info SET name = %s, expiration_date = %s WHERE uuid = %s",
                          (name, expiration_date, uuid))
    
        # Get barcode
        cur.execute("SELECT barcode FROM item_info WHERE uuid = %s", (uuid,))
        barcode_row = cur.fetchone()
        
        if barcode_row is None:
            return {"success": False, "message": "Failed to retrieve barcode for the updated item"}, 200
            
        barcode = barcode_row[0]
    
        # Check if the barcode already exists in the saved_map table for the specified fridge_id
        cur.execute("SELECT COUNT(*) FROM saved_map WHERE fridge_id = %s AND barcode = %s", (fridge_id, barcode))
        existing_mapping_count = cur.fetchone()[0]
    
        if existing_mapping_count == 0:
            # Add an entry in the saved_map table associating the barcode with the name
            cur.execute("INSERT INTO saved_map (fridge_id, barcode, name) VALUES (%s, %s, %s)", (fridge_id, barcode, name))
            
            # Update all items with that barcode to that name for that fridge id in item_info table
            cur.execute("""
                UPDATE item_info
                SET name = %s
                WHERE fridge_id = %s AND barcode = %s
            """, (name, fridge_id, barcode))
        else:
            return {"success": False, "message": f"Barcode {barcode} already exists in the saved_map table"}, 200
        
        conn.commit()

    return {"success": True, "item": {"uuid": uuid, "name": name, "expiration_date": expiration_date_str}}, 200

def update_labeled_data(data):
    """
    Note: not all labeled items that can be updated need to have a barcode. For example, an items added from the phone may not have a barcode.
    {
        "user_id": "user1",
        "item": {       
            "uuid": "1234",
            "name": "Cheese",
            "expiration_date": "12/31/2020"
        }
    }
    """
    # Extract user_id and item data from the request
    user_id = data.get('user_id')
    item = data.get('item')

    # Extract item details
    uuid = item.get('uuid')
    name = item.get('name')
    expiration_date_str = item.get('expiration_date')
    
    with conn.cursor() as cur:
        # Check if user_id exists in user_map table
        cur.execute("SELECT fridge_id FROM user_map WHERE user_id = %s", (user_id,))
        fridge_id_row = cur.fetchone()
    
        if fridge_id_row is None:
            return {"success": False, "message": "User does not have a fridge associated"}, 200
        
        fridge_id = fridge_id_row[0]
    
        # Check if the item exists and is labeled
        cur.execute("SELECT name, barcode FROM item_info WHERE uuid = %s AND name IS NOT NULL", (uuid,))
        existing_name, existing_barcode = cur.fetchone()
    
        if existing_name is None:
            return {"success": False, "message": "Item with specified UUID does not exist or is unlabeled"}, 200
    
        # Convert expiration_date string to a datetime object
        expiration_date = datetime.datetime.strptime(expiration_date_str, "%m/%d/%Y").date()
    
        # Update the expiration_date for the labeled item in item_info table
        cur.execute("UPDATE item_info SET name = %s, expiration_date = %s WHERE uuid = %s",
                          (name, expiration_date, uuid))
                          
        # Update barcode's value in saved_map
        cur.execute("SELECT barcode FROM item_info WHERE uuid = %s", (uuid,))
        barcode_row = cur.fetchone()
        
        if barcode_row is not None:
            barcode = barcode_row[0]
            # Update all items with that barcode to that name for that fridge id in item_info table
            cur.execute("""
                UPDATE item_info
                SET name = %s
                WHERE fridge_id = %s AND barcode = %s
            """, (name, fridge_id, barcode))
                          
        conn.commit()

    return {"success": True, "item": {"uuid": uuid, "expiration_date": expiration_date_str}}, 200

def add_data(data):
    """
    { 
        "user_id": "user1",
        "item": {
            "name": "Milk",
            "expiration_date": "12/31/2020"
        }
    }
    """
    # Extract user_id and item data from the request
    user_id = data.get('user_id')
    item = data.get('item')

    with conn.cursor() as cur:
        # Check if user_id exists in user_map table
        cur.execute("SELECT fridge_id FROM user_map WHERE user_id = %s", (user_id,))
        fridge_id_row = cur.fetchone()
    
        if fridge_id_row is None:
            return {"success": False, "message": "User does not have a fridge associated"}, 200
    
        fridge_id = fridge_id_row[0]
    
        # Generate UUID for the item
        item_uuid = str(uuid.uuid4())
    
        # Extract item details
        name = item.get('name')
        expiration_date_str = item.get('expiration_date')
    
        # Convert expiration_date string to a datetime object
        expiration_date = datetime.datetime.strptime(expiration_date_str, "%m/%d/%Y").date()
    
        # Insert item into item_info table
        cur.execute("INSERT INTO item_info (uuid, fridge_id, name, expiration_date) VALUES (%s, %s, %s, %s)",
                          (item_uuid, fridge_id, name, expiration_date))
                          
        conn.commit()

    return {"success": True, "item": {"uuid": item_uuid, "name": name, "expiration_date": expiration_date_str}}, 200

def delete_data(data):
    """
    {
        "user_id": "user1",
        "item": {
            "uuid": "1234"
        }
    }
    """

    # Extract user_id and item data from the request
    user_id = data.get('user_id')
    item = data.get('item')

    # Extract item details
    uuid = item.get('uuid')

    with conn.cursor() as cur:
        # Check if user_id exists in user_map table
        cur.execute("SELECT fridge_id FROM user_map WHERE user_id = %s", (user_id,))
        fridge_id_row = cur.fetchone()
    
        if fridge_id_row is None:
            return {"success": False, "message": "User does not have a fridge associated"}, 200
    
        # Delete the item from item_info table
        cur.execute("DELETE FROM item_info WHERE uuid = %s", (uuid,))
    
        if cur.rowcount == 0:
            return {"success": False, "message": "Item with specified UUID does not exist"}, 200
        
        conn.commit()

    return {"success": True, "item": {"uuid": uuid}}, 200

def get_env_data(data):
    """
    {
        "user_id": "user1"
    }
    """
    # Extract user_id and item data from the request
    user_id = data.get('user_id')

    with conn.cursor() as cur:
        # Check if user_id exists in user_map table
        cur.execute("SELECT fridge_id FROM user_map WHERE user_id = %s", (user_id,))
        fridge_id_row = cur.fetchone()
    
        if fridge_id_row is None:
            return {"success": False, "message": "User does not have a fridge associated"}, 200
        
        fridge_id = fridge_id_row[0]
        
        # get env data from env_info table
        cur.execute("SELECT temperature, humidity FROM env_info WHERE fridge_id = %s", (fridge_id,))
        env_data_row = cur.fetchone()
        
        if env_data_row is None:
            return {"success": False, "env_data": {"temperature": None, "humidity": None}}, 200
        
        existing_temperature, existing_humidity = env_data_row
        
        conn.commit()
    
    return {"success": True, "env_data": {"temperature": existing_temperature, "humidity": existing_humidity}}, 200

    

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
    
    path = event["path"].split('/')[-1]
    body = json.loads(event["body"])
    
    return_body = None
    return_status = None
    if path == "get_user_mapping":
        return_body, return_status = get_user_mapping(body)
    elif path == "add_user_mapping":
        return_body, return_status = add_user_mapping(body)
    elif path == "get_data":
        return_body, return_status = get_data(body)
    elif path == "update_unlabeled_data":
        return_body, return_status = update_unlabeled_data(body)
    elif path == "update_labeled_data":
        return_body, return_status = update_labeled_data(body)
    elif path == "add_data":
        return_body, return_status = add_data(body)
    elif path == "delete_data":
        return_body, return_status = delete_data(body)
    elif path == "get_env_data":
        return_body, return_status = get_env_data(body)
    else:
        return_body, return_status = {"message": "Invalid path"}, 500 
    
    return generate_response(return_body, return_status)
    