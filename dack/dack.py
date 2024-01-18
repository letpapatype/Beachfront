import logging
import requests
import json
import os
import datetime
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from crm import get_reservation

# from slack_bolt.adapter.flask import SlackRequestHandler
# from flask import Flask, request


app = App(token=os.environ['SLACK_BOT_TOKEN'], signing_secret=os.environ['SLACK_SIGNING_SECRET'], process_before_response=True)
logging.basicConfig(level=logging.DEBUG)

# leverage boto3 to get the PEM key from SSM
# ssm = boto3.client('ssm')
# response = ssm.get_parameter(
#     Name='PEM_KEY',
#     WithDecryption=True
# )

# set the contents of $PEM_KEY to a file to use in a sql query
# with open('/tmp/PEM_KEY', 'w') as f:
#     f.write(os.environ['PEM_KEY'])


def create_task(unit, cleaner, checkout_date, time):

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
    sch_time = f"{time}:00"

    print (f"Unit: {unit}")
    print (f"Cleaner: {cleaner}")
    print (f"Checkout Date: {checkout_date}")
    print (f"Checkout Time: {sch_time}")


    payload={
        "reference_property_id": f"{unit}",
        "type_department": "housekeeping",
        "type_priority": "normal",
        "name": "Upholstery Cleaning (¡PERRO! Limpieza de Tapiceria)",
        "scheduled_date": f"{checkout_date}",
        "scheduled_time": f"{sch_time}",
        "assignments": [
            f"{cleaner}"
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


@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@app.action("dog_cleaning")
def schedule_dog_cleaning(ack, body, logger, client):
    ack()
    logger.info(body['user']['id'])
    print(body['user']['id'])
    user = body['user']['id']
    logger.info(body['trigger_id'])
    print(body['trigger_id'])
    logger.info(body['message'])
    print(body['message'])
    logger.info(body['actions'][0]['value'])
    print(body['actions'][0]['value'])

    ts = body['container']['message_ts']

    value = body['actions'][0]['value'].split('_')
    property_to_clean = value[0]
    checkout_time = value[1]
    checkout_date = value[2]
    unit = value[3]
    pretty_date = value[4]
    cost = value[5]
    in_or_out = value[6]

    channel = body['channel']['id']

    logger.info(f"Property to clean: {property_to_clean}")
    logger.info(f"Checkout time: {checkout_time}")
    logger.info(f"Checkout date: {checkout_date}")
    logger.info(f"Unit: {unit}")
    logger.info(f"Pretty date: {pretty_date}")
    logger.info(f"Channel: {channel}")
    logger.info(f"TS: {ts}")
    logger.info(f"User: {user}")
    logger.info(f"Trigger ID: {body['trigger_id']}")

    view = {
        "type": "modal",
        "callback_id": "scheduling_dog",
        "title": {
            "type": "plain_text",
            "text": "Schedule Dog Cleaning",
        },
        "submit": {
            "type": "plain_text",
            "text": "Schedule"
        },
        "blocks": [
            {
                "type": "section",
                "block_id": f"{ts}_{property_to_clean}_{checkout_time}_{checkout_date}_{channel}_{unit}_{cost}_{in_or_out}",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey <@{user}>\n\nSchedule a cleaning for {unit} on {pretty_date} at {checkout_time}?"
                }
            },
            {
                "type": "input",
                "block_id": "select-cleaner",
                "label": {
                    "type": "plain_text",
                    "text": f"Who would you like to schedule for the cleaning?",
                    "emoji": True
                },
                "element": {
                    "type": "radio_buttons",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Cristian M",
                                "emoji": True
                            },
                            "value": "46589"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Ismael",
                                "emoji": True
                            },
                            "value": "4052"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Rocky",
                                "emoji": True
                            },
                            "value": "37978"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Roberto",
                                "emoji": True
                            },
                            "value": "4589"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Jose",
                                "emoji": True
                            },
                            "value": "64740"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Uriel",
                                "emoji": True
                            },
                            "value": "4062"
                        }
                    ],
                    "action_id": "schedule_dog_cleaning"
                }
            },     
        ]
    }


    # value "P817-3_58_289606"

    client.views_open(
        trigger_id=body['trigger_id'],
        view=view
    )

# create a function for when the view is submitted
@app.view_submission("scheduling_dog")
def handle_submission(ack, body, logger, client):
    ack()
    slack_scheduler = body['user']['id']
    logger.info(body['view']['blocks'][0]['block_id'])

    channel = body['view']['blocks'][0]['block_id'].split('_')[4]
    logger.info(f"channel: {channel}")

    ts = body['view']['blocks'][0]['block_id'].split('_')[0]
    logger.info(f"ts: {ts}")
    property_to_clean = body['view']['blocks'][0]['block_id'].split('_')[1]
    logger.info(f"property_to_clean: {property_to_clean}")
    checkout_time = body['view']['blocks'][0]['block_id'].split('_')[2]
    logger.info(f"checkout_time: {checkout_time}")
    checkout_date = body['view']['blocks'][0]['block_id'].split('_')[3]
    logger.info(f"checkout_date: {checkout_date}")
    cleaner = body['view']['state']['values']['select-cleaner']['schedule_dog_cleaning']['selected_option']['value']
    logger.info(f"cleaner: {cleaner}")
    unit = body['view']['blocks'][0]['block_id'].split('_')[5]
    print(f"unit: {unit}")
    cost = body['view']['blocks'][0]['block_id'].split('_')[6]
    print(f"cost: {cost}")
    in_or_out = body['view']['blocks'][0]['block_id'].split('_')[7]

    task_id = create_task(property_to_clean, cleaner, checkout_date, checkout_time)

    brzw_task_ling = f"https://app.breezeway.io/task/{task_id}"

    # update the original message
    notify_team = client.chat_postMessage(
        channel=channel,
        thread_ts=ts,
        text=f"Thanks for scheduling <@{slack_scheduler}> :rocket:\n<{brzw_task_ling} | View Task {task_id}>\n\nHey <!subteam^S05UL6NUWNS> has schedule upholstery cleaning. Please make the necessary revisions in Track."
    )

    assert notify_team["ok"]

    reservation, track_url = get_reservation(unit, check_date=checkout_date, in_or_out=in_or_out)
    print(f"Reservation: {reservation}")
    print(f"Track URL: {track_url}")

    # sales_channel = 'C0LB0GGQN'

    # sales_notification = client.chat_postMessage(
    #     channel=sales_channel,
    #     thread_ts=ts,
    #     text=f"Hey <!subteam^S05UL6NUWNS>, please make the necessary revisions in Track.\n<{track_url} | View Reservation {reservation}>\nAdditional costs: {cost}"
    # )

    # assert sales_notification["ok"]


def handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)

# Flask server for Slack Bolt
# flask_app = Flask(__name__)
# handler = SlackRequestHandler(app)

# @flask_app.route("/slack/events", methods=["POST"])
# def slack_events():
#     return handler.handle(request)









