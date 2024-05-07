import sys
import logging
import pymysql
import json
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

def create_tables():
    with conn.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS item_info (
                    uuid VARCHAR(255) PRIMARY KEY,
                    fridge_id TEXT NOT NULL,
                    expiration_date DATE NOT NULL,
                    barcode TEXT,
                    image_url TEXT,
                    name TEXT
                )''')

        cur.execute('''CREATE TABLE IF NOT EXISTS user_map (
                            user_id VARCHAR(255) PRIMARY KEY,
                            fridge_id TEXT NOT NULL
                        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS saved_map (
                            barcode VARCHAR(255) PRIMARY KEY,
                            name TEXT NOT NULL,
                            fridge_id TEXT NOT NULL
                        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS env_info (
                    fridge_id VARCHAR(255) PRIMARY KEY,
                    temperature FLOAT NOT NULL,
                    humidity FLOAT NOT NULL
                )''')
                
        cur.execute('''CREATE TABLE IF NOT EXISTS door_info (
                    fridge_id VARCHAR(255) PRIMARY KEY,
                    value INT NOT NULL
                )''')
                
                
        conn.commit()
        
    conn.commit()
    
    return {"message": "Tables created successfully"}, 200

def clear_tables():
    with conn.cursor() as cur:
        cur.execute("DELETE FROM item_info")
        cur.execute("DELETE FROM user_map")
        cur.execute("DELETE FROM saved_map")
        cur.execute("DELETE FROM env_info")
        cur.execute("DELETE FROM door_info")
        
        conn.commit()

    conn.commit()
    
    return {"message": "Tables cleared successfully"}, 200

def get_all_items():
    
    items = None
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM item_info")
        rows = cur.fetchall()
        
        items = [
            {
                "uuid": row[0], 
                "fridge_id": row[1], 
                "expiration_date": row[2].strftime('%Y-%m-%d') if row[2] else None, 
                "barcode": row[3], 
                "image_url": row[4], 
                "name": row[5]
            } for row in rows
        ]
        
        conn.commit()
    return {"all_items": items}, 200

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
    # body = json.loads(event["body"])
    
    return_body = None
    return_status = None
    if path == "create_tables":
        return_body, return_status = create_tables()
    elif path == "clear_tables":
        return_body, return_status = clear_tables()
    elif path == "get_all_items":
        return_body, return_status = get_all_items()
    else:
        return_body, return_status = {"message": "Invalid path"}, 500 
    
    return generate_response(return_body, return_status)
    