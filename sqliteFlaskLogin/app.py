# Imports
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import bcrypt
from flask_cors import CORS
import sqlite3
import random
import string
import requests
from datetime import datetime
import os


# Setup
app = Flask(__name__)
CORS(app)

# Function to hash a password
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

# Define a function to save uploaded files
def save_uploaded_file(file):
    if file:
        # Ensure the uploads directory exists
        uploads_dir = 'sqliteFlaskLogin/uploads'
        os.makedirs(uploads_dir, exist_ok=True)
        # Save the uploaded file to the uploads directory
        file_path = os.path.join(uploads_dir, file.filename)
        file.save(file_path)
        return file_path
    return None

# Routes------------------------------------------------

# Route for handling login page logic
# http://localhost:8080/
@app.route('/', methods=['GET', 'POST'])
def root():
    if request.method == 'POST':
        # Press Login
        if request.form.get('action') == 'login':
            connection = sqlite3.connect('user_LoginData.db')
            cursor = connection.cursor()

            username = request.form['username']
            password = request.form['password']
            print(f'\nUsername: {username}, Password: {password}')

            cursor.execute("SELECT password FROM users WHERE username=?", (username,))
            result = cursor.fetchone()

            # Checking if simple password checks it h
            if result:
                hashed_password = result[0]
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                    return redirect(url_for('insert', username=username))
                else:
                    print("Incorrect password")
            else:
                print("User not found")
        
        # Press Register
        elif request.form.get('action') == 'register':
            connection = sqlite3.connect('user_LoginData.db')
            cursor = connection.cursor()
            username = request.form.get('username')
            password = request.form.get('password')

            # Check if the username already exists in the database
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                # If the username already exists, display an error message
                msg = "Username already taken. Please choose a different username."
                return render_template('login.html', fail_msg=msg)
            else:
                # Generate a random 3-digit ID for the user
                user_id = ''.join(random.choices(string.digits, k=3))
                # Generate a random API key for the user
                api_key = ''.join(random.choices(string.digits + string.ascii_letters, k=15))
                # Hash the password
                hashed_password = hash_password(password)
                # Insert the user data into the database
                cursor.execute("INSERT INTO users (id, username, password, APIkey) VALUES (?, ?, ?, ?)",
                               (user_id, username, hashed_password, api_key))
                connection.commit()
                msg = "User Registered Successfully"
                return render_template('login.html', success_msg=msg)

    return render_template('login.html')

# Route for the data dashboard
# http://localhost:8080/data
@app.route('/data', methods=['GET'])
def data():
    # Connect to the database
    connection = sqlite3.connect('user_LoginData.db')
    cursor = connection.cursor()

    # Fetch data from the reports table
    cursor.execute("SELECT * FROM reports")
    data = cursor.fetchall()

    # Close the database connection
    connection.close()

    # Pass the fetched data to the data.html template
    return render_template('data.html', data=data)

# http://localhost:8080/report
@app.route('/report', methods=['POST'])
def report():
    # Handle form submission here
    # 1. Characterize the Description input----------------------------------------
    description = request.form['description']
    apikey = 'AIzaSyAfCgbI39QWvIdlILA1-qqGynwNfxJz05o'
    host = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    params = {"key": apikey}
    body = {"contents": [{"parts":[{"text": f"Can you please characterize the following description {description}. Give is a 1 word description"}]}]}
    res = requests.post(host, params=params,json=body)
    char_desc = res.json()['candidates'][0]['content']['parts'][0]['text']
    print(char_desc)

    # 2. Get IP Address of User----------------------------------------
    ip_address = request.remote_addr
    print(f'Users IP Address: {ip_address}')

    # 3. Get the USERNAME and ID from the APIKEY
    api_key = request.form['api_key']
    connection = sqlite3.connect('user_LoginData.db')
    cursor = connection.cursor()

    # Fetch user data from the database based on the API key
    cursor.execute("SELECT username, ID FROM users WHERE APIkey=?", (api_key,))
    user_data = cursor.fetchone()

    if user_data:
        username, user_id = user_data  # Extract username and ID from user data
        print(f'Username: {username}, User ID: {user_id}\n')
    else:
        # Handle case where user data is not found
        return "User not found"


    # 4. Use the GPS Coordinates to reverse geolocation to get State, Country----------------------------------------
    latitude = request.form['lat']
    longitude = request.form['lon']
    # Nominatim reverse geocoding API endpoint
    base = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json"
    # Make a GET request to the API
    res = requests.get(base)
    data = res.json()
    address = data.get('display_name', 'Address not found')
    print("Address:", address)
    # Split the address by commas, get the state and country
    address_parts = address.split(',')
    state = address_parts[-3].strip()  # Georgia
    country = address_parts[-1].strip()  # United States
    print(f'The adress is: {state}, {country}')

    # 5. Use Open Meteo to Predict the Weather----------------------------------------
    host = "https://api.open-meteo.com"
    resource = "/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m",
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York",
        "forecast_days": 1
    }
    res = requests.get(host+resource,params=params)
    data = res.json()
    temperature = data['current']['temperature_2m']
    formatted_temp = f"{temperature}°F"

    # 6. Get Date and Time for Submission----------------------------------------    
    submission_time = datetime.now().strftime("%m/%d/%Y - %H:%M.%S")

    # 7. Get File Name----------------------------------------    
    uploaded_file = request.files['file']
    file_name = save_uploaded_file(uploaded_file)

    # Get the current report number and submit data to DB
    connection = sqlite3.connect('user_LoginData.db')
    cursor = connection.cursor()
    cursor.execute("SELECT MAX(reportnumber) FROM reports")
    max_report_number = cursor.fetchone()[0]
    if max_report_number is None:
        report_number = 1
    else:
        report_number = max_report_number + 1

    # Insert data into the reports table
    cursor.execute("""INSERT INTO reports (username, id, reportnumber, datetime, ip, latitude, longitude, state, country, temperature, filepath, description, characterization) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                   (username, user_id, report_number, submission_time, ip_address, latitude, longitude, state, country, formatted_temp, file_name, description, char_desc))
    connection.commit()
    connection.close()


    return render_template('report.html', username=username, user_id=user_id, description=description, char_desc=char_desc, ip_address=ip_address, state=state, country=country, temp=formatted_temp, date_time=submission_time, latitude=latitude, longitude=longitude, file_name=file_name)

# Route for inserting data
# http://localhost:8080/home/<username>
@app.route('/home/<username>', methods=['GET'])
def insert(username):
    connection = sqlite3.connect('user_LoginData.db')
    cursor = connection.cursor()

    # Fetch user data from the database based on the username
    cursor.execute("SELECT APIkey FROM users WHERE username=?", (username,))
    user_data = cursor.fetchone()

    if user_data:
        api_key = user_data[0]  # Extract API key from user data
        print(f'API Key: {api_key}\n')
        return render_template('insert.html', username=username, api_key=api_key)
    else:
        # Handle case where user data is not found
        return "User not found"


if __name__ == '__main__':
    app.run(debug=True, port=8080)
