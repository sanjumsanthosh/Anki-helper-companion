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

# Get all repos in the target folder using awk
REPOS=$(ls $TARGET_REPO | awk '{print NR, $0, "'"$TARGET_REPO"'/"$0}')

# create a table view of the repos with columns, index, repo name, repo url using awk
# $ awk -F':' '{printf "%s%s", $2, (/^Grade/)?"\n":"\t|"}' file
awk -v repos="$REPOS" 'BEGIN {
    print "Index\t| Repo Name\t| Repo URL"
    split(repos, arr, "\n")
    for (i in arr) {
        split(arr[i], repo, " ")
        print repo[1] "\t| " repo[2] "\t| " repo[3]
    }
}'

MULI_SELECT_CLEANUP_FZF=$(echo "$REPOS" | fzf -m --preview 'echo {3}' --preview-window=right:70%:wrap)

# confirm deletion of the selected repos

# only if selected MULI_SELECT_CLEANUP_FZF
confirm_delete="n"
if [[ -n $MULI_SELECT_CLEANUP_FZF ]]; then
    read -p "Are you sure you want to delete the selected repos? (y/n): " confirm_delete
fi


if [[ $confirm_delete == "y" ]]; then
    # delete the selected repos
    log info  "$MULI_SELECT_CLEANUP_FZF" | awk '{print $3}' | xargs -I {} rm -rf {}
    log info "Selected repos deleted successfully."
else
    log info "Selected repos deletion cancelled."
fi

# Get dot files in the target folder using awk
DOT_FILES=$(ls $STATIC_FOLDER | grep -i ".dot" | awk '{print NR, $0, "'"$TARGET_REPO"'/"$0}')

awk -v dot_files="$DOT_FILES" 'BEGIN {
    print "Index\t| Dot File Name\t| Dot File Path"
    split(dot_files, arr, "\n")
    for (i in arr) {
        split(arr[i], dot_file, " ")
        print dot_file[1] "\t| " dot_file[2] "\t| " dot_file[3]
    }
}'

MULI_SELECT_CLEANUP_FZF=$(echo "$DOT_FILES" | fzf -m --preview 'echo {3}' --preview-window=right:70%:wrap)
MULI_SELECT_CLEANUP_FZF_JSON=$(echo "$MULI_SELECT_CLEANUP_FZF" | awk '{print $3}' | sed 's/.dot/.json/g')

confirm_delete="n"
if [[ -n $MULI_SELECT_CLEANUP_FZF ]]; then
    log info  "$MULI_SELECT_CLEANUP_FZF"
    read -p "Are you sure you want to delete the selected dot files and their corresponding json files? (y/n): " confirm_delete
fi


if [[ $confirm_delete == "y" ]]; then
    # delete the selected dot files and their corresponding json files
    log info  "$MULI_SELECT_CLEANUP_FZF" | awk '{print $3}' | xargs -I {} rm -rf {}
    log info  "$MULI_SELECT_CLEANUP_FZF_JSON" | xargs -I {} rm -rf {}
    log info "Selected dot files and their corresponding json files deleted successfully."
else
    log info "Selected dot files and their corresponding json files deletion cancelled."
fi