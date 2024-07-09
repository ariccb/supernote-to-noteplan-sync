
import os
import re
import subprocess
from datetime import datetime

# Define the paths and variables
supernote_parent_storage_path = "/Users/acbouwers/Library/Containers/5E209006-499F-43DC-BD7C-EC697B9B4D64/Data/Library/Application Support/com.ratta.supernote/677531935891181568"
supernote_path = os.path.join(supernote_parent_storage_path, "Supernote", "Note")
supernote_tool_path = "/opt/homebrew/bin/supernote-tool"
supernote_tool_conversion_type = "png"
notes_application_storage_path = "/Users/acbouwers/Library/Containers/co.noteplan.NotePlan3/Data/Library/Application Support/co.noteplan.NotePlan3/Notes"
notes_application_file_ext = ".md"
notes_application_inbox_path = os.path.join(notes_application_storage_path, "00 - Inbox")
notes_application_attachment_suffix = "_attachments"
return_line = "\n"

# Initialize list to track failed conversions
failed_conversions = []

# Get a list of all .note files in the Supernote directory
note_files = [os.path.join(root, file) for root, _, files in os.walk(supernote_path) for file in files if file.endswith('.note')]

# Function to get file ID from .note file
def get_file_id(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()
        match = re.search(b'<FILE_ID:(.*?)>', content)
        return match.group(1).decode('utf-8', errors='ignore') if match else None

# Function to search for existing markdown file
def find_existing_markdown(file_id):
    for root, _, files in os.walk(notes_application_storage_path):
        for file in files:
            if file.endswith(notes_application_file_ext):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        if file_id in f.read():
                            return file_path
                except UnicodeDecodeError:
                    print(f"Warning: Unable to read {file_path} as UTF-8. Skipping.")
    return None


# Get a list of all .note files in the Supernote directory
note_files = [os.path.join(root, file) for root, _, files in os.walk(supernote_path) for file in files if file.endswith('.note')]


# Iterate over each .note file and convert it
for note_file in note_files:
    file_id = get_file_id(note_file)
    if file_id is None:
        print(f"Warning: Could not find FILE_ID in {note_file}. Skipping.")
        failed_conversions.append(note_file)
        continue

    note_file_name_without_ext = os.path.splitext(os.path.basename(note_file))[0].strip()
    note_full_path = note_file

    existing_markdown_file = find_existing_markdown(file_id)

    if not existing_markdown_file:
        new_markdown_file_path = os.path.join(notes_application_inbox_path, f"{note_file_name_without_ext}{notes_application_file_ext}")
        note_directory_path = os.path.dirname(note_file).strip()

        # Process note_tags to remove leading slash and ensure correct format
        note_tags = note_directory_path.replace(supernote_parent_storage_path, "").strip("/").replace(" ", "").lower()
        note_tags = note_tags.replace("/", "/")  # This replaces multiple slashes with a single slash, if any

        note_created_date = datetime.fromtimestamp(os.path.getctime(note_file))

        with open(new_markdown_file_path, 'w', encoding='utf-8') as f:
            f.write(f"---{return_line}title: {note_file_name_without_ext} {return_line}")
            f.write(f"aliases:{return_line}tags: #{note_tags}{return_line}---{return_line}")
            f.write(f"#### Source:{return_line}#### Next:{return_line}#### Branch:{return_line}#### ---{return_line}")
            f.write(f"- [ ] File Incoming SuperNote {note_file_name_without_ext} >today{return_line}")
            f.write("#### *SuperNote Files Do Not Edit Below This Line*\n")

        os.utime(new_markdown_file_path, (note_created_date.timestamp(), note_created_date.timestamp()))
        existing_markdown_file = new_markdown_file_path
    else:
        print("Markdown Already Exists")

    attachments_path = existing_markdown_file.replace(notes_application_file_ext, notes_application_attachment_suffix)

    if not os.path.exists(attachments_path):
        print(f"New Folder {attachments_path}")
        os.makedirs(attachments_path)

    relative_path_to_existing_markdown_file = f"{note_file_name_without_ext}_attachments"
    default_conversion_path = os.path.join(attachments_path, f"{file_id}.{supernote_tool_conversion_type}")

    # Convert the note file
    try:
        subprocess.run([supernote_tool_path, "convert", "--policy=loose", "-t", supernote_tool_conversion_type, "-a", note_full_path, default_conversion_path], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error converting {note_file}: {e}")
        print(f"Error output: {e.stderr}")
        print("Skipping this file and continuing with the next one.")
        failed_conversions.append(note_file)
        continue

    iteration = 0
    while True:
        file_name_iteration = f"{file_id}_{iteration}.{supernote_tool_conversion_type}"
        png_page_number_file_path = os.path.join(attachments_path, file_name_iteration)

        try:
            with open(existing_markdown_file, 'r', encoding='utf-8') as f:
                text_found = file_name_iteration in f.read()
        except UnicodeDecodeError:
            print(f"Warning: Unable to read {existing_markdown_file} as UTF-8. Skipping file content check.")
            text_found = False

        if not text_found and os.path.exists(png_page_number_file_path):
            embed_relative_path = f"{relative_path_to_existing_markdown_file}/{file_name_iteration}"
            png_embed = f"![image]({embed_relative_path})"
            with open(existing_markdown_file, 'a', encoding='utf-8') as f:
                f.write(f"{png_embed}\n")
            print(f"Iteration {file_name_iteration} added to {existing_markdown_file}")
        elif text_found:
            print(f"Nothing needed to be added for iteration {file_name_iteration} it already exists")
        else:
            print(f"Iteration {file_name_iteration} does not exist")
            break

        if iteration > 100:
            break
        iteration += 1

    print(f"Stopped at {iteration}")

# After processing all files, print summary
if failed_conversions:
    print("\nThe following files failed conversion:")
    for file in failed_conversions:
        print(file)
else:
    print("\nAll files were converted successfully.")

print("Script completed.")
