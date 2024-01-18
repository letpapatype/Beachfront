#!/bin/bash

# Load environment variables from .env file
export $(egrep -v '^#' .env | xargs)

# grep the version key from version.yaml
export VERSION=$(grep version version.yaml | cut -d':' -f2 | tr -d '[:space:]')

printf "Building version $VERSION\n"



# # Build the Docker image
docker build --build-arg SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN --build-arg SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET --build-arg BRZW_CLIENT_SECRET=$BRZW_CLIENT_SECRET --build-arg BRZW_CLIENT_ID=$BRZW_CLIENT_ID -t dack_bot:$VERSION .

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 382915386864.dkr.ecr.us-east-1.amazonaws.com

docker tag dack_bot:$VERSION 382915386864.dkr.ecr.us-east-1.amazonaws.com/dack_bot:$VERSION

docker push 382915386864.dkr.ecr.us-east-1.amazonaws.com/dack_bot:$VERSION