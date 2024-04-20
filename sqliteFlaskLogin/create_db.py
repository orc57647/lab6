import sqlite3

# Specify the desired path for the database file
db_path = 'user_LoginData.db'

# Connect to the database using the specified path
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Define the SQL command to create the users table
command = """CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    password TEXT,
                    APIkey TEXT
                )"""

# Execute the SQL command
cursor.execute(command)

# Define the SQL command to create the second table with 15 unnamed columns
command = """CREATE TABLE IF NOT EXISTS reports(
                    username TEXT,
                    id INTEGER,
                    reportnumber INTEGER,
                    datetime TEXT,
                    ip TEXT,
                    latitude TEXT,
                    longitude TEXT,
                    state TEXT,
                    country TEXT,
                    temperature TEXT,
                    filepath TEXT,
                    description TEXT,
                    characterization TEXT
                )"""

# Execute the SQL command
cursor.execute(command)

# Commit the changes and close the connection
connection.commit()
connection.close()
