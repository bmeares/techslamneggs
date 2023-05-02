#! /bin/bash

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT="$(dirname "$HERE")"

IMAGE_NAME="techslamneggs"
DOCKERFILE_PATH="$ROOT/docker/$IMAGE_NAME/Dockerfile"

cd "$ROOT"

docker build \
  -t "$IMAGE_NAME" \
  --file "$DOCKERFILE_PATH" \
  .
