#!/bin/bash


current_time=$(date)

disk_usage=$(df -h)


user_name=$(whoami)

echo "Report Generated on: $current_time" > log.txt
echo "Logged in user: $user_name" >> log.txt
echo "--- Disk Usage ---" >> log.txt
echo "$disk_usage" >> log.txt


if [ ! -d "deploy_app" ]; then
    echo "Creating directory: deploy_app"
    mkdir deploy_app
fi


mv log.txt deploy_app/

echo "System check complete. File moved to deploy_app/log.txt"