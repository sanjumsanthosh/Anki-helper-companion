#!/bin/bash

. ~/.zsh/log.sh

# Constant Variable Declaration
TARGET_REPO="/home/sanjay/Development/explore"
STATIC_FOLDER="/home/sanjay/Development/personal/Anki-helper-companion/static"

log debug "Selected Target Repo: $TARGET_REPO"
log debug "Selected Static Folder: $STATIC_FOLDER"

export DEBUG=1

# Program variable declarations

# Enter github repo url with /blob/ in it to see the brach name main or master.
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
cd /home/sanjay/Development/personal/pyan 
source .venv/bin/activate

# add an option to provide custom folder from which to take the files. default to all /**/ foldrs
read -p "Do you need to provide a custom folder path to take the files from? defaults to "$TARGET_REPO/$REPO_NAME/" (y/n): " custom_folder
customPath="$TARGET_REPO/$REPO_NAME/"
if [ $custom_folder == "y" ]; then
    customPath=$(find $TARGET_REPO/$REPO_NAME -type d | fzf)
    log debug "Custom folder path selected: $customPath"
fi

# ./.venv/bin/python -m pyan.main "$TARGET_REPO/$REPO_NAME/**/*.py" --uses --no-defines --colored --grouped --annotated --dot --file=$STATIC_FOLDER/$REPO_NAME.dot
./.venv/bin/python -m pyan.main "$customPath/**/*.py" --uses --no-defines --colored --grouped --annotated --dot --file=$STATIC_FOLDER/$REPO_NAME.dot
cd $current_dir

log debug "cd /home/sanjay/Development/personalpyan && /home/sanjay/Development/personalpyan/.venv/bin/python -m pyan.main $TARGET_REPO/$REPO_NAME/**/*.py --uses --no-defines --colored --grouped --annotated --dot --file=$STATIC_FOLDER/$REPO_NAME.dot"

log info "Dot file generated successfully. at $STATIC_FOLDER/$REPO_NAME.dot"
log info "Number of lines in the dot file ---->  $(wc -l $STATIC_FOLDER/$REPO_NAME.dot)"

# pring how to the above command looks like 


# Generate JSON Report

log info "Generating JSON report for the repo...."

export JSON_FILE=$STATIC_FOLDER/$REPO_NAME.json
export DOT_FILE=$STATIC_FOLDER/$REPO_NAME.dot
export PROJECT_PATH=$TARGET_REPO/$REPO_NAME
export GITHUB_URL=$REPO_URL/blob/$REPO_BRANCH/

log debug "JSON_FILE: $JSON_FILE"
log debug "DOT_FILE: $DOT_FILE"
log debug "PROJECT_PATH: $PROJECT_PATH"
log debug "GITHUB_URL: $GITHUB_URL"

/home/sanjay/Development/personal/Anki-helper-companion/processor/.venv/bin/python /home/sanjay/Development/personal/Anki-helper-companion/processor/main.py

log info "JSON report generated successfully. at $STATIC_FOLDER/$REPO_NAME.json"

log info "Operation Completed. Generating the report for the repo $REPO_NAME is completed successfully."