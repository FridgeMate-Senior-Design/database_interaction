# software.py
import uuid
import datetime

db_conn = None
db_cursor = None

def set_database_connection(conn, cursor):
    global db_conn
    global db_cursor
    db_conn = conn
    db_cursor = cursor

def get_user_mapping(data):
    """
    {
        "user_id": "user1"
    }
    """
    # Extract user_id from the request
    user_id = data.get('user_id')

    # Check if user_id exists in user_map table
    db_cursor.execute("SELECT fridge_id FROM user_map WHERE user_id = ?", (user_id,))
    fridge_id_row = db_cursor.fetchone()

    if fridge_id_row is None:
        return {"success": False, "message": "User does not have a fridge associated"}

    fridge_id = fridge_id_row[0]

    return {"success": True, "user_id": user_id, "fridge_id": fridge_id}

def get_data(data):
    """
    {
        "user_id": "user1"
    }
    """
    # Extract user_id from the request
    user_id = data.get('user_id')

    # Check if user_id exists in user_map table
    db_cursor.execute("SELECT fridge_id FROM user_map WHERE user_id = ?", (user_id,))
    fridge_id_row = db_cursor.fetchone()

    if fridge_id_row is None:
        return {"success": False, "message": "User does not have a fridge associated"}

    fridge_id = fridge_id_row[0]

    # Fetch labeled items
    db_cursor.execute("SELECT uuid, expiration_date, name FROM item_info WHERE fridge_id = ? AND name IS NOT NULL", (fridge_id,))
    labeled_items = [{"uuid": row[0], "expiration_date": row[1].strftime("%m/%d/%Y"), "name": row[2]} for row in db_cursor.fetchall()]

    # Fetch unlabeled items
    db_cursor.execute("SELECT uuid, expiration_date, image_url FROM item_info WHERE fridge_id = ? AND name IS NULL", (fridge_id,))
    unlabeled_items = [{"uuid": row[0], "expiration_date": row[1].strftime("%m/%d/%Y"), "image_url": row[2]} for row in db_cursor.fetchall()]

    return {"success": True, "labeled_items": labeled_items, "unlabeled_items": unlabeled_items}

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

    # Check if user_id exists in user_map table
    db_cursor.execute("SELECT fridge_id FROM user_map WHERE user_id = ?", (user_id,))
    fridge_id_row = db_cursor.fetchone()

    if fridge_id_row is None:
        return {"success": False, "message": "User does not have a fridge associated"}

    # Check if the item exists and is unlabeled
    db_cursor.execute("SELECT name FROM item_info WHERE uuid = ? AND name IS NULL", (uuid,))
    existing_item = db_cursor.fetchone()

    if existing_item is None:
        return {"success": False, "message": "Item with specified UUID does not exist or is labeled"}

    # Convert expiration_date string to a datetime object
    expiration_date = datetime.datetime.strptime(expiration_date_str, "%m/%d/%Y").date()

    # Update the item in item_info table
    db_cursor.execute("UPDATE item_info SET name = ?, expiration_date = ? WHERE uuid = ?",
                      (name, expiration_date, uuid))
    db_conn.commit()

    return {"success": True, "item": {"uuid": uuid, "name": name, "expiration_date": expiration_date_str}}

def update_labeled_data(data):
    """
    {
        "user_id": "user1",
        "item": {       
            "uuid": "1234",
            "expiration_date": "12/31/2020"
        }
    }
    """
    # Extract user_id and item data from the request
    user_id = data.get('user_id')
    item = data.get('item')

    # Extract item details
    uuid = item.get('uuid')
    expiration_date_str = item.get('expiration_date')

    # Check if user_id exists in user_map table
    db_cursor.execute("SELECT fridge_id FROM user_map WHERE user_id = ?", (user_id,))
    fridge_id_row = db_cursor.fetchone()

    if fridge_id_row is None:
        return {"success": False, "message": "User does not have a fridge associated"}

    # Check if the item exists and is labeled
    db_cursor.execute("SELECT name FROM item_info WHERE uuid = ? AND name IS NOT NULL", (uuid,))
    existing_item = db_cursor.fetchone()

    if existing_item is None:
        return {"success": False, "message": "Item with specified UUID does not exist or is unlabeled"}

    # Convert expiration_date string to a datetime object
    expiration_date = datetime.datetime.strptime(expiration_date_str, "%m/%d/%Y").date()

    # Update the expiration_date for the labeled item in item_info table
    db_cursor.execute("UPDATE item_info SET expiration_date = ? WHERE uuid = ?",
                      (expiration_date, uuid))
    db_conn.commit()

    return {"success": True, "item": {"uuid": uuid, "expiration_date": expiration_date_str}}

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

    # Check if user_id exists in user_map table
    db_cursor.execute("SELECT fridge_id FROM user_map WHERE user_id = ?", (user_id,))
    fridge_id_row = db_cursor.fetchone()

    if fridge_id_row is None:
        return {"success": False, "message": "User does not have a fridge associated"}

    fridge_id = fridge_id_row[0]

    # Generate UUID for the item
    item_uuid = str(uuid.uuid4())

    # Extract item details
    name = item.get('name')
    expiration_date_str = item.get('expiration_date')

    # Convert expiration_date string to a datetime object
    expiration_date = datetime.datetime.strptime(expiration_date_str, "%m/%d/%Y").date()

    # Insert item into item_info table
    db_cursor.execute("INSERT INTO item_info (uuid, fridge_id, name, expiration_date) VALUES (?, ?, ?, ?)",
                      (item_uuid, fridge_id, name, expiration_date))
    db_conn.commit()

    return {"success": True, "item": {"uuid": item_uuid, "name": name, "expiration_date": expiration_date_str}}

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

    # Check if user_id exists in user_map table
    db_cursor.execute("SELECT fridge_id FROM user_map WHERE user_id = ?", (user_id,))
    fridge_id_row = db_cursor.fetchone()

    if fridge_id_row is None:
        return {"success": False, "message": "User does not have a fridge associated"}

    # Delete the item from item_info table
    db_cursor.execute("DELETE FROM item_info WHERE uuid = ?", (uuid,))
    db_conn.commit()

    if db_cursor.rowcount == 0:
        return {"success": False, "message": "Item with specified UUID does not exist"}

    return {"success": True, "item": {"uuid": uuid}}