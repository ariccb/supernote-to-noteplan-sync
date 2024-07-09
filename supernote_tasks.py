import sqlite3
import json
from datetime import datetime

# Path to your SQLite database
db_path = '/Users/acbouwers/Library/Containers/5E209006-499F-43DC-BD7C-EC697B9B4D64/Data/Library/Application Support/com.ratta.supernote/677531935891181568/calendar_db.sqlite'

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fetch task groups to dynamically map task_list_id to tags
cursor.execute("SELECT task_list_id, title FROM task_group;")
task_groups = cursor.fetchall()

# Create a dictionary to map task_list_id to tag names
task_tag_mapping = {task_group[0]: task_group[1].replace(' ', '-').lower() for task_group in task_groups}

# Print task group mappings for verification (uncomment lines 19-22 to see)
# print("Task Group Mappings:")
# for task_list_id, title in task_tag_mapping.items():
#     print(f"Task List ID: {task_list_id}, Tag: {title}")

# Fetch tasks from the 'task' table
query = "SELECT id, task_list_id, task_id, title, detail, last_modified, recurrence, is_reminder_on, status, importance, due_time, completed_time, links, deleted, has_sync, sort, sort_completed, sort_time, planned_sort, planned_sort_time FROM task;"
cursor.execute(query)
tasks = cursor.fetchall()

# Close the connection
conn.close()

# Function to convert milliseconds timestamp to human-readable date
def millis_to_date(millis, date_format="%Y-%m-%d %I:%M %p"):
    try:
        if millis:
            return datetime.fromtimestamp(millis / 1000).strftime(date_format)
    except (ValueError, OSError):
        print(f"Invalid timestamp: {millis}")
        return ""
    return ""

# Convert task data to NotePlan markdown format
markdown_output = ""

for task in tasks:
    task_id, task_list_id, task_code, task_title, detail, last_modified, recurrence, is_reminder_on, status, importance, due_time, completed_time, links, deleted, has_sync, sort, sort_completed, sort_time, planned_sort, planned_sort_time = task

    # Determine task status
    if status == "completed":
        status_symbol = "[x]"
        done_time = ""
        if completed_time:
            done_time_str = millis_to_date(completed_time)
            done_time = f" @done({done_time_str})" if done_time_str else ""
    else:
        status_symbol = ""
        done_time = ""

    # Parse due_time to human-readable format if available
    due_date = ""
    if due_time:
        due_date_str = millis_to_date(due_time, '%Y-%m-%d')
        due_date = f" >{due_date_str}" if due_date_str else ""

    # Check if links are available and extract file name if present
    file_reference = ""
    if links:
        try:
            link_data = json.loads(links)
            if 'filePath' in link_data and link_data['filePath']:
                file_name = link_data['filePath'].split("/")[-1]
                file_reference = f" [[{file_name}]]"
        except json.JSONDecodeError:
            pass

    # Generate markdown line
    if status_symbol:
        line = f"* {status_symbol} {task_title}{file_reference}{due_date}{done_time}"
    else:
        line = f"* {task_title}{file_reference}{due_date}{done_time}"

    # Add group title as a tag if task_list_id matches the dynamic mapping
    if task_list_id and task_list_id in task_tag_mapping:
        line += f" #{task_tag_mapping[task_list_id]}"
    elif task_list_id:
        print(f"Warning: Unknown task_list_id '{task_list_id}' for task '{task_title}'")

    # Add the synced line id from the first 6 characters of task_id
    synced_id = task_code[:6]
    line += f" ^{synced_id}"

    markdown_output += line + "\n"

# Print markdown output
print(markdown_output)
