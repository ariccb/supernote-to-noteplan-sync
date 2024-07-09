import os
import re
import subprocess
from datetime import datetime
import json

# Define the paths and variables
supernote_parent_storage_path = "/Users/acbouwers/Library/Containers/5E209006-499F-43DC-BD7C-EC697B9B4D64/Data/Library/Application Support/com.ratta.supernote/677531935891181568"
supernote_path = os.path.join(supernote_parent_storage_path, "Supernote", "Note")
supernote_tool_path = "/opt/homebrew/bin/supernote-tool"
supernote_tool_image_conversion_type = "png"  # Set this to either "png" or "pdf"
notes_application_storage_path = "/Users/acbouwers/Library/Containers/co.noteplan.NotePlan3/Data/Library/Application Support/co.noteplan.NotePlan3/Notes"
notes_application_file_ext = ".md"
notes_application_inbox_path = os.path.join(notes_application_storage_path, "00 - Inbox")
notes_application_attachment_suffix = "_attachments"
return_line = "\n"

# Initialize lists to track conversions
failed_conversions = []
successful_conversions = []

def get_file_id(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()
        match = re.search(b'<FILE_ID:(.*?)>', content)
        return match.group(1).decode('utf-8', errors='ignore') if match else None

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

def extract_text_from_note(note_file_path, text_output_path):
    try:
        command = [supernote_tool_path, "convert", "--policy=loose", "-t", "txt", "-a", note_file_path, text_output_path]
        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Command output: {result.stdout}")

        if os.path.exists(text_output_path):
            if os.path.getsize(text_output_path) > 0:
                print(f"Text extracted successfully to {text_output_path}")
                return True
            else:
                print(f"Text extraction produced an empty file for {note_file_path}")
                return False
        else:
            print(f"Text output file was not created: {text_output_path}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error extracting text from {note_file_path}: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_new_markdown_file(file_path, note_file_name_without_ext, note_tags, formatted_note_created_date):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"---{return_line}title: {note_file_name_without_ext} {return_line}")
        f.write(f"aliases:{return_line}tags: #{note_tags}{return_line}created: {formatted_note_created_date}{return_line}---{return_line}")
        f.write(f"#### Source:{return_line}#### Next:{return_line}#### Branch:{return_line}#### ---{return_line}")
        f.write(f"- [ ] File Incoming SuperNote {note_file_name_without_ext} >today{return_line}")
        f.write("\n## Supernote Sync - Do Not Edit Below This Line\n")
        f.write("---\n")
        f.write("### Supernote Text Recognition Results\n\n")
        f.write("### SuperNote Exported Images\n")

def update_existing_markdown_file(file_path):
    with open(file_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        sync_start = content.find("## Supernote Sync - Do Not Edit Below This Line")
        if sync_start != -1:
            content = content[:sync_start]
        f.seek(0)
        f.write(content)
        f.write("\n\n## Supernote Sync - Do Not Edit Below This Line\n")
        f.write("---\n")
        f.write("### Supernote Text Recognition Results\n\n")
        f.write("### SuperNote Exported Images\n")
        f.truncate()

def append_new_text(markdown_file, new_text):
    with open(markdown_file, 'r+', encoding='utf-8') as f:
        content = f.read()
        start_position = content.find("### Supernote Text Recognition Results")
        end_position = content.find("### SuperNote Exported Images")
        if start_position != -1 and end_position != -1:
            new_content = (
                content[:start_position + len("### Supernote Text Recognition Results\n\n")] +
                new_text + "\n\n" +
                content[end_position:]
            )
        else:
            # If the headers don't exist, append to the end of the file
            new_content = content + "\n\n### Supernote Text Recognition Results\n\n" + new_text + "\n\n### SuperNote Exported Images\n"

        f.seek(0)
        f.write(new_content)
        f.truncate()

def append_error_message(markdown_file, error_message, section):
    with open(markdown_file, 'r+', encoding='utf-8') as f:
        content = f.read()
        insert_position = content.find(section)
        if insert_position != -1:
            new_content = (
                content[:insert_position + len(section + "\n\n")] +
                error_message + "\n\n" +
                content[insert_position + len(section + "\n\n"):]
            )
        else:
            # If the header doesn't exist, append to the end of the file
            new_content = content + "\n\n" + section + "\n\n" + error_message

        f.seek(0)
        f.write(new_content)
        f.truncate()

def convert_note_to_images(note_file_path, output_folder, file_id):
    command = [
        supernote_tool_path,
        "convert",
        "--policy=loose",
        "-t", supernote_tool_image_conversion_type,
        "-a",
        note_file_path,
        os.path.join(output_folder, f"{file_id}.{supernote_tool_image_conversion_type}")
    ]

    try:
        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Command output: {result.stdout}")

        # Check for generated files
        generated_files = []
        for file in os.listdir(output_folder):
            if file.startswith(file_id) and file.endswith(f".{supernote_tool_image_conversion_type}"):
                generated_files.append(file)

        if generated_files:
            generated_files.sort()  # Ensure the files are in the correct order
            print(f"Successfully created the following files: {', '.join(generated_files)}")
            return generated_files
        else:
            print(f"Failed to create expected image files for {note_file_path}")
            return []
    except subprocess.CalledProcessError as e:
        print(f"Error converting {note_file_path} to {supernote_tool_image_conversion_type.upper()}: {e}")
        print(f"Error output: {e.stderr}")
        if "KeyError" in e.stderr:
            print("Color code error detected. This may be due to an unsupported color in the note.")
        return []

def append_image_references(markdown_file, image_references):
    with open(markdown_file, 'r+', encoding='utf-8') as f:
        content = f.read()
        insert_position = content.find("### SuperNote Exported Images")
        if insert_position != -1:
            new_content = (
                content[:insert_position + len("### SuperNote Exported Images\n")] +
                "\n".join(image_references) + "\n"
            )
        else:
            # If the header doesn't exist, append to the end of the file
            new_content = content + "\n\n### SuperNote Exported Images\n" + "\n".join(image_references) + "\n"

        f.seek(0)
        f.write(new_content)
        f.truncate()

def sync_note_to_correct_folder(note_file, file_id, note_file_name_without_ext, note_created_date):
    relative_path = os.path.relpath(note_file, supernote_path)
    note_folder = os.path.dirname(relative_path)
    note_folder_path = os.path.join(notes_application_storage_path, note_folder)

    if not os.path.exists(note_folder_path):
        os.makedirs(note_folder_path)

    new_markdown_file_path = os.path.join(note_folder_path, f"{note_file_name_without_ext}{notes_application_file_ext}")

    note_tags = note_folder.replace(" ", "").lower().replace("/", "/")
    note_tags = re.sub(r'(\d+)\.(\d+)', r'\1/\2', note_tags)
    formatted_note_created_date = note_created_date.strftime('%Y-%m-%d')

    create_new_markdown_file(new_markdown_file_path, note_file_name_without_ext, note_tags, formatted_note_created_date)
    return new_markdown_file_path

# Main processing loop
note_files = [os.path.join(root, file) for root, _, files in os.walk(supernote_path) for file in files if file.endswith('.note')]

for note_file in note_files:
    print(f"\nProcessing file: {note_file}")
    file_id = get_file_id(note_file)
    if file_id is None:
        print(f"Warning: Could not find FILE_ID in {note_file}. Skipping.")
        failed_conversions.append(note_file)
        continue

    note_file_name_without_ext = os.path.splitext(os.path.basename(note_file))[0].strip()
    note_created_date = datetime.fromtimestamp(os.path.getctime(note_file))

    existing_markdown_file = find_existing_markdown(file_id)

    if not existing_markdown_file:
        existing_markdown_file = sync_note_to_correct_folder(note_file, file_id, note_file_name_without_ext, note_created_date)
    else:
        update_existing_markdown_file(existing_markdown_file)

    attachments_path = existing_markdown_file.replace(notes_application_file_ext, notes_application_attachment_suffix)

    if not os.path.exists(attachments_path):
        print(f"Creating new folder: {attachments_path}")
        os.makedirs(attachments_path)

    # Extract text from .note file
    text_output_path = os.path.join(attachments_path, f"{file_id}_text.txt")
    text_extracted = extract_text_from_note(note_file, text_output_path)
    if not text_extracted:
        # Retry text extraction
        print(f"Retrying text extraction for {note_file}")
        text_extracted = extract_text_from_note(note_file, text_output_path)
        if not text_extracted:
            error_message = f"This .note file was not created using the Real-Time Recognition file type, so no text was able to be output\n{note_file}"
            append_error_message(existing_markdown_file, error_message, "### Supernote Text Recognition Results")
            print(f"Failed to extract text from {note_file} after retrying")
            failed_conversions.append(note_file)

    if text_extracted and os.path.exists(text_output_path):
        with open(text_output_path, 'r', encoding='utf-8') as f:
            new_text = f.read()
        if new_text.strip():
            append_new_text(existing_markdown_file, new_text)
            print(f"Updated text for {note_file_name_without_ext}")
            print(json.dumps({"text_recognition_results": new_text}))  # Output the converted text recognition results using JSON format
        else:
            print(f"Extracted text is empty for {note_file_name_without_ext}")
    else:
        print(f"Text file not created for {note_file_name_without_ext}")

    # Convert the note file to images
    print(f"Attempting to convert {note_file} to {supernote_tool_image_conversion_type.upper()}")
    generated_files = convert_note_to_images(note_file, attachments_path, file_id)
    if not generated_files:
        # Retry image conversion
        print(f"Retrying image conversion for {note_file}")
        generated_files = convert_note_to_images(note_file, attachments_path, file_id)
        if not generated_files:
            error_message = f"The .note file conversion to images failed for some reason. Error output: {note_file}"
            append_error_message(existing_markdown_file, error_message, "### SuperNote Exported Images")
            print(f"Failed to convert {note_file} to {supernote_tool_image_conversion_type.upper()} after retrying")
            failed_conversions.append(note_file)
            continue

    print(f"Successfully converted {note_file_name_without_ext} to {supernote_tool_image_conversion_type.upper()}")

    image_references = []
    for file_name in generated_files:
        relative_path = f"{note_file_name_without_ext}_attachments/{file_name}"
        image_embed = f"![image]({relative_path})"
        image_references.append(image_embed)
        print(f"Found {supernote_tool_image_conversion_type.upper()} file: {file_name}")

    if image_references:
        append_image_references(existing_markdown_file, image_references)
        print(f"Added {len(image_references)} {supernote_tool_image_conversion_type.upper()} references to {existing_markdown_file}")
    else:
        print(f"No {supernote_tool_image_conversion_type.upper()} files were found for {note_file_name_without_ext}")

    successful_conversions.append(note_file)

    print(f"Finished processing {note_file}")
    print("-----------------------------------")

# After processing all files, print summary
print("\nConversion Summary:")
print(f"Total files processed: {len(note_files)}")
print(f"Successful conversions: {len(successful_conversions)}")
print(f"Failed conversions: {len(failed_conversions)}")

if failed_conversions:
    print("\nThe following files failed conversion:")
    for file in failed_conversions:
        print(file)
else:
    print("\nAll files were converted successfully.")

print("Script completed.")
