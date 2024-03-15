# main.py
import sqlite3
from flask import Flask, request, jsonify
from software import get_user_mapping, get_data, update_unlabeled_data, update_labeled_data, add_data as add_software_data, delete_data as delete_software_data
from hardware import add_data as add_hardware_data, delete_data as delete_hardware_data

app = Flask(__name__)

# Create SQLite database and establish connection
conn = sqlite3.connect('my_database.db')
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

# Pass connection and cursor objects to software and hardware modules
from software import set_database_connection
from hardware import set_database_connection

set_database_connection(conn, cursor)

@app.route('/software/get_user_mapping', methods=['POST'])
def software_get_user_mapping():
    data = request.json
    result = get_user_mapping(data)
    return jsonify(result)

@app.route('/software/get_data', methods=['POST'])
def software_get_data():
    data = request.json
    result = get_data(data)
    return jsonify(result)

@app.route('/software/update_unlabeled_data', methods=['POST'])
def software_update_unlabeled_data():
    data = request.json
    result = update_unlabeled_data(data)
    return jsonify(result)

@app.route('/software/update_labeled_data', methods=['POST'])
def software_update_labeled_data():
    data = request.json
    result = update_labeled_data(data)
    return jsonify(result)

@app.route('/software/add_data', methods=['POST'])
def software_add_data():
    data = request.json
    result = add_software_data(data)
    return jsonify(result)

@app.route('/software/delete_data', methods=['POST'])
def software_delete_data():
    data = request.json
    result = delete_software_data(data)
    return jsonify(result)


@app.route('/hardware/add_data', methods=['POST'])
def hardware_add_data():
    data = request.json
    result = add_hardware_data(data)
    return jsonify(result)

@app.route('/hardware/delete_data', methods=['POST'])
def hardware_delete_data():
    data = request.json
    result = delete_hardware_data(data)
    return jsonify(result)

@app.route('/clear_tables', methods=['POST'])
def clear_tables():
    cursor.execute("DELETE FROM item_info")
    cursor.execute("DELETE FROM user_map")
    cursor.execute("DELETE FROM saved_map")
    conn.commit()
    return jsonify({"message": "Tables cleared successfully"})

if __name__ == '__main__':
    app.run(debug=True)
