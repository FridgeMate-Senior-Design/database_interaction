# hardware.py

db_conn = None
db_cursor = None

def set_database_connection(conn, cursor):
    global db_conn
    global db_cursor
    db_conn = conn
    db_cursor = cursor

def add_data(data):
    # Access database using db_conn and db_cursor
    # Add logic to add data
    return {"message": "Data added to hardware successfully", "data": data}

def delete_data(data):
    # Access database using db_conn and db_cursor
    # Add logic to delete data
    return {"message": "Data deleted from hardware successfully", "data": data}
