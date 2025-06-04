#!/bin/bash

# Build the Docker image
docker build -t fb_uploader .

# Run the container interactively and start uvicorn automatically
docker run -it --rm -p 8000:8000 fb_uploader uvicorn fb_uploader.upload:app --host 0.0.0.0 --port 8000
