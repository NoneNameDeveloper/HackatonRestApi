cd "$(dirname "$0")"
rsync -rPvah --exclude 'venv' --exclude '__pycache__' * tada@greed.implario.net:/home/tada/api_patches/