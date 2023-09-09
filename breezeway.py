import json
import requests
import sys
import datetime

raw_body = [input_data['body']]
body = json.loads(raw_body[0])
print(body)


# declare slack channel and token
# slack_channel = 'C02RRTP6V3L'
slack_token = ''


# set consistent variables
status = body['event_type']
print(status)

task_id = body['task']['id']
print(task_id)

department = body['task']['department']['name']
print(department)

priority = body['task']['priority']['name']
print(priority)

home = body['task']['home']['name']
print(home)

created_by = None
if body['task']['created_by'] is not None:
    created_by = body['task']['created_by']['full_name']

date = None
date = body['task']['due_date']

def reschedule_message(slack_channel, task_id, due_date, post_at):

    print('Searching for Ticket')
        # search for the message id in the channel for a post that contains the task id
    url = 'https://slack.com/api/conversations.history'

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f"Bearer {slack_token}"
    }
    payload = {
        "channel": slack_channel,
        "limit": 200
    }

    json_payload = json.dumps(payload)

    response = requests.request("POST", url, headers=headers, data=json_payload)

    if response.status_code != 200:
        print("Error getting message")
        print(response.text)
        sys.exit(1)
    # parse the response to get the message id

    body = json.loads(response.text)

    message_id = None

    for message in body['messages']:
        if f"Ticket: {task_id}" in message['text']:
            message_id = message['ts']
            print(message_id)
    if message_id:
        url = 'https://slack.com/api/chat.update'

        task_url = f"https://app.breezeway.io/task/{task_id}"

        headers = {
            # declare the charset to avoid errors
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {slack_token}',
        }
        
        payload = {
            "channel": slack_channel,
            "ts": message_id,
            "text": f"<{task_url}|Breezeway Task: {task_id}> has been scheduled for {due_date}",
            "attachments": []
        }

        json_payload = json.dumps(payload)

        response = requests.request("POST", url, headers=headers, data=json_payload)
    else:
        print("Message not found")


        print('Rescheduling')
        url = 'https://slack.com/api/chat.scheduledMessages.list'

        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {slack_token}',
        }

        payload = {
            "channel": slack_channel,
            "limit": 200
        }

        try:
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            print(response.json()['ok'])
        except Exception as e:
            print(e)

        scheduled_message_id = None
        for message in response.json()['scheduled_messages']:
            if f'Ticket: {task_id}' in message['text']:
                print(message['text'])
                scheduled_message_id = message['id']
                # delete_message(slack_channel, scheduled_message_id)
            else:
                print('Message not found')

        if scheduled_message_id:
            delete_message(slack_channel, scheduled_message_id)
        else:
            print('Message not found')
def delete_message(slack_channel, scheduled_message_id):

    """
    scheduled_message_id != post_at

    """

    if scheduled_message_id != post_at:

        url = 'https://slack.com/api/chat.deleteScheduledMessage'

        headers = {
            # declare the charset to avoid errors
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {slack_token}',
        }

        payload = {
            "channel": slack_channel,
            "scheduled_message_id": scheduled_message_id
        }

        try:
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            print(response.json()['ok'])
        except Exception as e:
            print(e)

        print('Message deleted')
        get_task_details(task_id)
    else:
        print('Message not deleted')

def get_task_details(task_id):
        # get the token from Breezeway
    # declare auth variables
    client_id = ''
    client_secret = ''
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
        sys.exit(1)
    else:
        print("Token received")

    token = response.json()['access_token']

    # get the task details
    url = f"{url}/public/inventory/v1/task/{task_id}"

    payload={}

    headers = {
        'Authorization': f"JWT {token}"
    }

    response = requests.request("GET", url, headers=headers, data=payload)
 
    task_name = response.json()['name']
    print(task_name)

    task_description = response.json()['description']
    print(task_description)

    if response.json()['created_by'] is not None:
        if response.json()['created_by'].get('name') is not None:
            created_by = response.json()['created_by']['name']
        elif response.json()['created_by'].get('full_name') is not None:
            created_by = response.json()['created_by']['full_name']
        else:
            created_by = 'Admin'
    else:
        created_by = 'Admin'
    print(created_by)

    print('Sending ticket details to Slack')
    schedule_message(slack_channel, task_id, due_date, post_at, task_name, created_by, task_description)
    
# method to schedule a message to be sent to slack
def schedule_message(slack_channel, task_id, due_date, post_at, task_name, created_by, task_description):

    if slack_channel == 'C05JG0B01EZ':
        message = f"{task_description}"
    else:
        message = f"{task_description}\n<!channel>"

    url = 'https://slack.com/api/chat.scheduleMessage'

    headers = {
        # declare the charset to avoid errors
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {slack_token}',
    }

    payload = {
        "channel": slack_channel,
        "post_at": post_at,
        "color": "f37052",
        "text": f"`{task_name}` at {home} - Ticket: {task_id} ",
        "attachments": json.dumps([
            {    
                "color": "f37052",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{message}"
                        },
                        "accessory": {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Task",
                                "emoji": True
                            },
                            "value": "view_task",
                            "url": f"https://app.breezeway.io/task/{task_id}",
                            "action_id": "button-action"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "image",
                                "image_url": "https://avatars.slack-edge.com/2023-06-20/5443516728647_007c76049210f5681980_96.png",
                                "alt_text": "cute cat"
                            },
                            {
                                "type": "plain_text",
                                "text": f"task Created by: {created_by}",
                                "emoji": True
                            }
                        ]
                    }
                ]
            }
    ])
}

    try:
        print('Scheduling')
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        print(response.json()['ok'])
    except Exception as e:
        print(e)

    task_scheduled(slack_channel, task_id, due_date)

def task_scheduled(slack_channel, task_id, due_date):
    url = 'https://slack.com/api/chat.postMessage'

    headers = {
        # declare the charset to avoid errors
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {slack_token}',
    }

    task_url = f"https://app.breezeway.io/task/{task_id}"
    payload = {
        "channel": slack_channel,
        "text": f"<{task_url}|Breezeway Task: {task_id}> has been scheduled for {due_date}"
    }

    json_payload = json.dumps(payload)

    try:
        response = requests.request("POST", url, headers=headers, data=json_payload)
        print(response.json()['ok'])
        print('Message posted')
    except Exception as e:
        print(e)

def post_supplies(task_id):

    # search the inventory slack for the task id
    channel = 'C0LECN2SY'

    url = 'https://slack.com/api/conversations.history'

    headers = {'Content-Type': 'application/json; charset=utf-8','Authorization': f"Bearer {slack_token}"}

    payload = {"channel": channel,"limit": 200}

    json_payload = json.dumps(payload)

    response = requests.request("POST", url, headers=headers, data=json_payload)


    # parse the response to get the message id

    body = json.loads(response.text)

    message_id = None

    for message in body['messages']:
        if f"{task_id}" in message['text']:
            message_id = message['ts']
            print(message_id)

    # Add validation to ensure that is message_id is not None, then to no post the comment
    if message_id is not None:
        url = 'https://slack.com/api/chat.update'

    # start to build the message
        body = json.loads(raw_body[0])
        supplies = body['task']['supplies']
        task_id = body['task']['id']

        home = body['task']['home']['name']

        if body['task']['finished_by'] is not None:
            finished_by = body['task']['finished_by']['full_name']
        else:
            finished_by = 'Admin'

        task_url = f"https://app.breezeway.io/task/{task_id}"
    

        total_cost = 0

        item_list = {}

        block = [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Supplies Expense Report:\n*<{task_url}|Work Order# {task_id}>*\nFinished By: {finished_by}\n*Property:* {home}"
                    }
                },{
                    "type": "divider"
                }]


        for supply in supplies:
            supply_name = supply['name']
            supply_cost = supply['unit_cost']
            supply_quantity = supply['quantity']

            supply_total = supply_cost * supply_quantity
            total_cost = total_cost + supply_total
            item_info = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Item:* {supply_name}\nQty: {supply_quantity}\nCost: ${supply_total}"
                    }
                }
            block.append(item_info)
            block.append({"type": "divider"})


        block.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Total Cost:* ${total_cost}"
                    }
                })

        if total_cost > 0:


            headers = {
                # declare the charset to avoid errors
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': f'Bearer {slack_token}',
            }

            payload = {
                "channel": channel,
                "color": "f37052",
                "ts": message_id,
                "blocks": block
            }

            results = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    else:
        
        # start to build the message
        body = json.loads(raw_body[0])
        supplies = body['task']['supplies']
        task_id = body['task']['id']

        home = body['task']['home']['name']
        if body['task']['finished_by'] is not None:
            finished_by = body['task']['finished_by']['full_name']
        else:
            finished_by = 'Admin'

        task_url = f"https://app.breezeway.io/task/{task_id}"
    

        total_cost = 0

        item_list = {}

        block = [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Supplies Expense Report:\n*<{task_url}|Work Order# {task_id}>*\nFinished By: {finished_by}\n*Property:* {home}"
                    }
                },{
                    "type": "divider"
                }]


        for supply in supplies:
            supply_name = supply['name']
            supply_cost = supply['unit_cost']
            supply_quantity = supply['quantity']

            supply_total = supply_cost * supply_quantity
            total_cost = total_cost + supply_total
            item_info = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Item:* {supply_name}\nQty: {supply_quantity}\nCost: ${supply_total}"
                    }
                }
            block.append(item_info)
            block.append({"type": "divider"})


        block.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Total Cost:* ${total_cost}"
                    }
                })

        if total_cost > 0:

            # get the report, and save it as a pdf
            url = 'https://slack.com/api/chat.postMessage'

            headers = {
                # declare the charset to avoid errors
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': f'Bearer {slack_token}',
            }

            payload = {
                "channel": channel,
                "color": "f37052",
                "blocks": block
            }

            results = requests.request("POST", url, headers=headers, data=json.dumps(payload))

            ts = results.json()['ts']

            photos_present = 0

            if body['task']['photos'] is not None:
                for pic in body['task']['photos']:
                    photos_present += 1
                    photo_comment = f'Here is image {photos_present}:'

                    print('posting the new photo')

                    # use the message id to post the task description
                    url = 'https://slack.com/api/files.upload'
                    
                    wo_pic = requests.get(pic)
                    file_data = wo_pic.content

                    headers = {
                        'Authorization': f"Bearer {slack_token}"
                    }

                    payload = {
                        'channels': channel,
                        'thread_ts': ts,
                        'initial_comment': photo_comment,
                        'title': "Image"
                    }

                    requests.post(url, data=payload, headers=headers, files={'file': file_data})

            else:
                print("No photos")
        else:
            print("No supplies")

def update_post_status(slack_channel, slack_token, message_id, updated_status, task_id, assigned_to, color):
    client_id = ''
    client_secret = ''
    url = 'https://api.breezeway.io'

    # get the token
    url_for_token = f"{url}/public/auth/v1/"

    payload = json.dumps({"client_id": client_id, "client_secret": client_secret})
    headers = {'Content-Type': 'application/json'}

    response = requests.request("POST", url_for_token, headers=headers, data=payload)

    if response.status_code != 200:
        sys.exit(1)
    else:
        print("Token received")

    token = response.json()['access_token']

    # get the task details
    url = f"{url}/public/inventory/v1/task/{task_id}"

    payload={}

    headers = {'Authorization': f"JWT {token}"}

    response = requests.request("GET", url, headers=headers, data=payload)

    task_name = response.json()['name']
    task_description = response.json()['description']

    url = 'https://slack.com/api/chat.update'

    headers = {
        # declare the charset to avoid errors
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {slack_token}',
    }
    
    if updated_status == 'finished':
        text = ''
    else:
        text = f"Ticket: {task_id}"

    payload = {
        "channel": slack_channel,
        "color": color,
        "text": text,
        "ts": message_id,
        "attachments": [{    
            "color": color,
			"blocks": [
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"`{task_name}` *Location: {home}* - {task_description}"
					},
                    "accessory": {
						"type": "button",
						"text": {
							"type": "plain_text",
							"text": "View Task",
							"emoji": True
						},
						"value": "view_task",
						"url": f"https://app.breezeway.io/task/{task_id}",
						"action_id": "button-action"
					}
				},
				{
					"type": "context",
					"elements": [
						{
							"type": "image",
							"image_url": "https://avatars.slack-edge.com/2023-06-20/5443516728647_007c76049210f5681980_96.png",
							"alt_text": "cute cat"
						},
						{
							"type": "plain_text",
							"text": f"Task {updated_status} by: {assigned_to}.",
							"emoji": True
						}
					]
				}
			]
		}]
    }

    json_payload = json.dumps(payload)

    response = requests.request("POST", url, headers=headers, data=json_payload)

    print(response.text.encode('utf8'))

def new_ticket(task_id):
    
    # get the token from Breezeway
    # declare auth variables
    client_id = ''
    client_secret = ''
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
        sys.exit(1)
    else:
        print("Token received")

    token = response.json()['access_token']

    # get the task details
    url = f"{url}/public/inventory/v1/task/{task_id}"

    payload={}

    headers = {
        'Authorization': f"JWT {token}"
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.json())

    # parse task id payload details
    body = json.loads(response.text)
    print(body)

    task_name = response.json()['name']
    print(task_name)

    task_description = response.json()['description']
    print(task_description)

    if response.json()['created_by'] is not None:
        if response.json()['created_by'].get('name') is not None:
            created_by = response.json()['created_by']['name']
        elif response.json()['created_by'].get('full_name') is not None:
            created_by = response.json()['created_by']['full_name']
        else:
            created_by = 'Admin'
    else:
        created_by = 'Admin'
    print(created_by)

    print('Sending ticket details to Slack')

    url = 'https://slack.com/api/chat.postMessage'

    headers = {
        # declare the charset to avoid errors
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {slack_token}',
    }

    if slack_channel == 'C05JG0B01EZ':
        message = f"{task_description}"
    else:
        message = f"{task_description}\n<!channel>"

    payload = {
    "channel": slack_channel,
    "color": "f37052",
    "text": f"`{task_name}` at {home} - Ticket: {task_id} ",
    "attachments": json.dumps([
        {    
            "color": "f37052",
			"blocks": [
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"{message}"
					},
                    "accessory": {
						"type": "button",
						"text": {
							"type": "plain_text",
							"text": "View Task",
							"emoji": True
						},
						"value": "view_task",
						"url": f"https://app.breezeway.io/task/{task_id}",
						"action_id": "button-action"
					}
				},
				{
					"type": "context",
					"elements": [
						{
							"type": "image",
							"image_url": "https://avatars.slack-edge.com/2023-06-20/5443516728647_007c76049210f5681980_96.png",
							"alt_text": "cute cat"
						},
						{
							"type": "plain_text",
							"text": f"task Created by: {created_by}",
							"emoji": True
						}
					]
				}
			]
		}
    ])
}

    json_payload = json.dumps(payload)

    response = requests.request("POST", url, headers=headers, data=json_payload)


    body = json.loads(raw_body[0])

    if body['task']['photos']:
        print('New photos found')
        update_ticket_photo(task_id)
    else:
        print('No photo found')

    if response.ok != True:
        print("Error posting message")
        print(response.text)
        sys.exit(1)
    else:
        print("Message posted")
        print(response.text)

 
# dedicated function to update the ticket comment
def update_ticket_comment(task_id, comment, commented_by):
    
    # search for the message id in the channel for a post that contains the task id
    url = 'https://slack.com/api/conversations.history'

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f"Bearer {slack_token}"
    }
    payload = {
        "channel": slack_channel,
        "limit": 200
    }

    json_payload = json.dumps(payload)

    response = requests.request("POST", url, headers=headers, data=json_payload)

    if response.status_code != 200:
        print("Error getting message")
        print(response.text)
        sys.exit(1)
    # parse the response to get the message id

    body = json.loads(response.text)

    message_id = None

    for message in body['messages']:
        if f"Ticket: {task_id}" in message['text']:
            message_id = message['ts']
            print(message_id)
    
    # Add validation to ensure that is message_id is not None, then to no post the comment
    if message_id is not None:

        print('Initial message found, posting comment...')
        # use the message id to post the task description
        url = 'https://slack.com/api/chat.postMessage'
        
        payload = {
            "channel": slack_channel,
            "thread_ts": message_id,
            "text": f"{commented_by} said: '{comment}'"
        }

        json_payload = json.dumps(payload)

        response = requests.request("POST", url, headers=headers, data=json_payload)

        if response.status_code != 200:
            print(response.text)
    else:
        print('No message id found')
        
def update_ticket_photo(task_id):
        # search for the message id in the channel for a post that contains the task id
    url = 'https://slack.com/api/conversations.history'

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f"Bearer {slack_token}"
    }
    payload = {
        "channel": slack_channel,
        "limit": 200
    }

    json_payload = json.dumps(payload)

    response = requests.request("POST", url, headers=headers, data=json_payload)

    if response.status_code != 200:
        print("Error getting message")
        print(response.text)
        sys.exit(1)
    # parse the response to get the message id

    original_post = json.loads(response.text)

    message_id = None

    for message in original_post['messages']:
        if f"Ticket: {task_id}" in message['text']:
            message_id = message['ts']
            print(message_id)
    
    # Add validation to ensure that is message_id is not None, then to no post the comment
    if message_id is not None:

        print('Initial message found, posting photo...')
        
        print('Ensuring the photo does not already exist in the thread...')
        url = 'https://slack.com/api/conversations.replies'

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer ' + slack_token
        }

        data = {
            'channel': slack_channel,
            'ts': message_id
        }

        response = requests.get(url, headers=headers, params=data)

        replies = []
        for message in response.json()['messages']:
            replies.append(message['text'])

        print(replies)

        photos_present = 0

        # create a list of, and then print all of the photos in the task section
        photos = []
        print('Checking for photos...')
        


                # iterate through each task in body
        for pic in body['task']['photos']:
            # iterate through each photo in the task
            print(pic)
            photos_present += 1
            photo_comment = f'Here is image {photos_present}:'


            if photo_comment not in replies:

                print('posting the new photo')

                # use the message id to post the task description
                url = 'https://slack.com/api/files.upload'
                
                wo_pic = requests.get(pic)
                file_data = wo_pic.content

                headers = {
                    'Authorization': f"Bearer {slack_token}"
                }

                payload = {
                    'channels': slack_channel,
                    'thread_ts': message_id,
                    'initial_comment': photo_comment,
                    'title': "Image"
                }

                response = requests.post(url, data=payload, headers=headers, files={'file': file_data})

                # Check if the request was successful
                if response.status_code == 200 and response.json().get('ok'):
                    print(f"{print} posted")
                else:
                    print('Failed to post image to Slack. Error:', response.json().get('error'))
            else:
                print('No photos to post')

        print(photos_present)
    else:
        print('No message id found')
# update the post with the task being started
def update_ticket_started(task_id, started_by):

        # search for the message id in the channel for a post that contains the task id
    url = 'https://slack.com/api/conversations.history'

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f"Bearer {slack_token}"
    }
    payload = {
        "channel": slack_channel,
        "limit": 200
    }

    json_payload = json.dumps(payload)

    response = requests.request("POST", url, headers=headers, data=json_payload)

    if response.status_code != 200:
        print("Error getting message")
        print(response.text)
        sys.exit(1)
    # parse the response to get the message id

    body = json.loads(response.text)

    message_id = None

    for message in body['messages']:
        if f"Ticket: {task_id}" in message['text']:
            message_id = message['ts']
            print(message_id)
    
    # Add validation to ensure that is message_id is not None, then to no post the comment
    if message_id is not None:

        print('Initial message found, notifying that the task has been started...')
        # use the message id to post the task description
        url = 'https://slack.com/api/chat.postMessage'
        
        payload = {
            "channel": slack_channel,
            "thread_ts": message_id,
            "text": f"This task has been started by {started_by}"
        }

        json_payload = json.dumps(payload)

        response = requests.request("POST", url, headers=headers, data=json_payload)

        if response.status_code != 200:
            print(response.text)

        update_post_status(slack_channel, slack_token, message_id, 'started', task_id, started_by, 'FFFF00')
    else:
        print('No message id found')

def finish_task(task_id, finished_by):
    url = 'https://slack.com/api/conversations.history'

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f"Bearer {slack_token}"
    }
    payload = {
        "channel": slack_channel,
        "limit": 200
    }

    json_payload = json.dumps(payload)

    response = requests.request("POST", url, headers=headers, data=json_payload)

    if response.status_code != 200:
        print("Error getting message")
        print(response.text)
        sys.exit(1)
    # parse the response to get the message id

    body = json.loads(response.text)

    message_id = None

    for message in body['messages']:
        if f"Ticket: {task_id}" in message['text']:
            message_id = message['ts']
            print(message_id)
    
    # Add validation to ensure that is message_id is not None, then to no post the comment
    if message_id is not None:

        print('Initial message found, searching for a Finished comment...')
        
        url = 'https://slack.com/api/conversations.replies'

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer ' + slack_token
        }

        data = {
            'channel': slack_channel,
            'ts': message_id
        }

        response = requests.get(url, headers=headers, params=data)

        post_finished_status = False
        for message in response.json()['messages']:
            if 'This task has been finished by' not in message['text']:
                post_finished_status = True
            else:
                post_finished_status = False
        print(post_finished_status)
        if post_finished_status:
            url = 'https://slack.com/api/chat.postMessage'

            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': f"Bearer {slack_token}"
            }
        
            payload = {
                "channel": slack_channel,
                "thread_ts": message_id,
                "text": f"This task has been finished by: {finished_by}"
            }

            json_payload = json.dumps(payload)

            print(json_payload)

            response = requests.request("POST", url, headers=headers, data=json_payload)

            if response.ok is not True:
                print(response.text)
            else:
                print('Finished comment posted')
                print(response.json())
            
            update_post_status(slack_channel, slack_token, message_id, 'finished', task_id, finished_by, '008000')

            print(response.text)
            body = json.loads(raw_body[0])

        else:
            print('No finished comment to post')

hk_triage = False
if body['task']['template'] is None:
    hk_triage = True
hk_triage

long_term = False
if body['task']['template'] is not None:
    if body['task']['template'].get('id') == 28144:
        long_term = True
    else:
        long_term = False

if created_by == 'Breezeway Assist':
    slack_channel = 'C0LB0GGQN'
elif department == 'Maintenance' and priority == 'Urgent':
    slack_channel = 'C99PLPRMJ'
elif department == 'Cleaning' and priority == 'Urgent':
    slack_channel = 'C60740ZSM'
elif long_term == True:
    slack_channel = 'C1GU9NRC2'
elif department == 'Maintenance' and priority != 'Urgent':
    slack_channel = 'C053BRFUB97'
elif department == 'Cleaning' and priority == 'Low' and hk_triage == True:
    slack_channel = 'C0LEK3G7R'
elif department == 'Cleaning' and priority != 'Urgent' and hk_triage == True:
    slack_channel = 'C8YQ7Q2J1'
elif department == 'Cleaning' and priority != 'Urgent' and hk_triage == False:
    slack_channel = 'C05JG0B01EZ'
else:
    quit()

print(f'Slack channel: {slack_channel} and the Department is {department} and the priority is {priority}')

utc_now = datetime.datetime.utcnow()
today = (utc_now - datetime.timedelta(hours=8)).date()
print(today)

# 7am pacific time
schedule_time = datetime.time(8, 0, 0)
print(schedule_time)

if date is not None:
    due_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    print(due_date)

    # convert due_date to EPOCH time
    post_at = datetime.datetime.combine(due_date, schedule_time).strftime('%s')
    print(post_at)


# Start assessing the task, if status is task-created, run new_ticket()
if status == 'task-created' and department != 'Inspection':

    if date is None or due_date == today:
        print('New ticket will be created...')
        new_ticket(task_id)
    else:
        print("Today is not the due date")
        get_task_details(task_id)

elif status == 'task-comment-updated' and department != 'Inspection':
    if body['task']['comments']:
        comment = body['task']['comments'][-1]['comment']
        commented_by = body['task']['comments'][-1]['comment_by'] if 'comment_by' in body['task']['comments'][-1] else 'Admin'
        print(f'New comment: {comment}')
        update_ticket_comment(task_id, comment, commented_by)
    else:
        print('No comment found') 


elif status == 'task-updated'and department != 'Inspection':
    print('Ticket will be updated with photos if theyre available...')

    if due_date > today: # or due_date > today:

        print("Today is not the due date")
        reschedule_message(slack_channel, task_id, due_date, post_at) 
    else:
        print("Today is the due date")
        print('Ticket will be updated with photos if theyre available...')

        # if a photo is added to the task, get the photo and post it to Slack
        if body['task']['photos']:
            print('New photos found')
            update_ticket_photo(task_id)
        else:
            print('No photo found')

        if body['task']['finished_at']:
            if body['task']['finished_by']:
                finished_by = body['task']['finished_by']['full_name']
            else:
                finished_by = 'Admin'
            finish_task(task_id, finished_by)
        else:
            print('This was not an update for a Maintenance or Cleaning Urgent task')

        if body['task']['supplies'] is not None:
            print("supplies")
            post_supplies(task_id)
        else:
            print("no supplies")

elif status == 'task-started' and department != 'Inspection':
    print('Ticket will be updated with the user who started the task...')

    started_by = body['task']['started_by']['full_name']
    print(f'Task started by: {started_by}')
    update_ticket_started(task_id, started_by)

elif status == 'task-supply-updated' and department != 'Inspection':
    print("Task supply updated")
    post_supplies(task_id)

else:
    print('No work to do')