#!/bin/zsh
# Define the paths to the Supernote, Supernote Tool, and Obsidian directories
superNoteParentStoragePath="/Users/acbouwers/Library/Containers/5E209006-499F-43DC-BD7C-EC697B9B4D64/Data/Library/Application Support/com.ratta.supernote/677531935891181568"
superNotePath="${superNoteParentStoragePath}/Supernote/Note"
superNoteToolPath="/opt/homebrew/bin/supernote-tool"
superNoteToolConversionType="png"
# Define the paths to the NotePlan directories
notesApplicationStoragePath="/Users/acbouwers/Library/Containers/co.noteplan.NotePlan3/Data/Library/Application Support/co.noteplan.NotePlan3/Notes"
notesApplicationFileExt=".md"
notesApplicationInboxPath="${notesApplicationStoragePath}/00 - Inbox"
notesApplicationAttachmentSuffix="_attachments"
returnLine=$'\n'
# Get a list of all of the .note files in the Supernote directory
noteFiles=$(find "$superNotePath" -name "*.note")
# Iterate over each .note file and convert it to a PDF and image file
for noteFile in $noteFiles; do
# Get the file ID from the .note file
fileID=$(ggrep -oP '<FILE_ID:\K[^>]+' "$noteFile")
noteFileNameWithOutExt=$(basename "$noteFile" .note)
noteFullPath="$noteFile"

# Check if the Markdown file already contains a reference to the image file
existingMarkdownFileSearch=$(ggrep -R "${fileID}" "${notesApplicationStoragePath}"/*"${notesApplicationFileExt}")

if [ -z "$existingMarkdownFileSearch" ]; then
    newMarkdownFilePath="${notesApplicationInboxPath}/${noteFileNameWithOutExt}${notesApplicationFileExt}"
    noteDirectoryPath=$(dirname "$noteFile")
    noteTags=$(echo "${noteDirectoryPath#$superNoteParentStoragePath}" | sed 's/ //g' | sed 's/\//\n  - #/g')
    noteCreatedDate=$(stat -f "%Sc" "$noteFile")
    # If the Markdown file doesn't contain a reference to the image file, create a new MarkdownFile
    touch "$newMarkdownFilePath"
    echo "#${noteFileNameWithOutExt} ${returnLine}" >> "$newMarkdownFilePath"
    echo "---${returnLine}tags:${returnLine}${noteTags}${returnLine}---${returnLine}" >> "$newMarkdownFilePath"
    echo "- [ ] File Incoming SuperNote ${noteFileNameWithOutExt}>today" >> "$newMarkdownFilePath"
    echo "#### *SuperNote Files Do Not Edit Below This Line*" >> "$newMarkdownFilePath"

    touch -t $(date -j -f "%a %b %d %T %Y" "$noteCreatedDate" "+%Y%m%d%H%M.%S") "$newMarkdownFilePath"
    existingMarkdownFile="$newMarkdownFilePath"
else
    echo "Markdown Already Exists"
    existingMarkdownFile=$(echo "$existingMarkdownFileSearch" | head -n1 | cut -d':' -f1)
fi

attachmentsPath="${existingMarkdownFile%$notesApplicationFileExt}$notesApplicationAttachmentSuffix"

# check for existing PDF storage, create if not
if [ ! -d "$attachmentsPath" ]; then
    echo "New Folder ${attachmentsPath}"
    mkdir -p "$attachmentsPath"
fi
relativePathToExistingMarkDownFile="${noteFileNameWithOutExt}_attachments"
defaultConversionPath="${attachmentsPath}/${fileID}.${superNoteToolConversionType}"

# Generate the paths to the converted files
"$superNoteToolPath" convert -t "$superNoteToolConversionType" -a "$noteFullPath" "$defaultConversionPath"

iteration=0
stop=false
while [ "$stop" = false ] && [ $iteration -le 100 ]; do
    fileNameIteration="${fileID}_${iteration}.${superNoteToolConversionType}"
    pngPageNumberFilePath="${attachmentsPath}/${fileNameIteration}"

    if ! ggrep -q "$fileNameIteration" "$existingMarkdownFile" && [ -f "$pngPageNumberFilePath" ]; then
        embedRelatvePath="${relativePathToExistingMarkDownFile}/${fileNameIteration}"
        pngEmbed="![image](${embedRelatvePath})"
        echo "$pngEmbed" >> "$existingMarkdownFile"
        echo "Iteration $fileNameIteration added to $existingMarkdownFile"
    elif ggrep -q "$fileNameIteration" "$existingMarkdownFile"; then
        echo "Nothing needed to be added for iteration $fileNameIteration it already exists"
    else
        echo "Iteration $fileNameIteration does not exist"
        stop=true
    fi

    if [ "$stop" = false ]; then
        ((iteration++))
    fi
done
echo "Stopped at $iteration"
done
SuperNote Can export