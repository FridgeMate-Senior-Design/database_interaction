# hardware.py

import uuid
import datetime

def add_data(data, db_conn, db_cursor):
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
    fridge_id = data.get('fridge_id')
    items = data.get('items', [])

    # Fetch barcode-name pairs from the saved_map table and store them in a dictionary
    barcode_name_map = {}
    db_cursor.execute("SELECT barcode, name FROM saved_map WHERE fridge_id = ?", (fridge_id,))
    rows = db_cursor.fetchall()
    for row in rows:
        barcode_name_map[row[0]] = row[1]

    for item in items:
        barcode = item.get('barcode')
        image_url = item.get('image_url')
        expiration_date_str = item.get('expiration_date')

        # Generate UUID for the item
        item_uuid = str(uuid.uuid4())

        # Convert expiration_date string to a datetime object
        expiration_date = datetime.datetime.strptime(expiration_date_str, "%m/%d/%Y").date()

        # Check if the barcode has a name in the barcode_name_map dictionary
        name = barcode_name_map.get(barcode)

        # Add the item to the item_info table
        db_cursor.execute("INSERT INTO item_info (uuid, fridge_id, expiration_date, barcode, image_url, name) VALUES (?, ?, ?, ?, ?, ?)",
                          (item_uuid, fridge_id, expiration_date, barcode, image_url, name))
        db_conn.commit()

    return {"success": True, "message": "Items added successfully"}


def delete_data(data, db_conn, db_cursor):
    """
    {
        "fridge_id": "fridge1",
        "barcode": "1234567890"
    }
    """
    fridge_id = data.get('fridge_id')
    barcode = data.get('barcode')

    # Check if there's an item with the specified fridge_id and barcode
    db_cursor.execute("SELECT uuid, MIN(expiration_date) FROM item_info WHERE fridge_id = ? AND barcode = ?", (fridge_id, barcode))
    row = db_cursor.fetchone()

    if row is None:
        return {"success": False, "message": "No item found with the specified fridge_id and barcode"}

    item_uuid, latest_expiration_date = row

    # Delete the row with the latest expiration date
    db_cursor.execute("DELETE FROM item_info WHERE uuid = ?", (item_uuid,))
    db_conn.commit()

    return {"success": True, "message": f"Item with barcode {barcode} deleted successfully"}

