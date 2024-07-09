import sqlite3

# Path to your SQLite database
db_path = '/Users/acbouwers/Library/Containers/5E209006-499F-43DC-BD7C-EC697B9B4D64/Data/Library/Application Support/com.ratta.supernote/677531935891181568/calendar_db.sqlite'

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fetch all columns and a few sample entries from the task_group table
query = "PRAGMA table_info(task);"
cursor.execute(query)
columns = cursor.fetchall()

print("Columns in task table:")
for column in columns:
    print(column)

# Fetch all data from the task table
cursor.execute("SELECT * FROM task;")
tasks = cursor.fetchall()

# Print task group data
print("\nData from task table:")
for task in tasks:
    print(task)

# Close the connection
conn.close()