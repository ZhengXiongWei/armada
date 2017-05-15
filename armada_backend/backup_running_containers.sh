#!/bin/bash

backups_dir="/opt/armada/saved_containers_backup"
mkdir -p "${backups_dir}"

# Wait for recovering and registering services in consul before making first backup.
sleep 60

while [ true ]; do
    now="$(date +%Y-%m-%d_%H-%M-%S)"
    backup_file_name="running_containers_parameters_${now}.json"
    python save_running_containers.py "${backups_dir}/${backup_file_name}" --force
    if [ $[ $RANDOM % 24 ] == 0 ]; then
        python /opt/armada-docker/armada_backend/clean_duplicated_saved_containers.py
    fi
    sleep 3600
done
