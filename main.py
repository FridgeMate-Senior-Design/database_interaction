# main.py
import sqlite3
from flask import Flask, request, jsonify, g
from software import get_user_mapping, add_user_mapping, get_data, update_unlabeled_data, update_labeled_data, add_data as add_software_data, delete_data as delete_software_data
from hardware import add_data as add_hardware_data, delete_data as delete_hardware_data

app = Flask(__name__)

DATABASE = 'my_database.db'

# Connect to the database
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS item_info (
                    uuid TEXT PRIMARY KEY,
                    fridge_id INTEGER NOT NULL,
                    expiration_date DATE NOT NULL,
                    barcode TEXT,
                    image_url TEXT,
                    name TEXT
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS user_map (
                    user_id TEXT PRIMARY KEY,
                    fridge_id INTEGER NOT NULL
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS saved_map (
                    barcode TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    fridge_id INTEGER NOT NULL
                )''')

conn.commit()

conn.close()

# Function to get database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Function to close database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/software/get_user_mapping', methods=['POST'])
def software_get_user_mapping():
    data = request.json

    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    result = get_user_mapping(data, db_conn, db_cursor)
    return jsonify(result)

@app.route('/software/add_user_mapping', methods=['POST'])
def software_add_user_mapping():
    data = request.json

    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    result = add_user_mapping(data, db_conn, db_cursor)
    return jsonify(result)

@app.route('/software/get_data', methods=['POST'])
def software_get_data():
    data = request.json

    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    result = get_data(data, db_conn, db_cursor)
    return jsonify(result)

@app.route('/software/update_unlabeled_data', methods=['POST'])
def software_update_unlabeled_data():
    data = request.json

    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    result = update_unlabeled_data(data, db_conn, db_cursor)
    return jsonify(result)

@app.route('/software/update_labeled_data', methods=['POST'])
def software_update_labeled_data():
    data = request.json

    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    result = update_labeled_data(data, db_conn, db_cursor)
    return jsonify(result)

@app.route('/software/add_data', methods=['POST'])
def software_add_data():
    data = request.json

    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    result = add_software_data(data, db_conn, db_cursor)
    return jsonify(result)

@app.route('/software/delete_data', methods=['POST'])
def software_delete_data():
    data = request.json

    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    result = delete_software_data(data, db_conn, db_cursor)
    return jsonify(result)


@app.route('/hardware/add_data', methods=['POST'])
def hardware_add_data():
    data = request.json

    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    result = add_hardware_data(data, db_conn, db_cursor)
    return jsonify(result)

@app.route('/hardware/delete_data', methods=['POST'])
def hardware_delete_data():
    data = request.json

    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    result = delete_hardware_data(data, db_conn, db_cursor)
    return jsonify(result)

@app.route('/clear_tables', methods=['POST'])
def clear_tables():
    # Get database cursor
    db_conn = get_db()
    db_cursor = db_conn.cursor()
    db_cursor.execute("DELETE FROM item_info")
    db_cursor.execute("DELETE FROM user_map")
    db_cursor.execute("DELETE FROM saved_map")
    db_conn.commit()
    return jsonify({"message": "Tables cleared successfully"})

if __name__ == '__main__':
    app.run(debug=True)
