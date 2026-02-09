#!/bin/bash

# 1. Capture the current date and time
# We use 'date' to get the timestamp so we know exactly when the check happened.
current_time=$(date)

# 2. Get Disk Usage
# 'df -h' shows disk space in "human-readable" format (GB/MB instead of bytes).
disk_usage=$(df -h)

# 3. Get the current logged-in user
# 'whoami' returns the username of the person running this script.
user_name=$(whoami)

# 4. Write this information to log.txt
# We use 'echo' to print the text and '>' to save/overwrite it into the file.
echo "Report Generated on: $current_time" > log.txt
echo "Logged in user: $user_name" >> log.txt
echo "--- Disk Usage ---" >> log.txt
echo "$disk_usage" >> log.txt
# Note: '>' creates/overwrites, while '>>' appends (adds to the end).

# 5. Directory Automation
# We check if 'deploy_app' exists using the -d flag.
# If it doesn't (!), we create it using 'mkdir'.
if [ ! -d "deploy_app" ]; then
    echo "Creating directory: deploy_app"
    mkdir deploy_app
fi

# 6. Move the log file
# We move (mv) the log.txt into the newly confirmed directory[cite: 11].
mv log.txt deploy_app/

echo "System check complete. File moved to deploy_app/log.txt"