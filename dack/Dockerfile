# Use the AWS Lambda Python 3.8 image
FROM amazon/aws-lambda-python:3.11

# TODO: add crm database env vars
ARG SLACK_BOT_TOKEN
ARG SLACK_SIGNING_SECRET
ARG BRZW_CLIENT_SECRET
ARG BRZW_CLIENT_ID

# TODO: add crm database env vars
ENV SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
ENV SLACK_SIGNING_SECRET=$SLACK_SIGNING_SECRET
ENV BRZW_CLIENT_SECRET=$BRZW_CLIENT_SECRET
ENV BRZW_CLIENT_ID=$BRZW_CLIENT_ID

# Copy the requirements.txt file into the image
COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --target ${LAMBDA_TASK_ROOT}

# Copy the Python file into the image
COPY dack.py ${LAMBDA_TASK_ROOT}
COPY crm.py ${LAMBDA_TASK_ROOT}

# Set the command to run when the container starts
CMD ["dack.handler"]