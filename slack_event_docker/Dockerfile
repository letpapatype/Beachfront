FROM amazon/aws-lambda-python:3.11

# Set environment var to your function name

ENV BRZW_CLIENT_ID = ""
ENV BRZW_CLIENT_SECRET = ""
ENV SLACK_BOT_TOKEN = ""
ENV SLACK_SIGNING_SECRET = ""


# Copy function code and dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --target ${LAMBDA_TASK_ROOT}

COPY slack_events.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "slack_events.lambda_handler" ]