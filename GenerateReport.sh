#!/bin/bash

# Load logging functions
. ~/.zsh/log.sh

# Constant Variable Declaration
BASE_DIR="/home/sanjay/Development"
TARGET_REPO="$BASE_DIR/explore"
STATIC_FOLDER="$BASE_DIR/personal/Anki-helper-companion/static"
PYAN_DIR="$BASE_DIR/personal/pyan"
PROCESSOR_DIR="$BASE_DIR/personal/Anki-helper-companion/processor"

log debug "Selected Target Repo: $TARGET_REPO"
log debug "Selected Static Folder: $STATIC_FOLDER"
log debug "Selected Pyan Directory: $PYAN_DIR"
log debug "Selected Processor Directory: $PROCESSOR_DIR"

export DEBUG=1

# Program variable declarations

# Enter github repo url with /blob/ in it to see the branch name main or master.
read -p "Enter the github repo url: " REPO_URL_REF
if [[ $REPO_URL_REF == *"/blob/"* ]]; then
    log debug "Repo URL is valid."
else
    log error "Repo URL is invalid. Exiting the program. It should have /blob/ in it."
    exit 1
fi

log info "Processing url $REPO_URL_REF, Please wait..."

REPO_NAME=$(echo $REPO_URL_REF | awk -F'/' '{print $5}')
REPO_URL=$(echo $REPO_URL_REF | awk -F'/blob/' '{print $1}')
REPO_BRANCH=$(echo $REPO_URL_REF | awk -F'/blob/' '{print $2}' | awk -F'/' '{print $1}')

log info "Repo Name: $REPO_NAME"
log info "Repo URL: $REPO_URL"
log info "Repo Branch: $REPO_BRANCH"

log info "Cloning the repo ($REPO_NAME) from the URL ($REPO_URL) to the target folder ($TARGET_REPO)"

# Check if the repo exists in the target folder
if [ -d "$TARGET_REPO/$REPO_NAME" ]; then
    log warn "Repo already exists in the target folder. Not cloning the repo."
else
    git clone $REPO_URL $TARGET_REPO/$REPO_NAME
    log info "Repo cloned successfully."
fi

log info "Generating the report for the repo...."

current_dir=$(pwd)

# Generate dot file
cd $PYAN_DIR
source .venv/bin/activate

# Add an option to provide custom folder from which to take the files. Default to all /**/ folders
read -p "Do you need to provide a custom folder path to take the files from? defaults to $TARGET_REPO/$REPO_NAME/ (y/n): " custom_folder
customPath="$TARGET_REPO/$REPO_NAME/"

export JSON_FILE=$STATIC_FOLDER/$REPO_NAME.json
export DOT_FILE=$STATIC_FOLDER/$REPO_NAME.dot
export PROJECT_PATH=$TARGET_REPO/$REPO_NAME
export GITHUB_URL=$REPO_URL/blob/$REPO_BRANCH/


if [ "$custom_folder" == "y" ]; then
    customPath=$(find $TARGET_REPO/$REPO_NAME -type d | fzf)
    read -p "Enter a name for the custom path: " customPathName

    export JSON_FILE=$STATIC_FOLDER/$REPO_NAME-$customPathName.json
    export DOT_FILE=$STATIC_FOLDER/$REPO_NAME-$customPathName.dot

    log debug "Custom folder path selected: $customPath" with name $customPathName
fi

./.venv/bin/python -m pyan.main "$customPath/**/*.py" --uses --no-defines --colored --grouped --annotated --dot --file=$DOT_FILE
cd $current_dir

log debug "cd $PYAN_DIR && $PYAN_DIR/.venv/bin/python -m pyan.main $TARGET_REPO/$REPO_NAME/**/*.py --uses --no-defines --colored --grouped --annotated --dot --file=$DOT_FILE"

log info "Dot file generated successfully at $DOT_FILE"
log warn "Number of lines in the dot file ---->  $(wc -l $DOT_FILE) <---- !!"

# Generate JSON Report
log info "Generating JSON report for the repo...."

log debug "JSON_FILE: $JSON_FILE"
log debug "DOT_FILE: $DOT_FILE"
log debug "PROJECT_PATH: $PROJECT_PATH"
log debug "GITHUB_URL: $GITHUB_URL"

$PROCESSOR_DIR/.venv/bin/python $PROCESSOR_DIR/main.py

log info "JSON report generated successfully at $STATIC_FOLDER/$REPO_NAME.json"
log info "Operation Completed. Generating the report for the repo $REPO_NAME is completed successfully."