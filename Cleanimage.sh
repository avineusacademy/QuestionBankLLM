#!/bin/bash
# Remove all Docker images

image_ids=$(docker images -q)

if [ -z "$image_ids" ]; then
  echo "No Docker images to remove."
else
  docker rmi -f $image_ids
  echo "All Docker images removed."
fi
