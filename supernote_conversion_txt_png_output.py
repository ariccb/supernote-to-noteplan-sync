import os
import re
import subprocess
import json
import sys
from datetime import datetime

# Read input variables from stdin
input_data = sys.stdin.read()
input_vars = json.loads(input_data)

supernote_parent_storage_path = input_vars["supernote_parent_storage_path"]
supernote_tool_path = input_vars["supernote_tool_path"]
supernote_tool_image_conversion_type = input_vars["supernote_tool_image_conversion_type"]
base_noteplan_path = input_vars["base_noteplan_path"]

supernote_path = os.path.join(supernote_parent_storage_path, "Supernote", "Note")

# Initialize list to store note data
notes_data = []

def get_file_id(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()
        match = re.search(b'<FILE_ID:(.*?)>', content)
        return match.group(1).decode('utf-8', errors='ignore') if match else None

def get_page_count(note_file_path):
    command = [supernote_tool_path, "analyze", note_file_path]
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    print(f"Command output: {result.stdout}")

    match = re.search(r'Pages:\s*(\d+)', result.stdout)
    if match:
        return int(match.group(1))
    else:
        return 0

def extract_text_from_note_pages(note_file_path, output_folder, file_id, page_count):
    all_text = ""
    if page_count == 0:
        page = 0
        while True:
            text_output_path = os.path.join(output_folder, f"{file_id}_page_{page}_text.txt")
            command = [supernote_tool_path, "convert", "--policy=loose", "-t", "txt", "-a", note_file_path, text_output_path, "--page", str(page)]
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)
            print(f"Command output: {result.stdout}")

            if os.path.exists(text_output_path):
                with open(text_output_path, 'r', encoding='utf-8') as f:
                    page_text = f.read().strip()
                    if page_text:
                        all_text += page_text + "\n\n"
                        page += 1
                    else:
                        break
            else:
                break
    else:
        for page in range(page_count):
            text_output_path = os.path.join(output_folder, f"{file_id}_page_{page}_text.txt")
            command = [supernote_tool_path, "convert", "--policy=loose", "-t", "txt", "-a", note_file_path, text_output_path, "--page", str(page)]
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)
            print(f"Command output: {result.stdout}")

            if os.path.exists(text_output_path):
                with open(text_output_path, 'r', encoding='utf-8') as f:
                    page_text = f.read().strip()
                    if page_text:
                        all_text += page_text + "\n\n"

    if all_text.strip():
        return all_text.strip()
    else:
        return None

def convert_note_to_images(note_file_path, output_folder, file_id, page_count):
    generated_files = []
    if page_count == 0:
        page = 0
        while True:
            image_output_path = os.path.join(output_folder, f"{file_id}_page_{page}.{supernote_tool_image_conversion_type}")
            command = [supernote_tool_path, "convert", "--policy=loose", "-t", supernote_tool_image_conversion_type, "-a", note_file_path, image_output_path, "--page", str(page)]
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)
            print(f"Command output: {result.stdout}")

            if os.path.exists(image_output_path):
                generated_files.append(image_output_path)
                page += 1
            else:
                break
    else:
        for page in range(page_count):
            image_output_path = os.path.join(output_folder, f"{file_id}_page_{page}.{supernote_tool_image_conversion_type}")
            command = [supernote_tool_path, "convert", "--policy=loose", "-t", supernote_tool_image_conversion_type, "-a", note_file_path, image_output_path, "--page", str(page)]
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)
            print(f"Command output: {result.stdout}")

            if os.path.exists(image_output_path):
                generated_files.append(image_output_path)

    if generated_files:
        print(f"Successfully created the following files: {', '.join(generated_files)}")
        return generated_files
    else:
        print(f"Failed to create expected image files for {note_file_path}")
        return []

# Main processing loop
note_files = [os.path.join(root, file) for root, _, files in os.walk(supernote_path) for file in files if file.endswith('.note')]

for note_file in note_files:
    print(f"\nProcessing file: {note_file}")
    file_id = get_file_id(note_file)
    if file_id is None:
        print(f"Warning: Could not find FILE_ID in {note_file}. Skipping.")
        continue

    note_file_name_without_ext = os.path.splitext(os.path.basename(note_file))[0].strip()
    note_full_path = note_file
    note_directory_path = os.path.dirname(note_file).replace(supernote_path, "").strip("/")
    if note_directory_path == "":
        note_directory_path = "/"

    attachments_path = os.path.join(base_noteplan_path, "00 - Inbox", f"{note_file_name_without_ext}_attachments")
    if not os.path.exists(attachments_path):
        print(f"Creating new folder: {attachments_path}")
        os.makedirs(attachments_path)

    # Get page count
    page_count = get_page_count(note_full_path)
    if page_count == 0:
        print(f"Warning: Could not determine page count for {note_file}. Proceeding with unknown page count.")

    # Extract text from .note file
    text_extracted = extract_text_from_note_pages(note_full_path, attachments_path, file_id, page_count)
    if not text_extracted:
        # Retry text extraction
        print(f"Retrying text extraction for {note_file}")
        text_extracted = extract_text_from_note_pages(note_full_path, attachments_path, file_id, page_count)
        if not text_extracted:
            text_extracted = f"This .note file was not created using the Real-Time Recognition file type, so no text was able to be output\n{note_full_path}"
            print(f"Failed to extract text from {note_file} after retrying")

    # Convert the note file to images
    print(f"Attempting to convert {note_file} to {supernote_tool_image_conversion_type.upper()}")
    generated_files = convert_note_to_images(note_full_path, attachments_path, file_id, page_count)
    if not generated_files:
        # Retry image conversion
        print(f"Retrying image conversion for {note_file}")
        generated_files = convert_note_to_images(note_full_path, attachments_path, file_id, page_count)
        if not generated_files:
            generated_files = [f"The .note file conversion to images failed for some reason. Error output: {note_full_path}"]
            print(f"Failed to convert {note_file} to {supernote_tool_image_conversion_type.upper()} after retrying")

    # Collect data for JSON output
    note_data = {
        "filename": note_file_name_without_ext,
        "folder": note_directory_path,
        "text_recognition": text_extracted,
        "images": generated_files
    }
    notes_data.append(note_data)

    print(f"Finished processing {note_file}")
    print("-----------------------------------")

# Output the notes data as JSON to stdout
print(json.dumps(notes_data, indent=4))

print("Script completed.")
