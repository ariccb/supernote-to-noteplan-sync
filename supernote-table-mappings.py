import sqlite3

# Path to your SQLite database
db_path = '/Users/acbouwers/Library/Containers/5E209006-499F-43DC-BD7C-EC697B9B4D64/Data/Library/Application Support/com.ratta.supernote/677531935891181568/calendar_db.sqlite'

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fetch task groups to dynamically map task_list_id to tags
cursor.execute("SELECT id, title FROM task_group;")
task_groups = cursor.fetchall()

# Print task group mappings
print("Task Group Mappings:")
for task_group in task_groups:
    print(f"ID: {task_group[0]}, Title: {task_group[1]}")

# Create a dictionary to map task_list_id to tag names
task_tag_mapping = {task_group[0]: task_group[1].replace(' ', '-').lower() for task_group in task_groups}

# Fetch tasks from the 'task' table
query = "SELECT id, title, due_time, completed_time, status, links, task_list_id FROM task;"
cursor.execute(query)
tasks = cursor.fetchall()

# Print task list
print("\nTask List with Task List IDs:")
for task in tasks:
    print(f"Task ID: {task[0]}, Task List ID: {task[6]}, Title: {task[1]}, Due Time: {task[2]}, Completed Time: {task[3]}, Status: {task[4]}, Links: {task[5]}")

# Close the connection
conn.close()
