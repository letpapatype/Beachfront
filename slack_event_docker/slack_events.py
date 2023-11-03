import logging
import requests
import json
import os
import datetime
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

"""
TODO: Create and import breezeway module
TODO: Create requirements.txt
TODO: Create AWS credentials
TODO: Create Serverless deployment script
"""


logging.basicConfig(level=logging.DEBUG)
app = App(process_before_response=True)

slack_users = {
    "124692": "U04UD9J1708",
    "27677": "U01BWDVQJH3",
    "28142": "U01C889UD6K",
    "4072": "UCTQ19N59",
    "160596": "U05SD306DMX",
    "59514": "U02MUS3F6MD",
    "152111": "U05JG8MJALT",
    "151485": "U05J7NF1QPM",
    "75934": "U03BES1BLMQ",
    "87719": "U03NMETUUHX"
}


def create_task(unit, greeter, eta, door_code):

    client_id = os.environ['BRZW_CLIENT_ID']
    client_secret = os.environ['BRZW_CLIENT_SECRET']
    url = 'https://api.breezeway.io'

    # get the token
    url_for_token = f"{url}/public/auth/v1/"

    payload = json.dumps({
        "client_id": client_id,
        "client_secret": client_secret
    })

    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url_for_token, headers=headers, data=payload)

    if response.status_code != 200:
        print("Error getting token")
        print(response.text)
    else:
        print("Token received")

    token = response.json()['access_token']

    url = f"{url}/public/inventory/v1/task/"

    today = datetime.date.today()

    # convert HH:MM to HH:MM:SS
    eta = f"{eta}:00"

    payload={
        "reference_property_id": f"{unit}",
        "type_department": "inspection",
        "type_priority": "normal",
        "name": "Meet and Greet",
        "description": f"Guest Door Code: {door_code}",
        "scheduled_date": f"{today}",
        "scheduled_time": f"{eta}",
        "assignments": [
            f"{greeter}"
        ],
        "template_id": 7730,
    }

    headers = {
        'Authorization': f"JWT {token}",
        'Content-Type': 'application/json'
    }

    print(payload)
    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    print(response.text)

    task_id = response.json()['id']

    return task_id


"""
Dev Server for Slack Bolt
app = App()
"""




@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@app.action("schedule_meet_and_greet")
def schedule_meet_and_greet(ack, body, logger, client):
    ack()
    logger.info(body)
    logger.info(body['user']['id'])
    logger.info(body['trigger_id'])
    logger.info(body['message'])
    logger.info(body['actions'][0]['value'])

    # split action value by _ and select the first value
    unit = body['actions'][0]['value'].split('_')[0]

    ts = body['container']['message_ts']
    channel = body['container']['channel_id']

    user = body['user']['id']

    unit_brzw_id = body['actions'][0]['value'].split('_')[1]

    door_code = body['actions'][0]['value'].split('_')[2]

    # value "P817-3_58_289606"

    client.views_open(
        trigger_id=body['trigger_id'],
        view={
            "type": "modal",
            "callback_id": "scheduling_task",
            "title": {
                "type": "plain_text",
                "text": "Schedule Meet and Greet"
            },
            "submit": {
                "type": "plain_text",
                "text": "Schedule"
            },
            "blocks": [
                {
                    "type": "section",
                    "block_id": f"info_{unit_brzw_id}_{door_code}_{unit}_{ts}_{channel}",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hey there @<@{user}>! Let's schedule a meet and greet."
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "input",
                    "block_id": "select-greeter",
                    "label": {
                        "type": "plain_text",
                        "text": f"Who would you like to schedule for the {unit} meet and greet?",
                        "emoji": True
                    },
                    "element": {
                        "type": "radio_buttons",
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Sarah G",
                                    "emoji": True
                                },
                                "value": "124692"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Allie",
                                    "emoji": True
                                },
                                "value": "27677"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Nina",
                                    "emoji": True
                                },
                                "value": "28142"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Jeff",
                                    "emoji": True
                                },
                                "value": "4072"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Kevin",
                                    "emoji": True
                                },
                                "value": "160596"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Kyle",
                                    "emoji": True
                                },
                                "value": "59514"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Valentin",
                                    "emoji": True
                                },
                                "value": "152111"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Freud",
                                    "emoji": True
                                },
                                "value": "151485"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Aaron",
                                    "emoji": True
                                },
                                "value": "75934"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Wyatt",
                                    "emoji": True
                                },
                                "value": "87719"
                            }
                        ],
                        "action_id": "select-greeter-action"
                    }
                },
                {
                    "type": "input",
                    "block_id": "datepicker",
                    "element": {
                        "type": "timepicker",
                        "initial_time": "16:00",
                        "timezone": "America/Los_Angeles",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select time",
                            "emoji": True
                        },
                        "action_id": "timepicker-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "What is the guest's estimated time of arrival?",
                        "emoji": True
                    }
                }
            ]
        }
    )

# create a function for when the view is submitted
@app.view_submission("scheduling_task")
def handle_submission(ack, body, logger, client):
    ack()
    slack_scheduler = body['user']['id']
    logger.info(body['view']['blocks'][0]['block_id'])

    unit = body['view']['blocks'][0]['block_id'].split('_')[1]
    door_code = body['view']['blocks'][0]['block_id'].split('_')[2]
    real_unit = body['view']['blocks'][0]['block_id'].split('_')[3]
    ts = body['view']['blocks'][0]['block_id'].split('_')[4]
    channel = body['view']['blocks'][0]['block_id'].split('_')[5]

    logger.info(unit)
    logger.info(door_code)
    logger.info(real_unit)

    selected_greeter = body['view']['state']['values']['select-greeter']['select-greeter-action']['selected_option']['value']
    eta = body['view']['state']['values']['datepicker']['timepicker-action']['selected_time']

    logger.info(selected_greeter)
    logger.info(eta)

    logger.info("This is the body of the view submission")
    task_id = create_task(unit, selected_greeter, eta, door_code)

    if selected_greeter in slack_users:
        assigned_to = slack_users[selected_greeter]

    schedule_post = client.conversations_replies(channel=channel, ts=ts)

    logger.info(schedule_post)

    text = schedule_post['messages'][0]['text']
    blocks = schedule_post['messages'][0]['blocks']

    # find the block_id that matches 'unit', and change that block value to {}
    for block in blocks:
        if block['block_id'] == unit:
            logger.info(block)

            # remove the block from the list
            blocks.remove(block)

    # update the message with the new blocks
    update_post = client.chat_update(channel=channel, ts=ts, blocks=blocks)
    
    assert update_post["ok"]

    # notify the scheduler that the task has been scheduled
    notify_scheduler = client.chat_postMessage(channel=channel, text=f"Thanks <@{slack_scheduler}>! I've scheduled a meet and greet for {real_unit}", thread_ts=ts)
    
    assert notify_scheduler["ok"]
    
    # notify the greeter that they have been scheduled
    notify_greeter = client.chat_postMessage(channel=channel, text=f"<@{assigned_to}> you have been scheduled for {real_unit} with an eta of {eta}. <https://app.breezeway.io/task/{task_id}|View Task>")

    assert notify_greeter["ok"]



# from flask import Flask, request

# flask_app = Flask(__name__)
# handler = SlackRequestHandler(app)


# @flask_app.route("/slack/events", methods=["POST"])
def lambda_handler(event, context):
    logging.info(event)
    slack_handler = SlackRequestHandler(app)
    return slack_handler.handle(event, context)

    #return slack_handler.handle(event, context)




