#!/bin/bash

# TODO: modifications needed

# Bulk upload of the dash functions
# run './_upload_from_gh.sh' to upload the updated functions from GitHub. 

# Define base project directory
project_dir="/home/ubuntu/zenodo"
cd "$project_dir" || exit 1

# Create timestamped archive folder inside project
archive_dir="archive-$(date +%F-%H-%M)"
gh_root="https://raw.githubusercontent.com/iramat/iramat-functions/refs/heads/main/zenodo"

mkdir "$archive_dir"
echo "Created folder: $archive_dir"

# Move all contents of zenodo into archive (except self and archive)
rsync -av --remove-source-files \
  --exclude='_upload_from_gh.sh' \
  --exclude="$archive_dir" \
  --exclude='(archives)' \
  ./ "$archive_dir"

echo "All files moved to $archive_dir"

# Move archive folder into centralized (archives) directory
mkdir -p "(archives)"
mv "$archive_dir" "(archives)/"
echo "All files moved to '(archives)'"

# Re-download fresh files
wget "$gh_root/chips_to_zenodo.py"

