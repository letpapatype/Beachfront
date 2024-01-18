import requests
import json
import os
from datetime import datetime as dt
import re

post = input_data['body']

# For DEV
#post = open('post.txt', 'r').read()

print(post)

# declare variables
slack_token = ""
channel = 'C06CN0WN9AP'
post_url = 'https://slack.com/api/chat.postMessage'
unit = ''
name = ''
request_time = ''
res_dates = ''
check_in = ''
check_out = ''
approval_link = ''
decline_link = ''
portal_link = ''
the_request = ''
text = ''
checkout_time = ''
ok_to_post = False
sales = False


# payload headers
headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Authorization': f"Bearer {slack_token}"
}

# properties dictionary
properties = {
    'C2375-0': 1,
    'C2955-8': 146,
    'C3015-A': 2,
    'C3015-B': 3,
    'E396-0': 8,
    'E950-0': 9,
    'E952-0': 10,
    'E1084-0': 5,
    'E1086-0': 6,
    'E1220-0': 7,
    'P807-1': 145,
    'P807-2': 144,
    'P809-1': 41,
    'P809-2': 42,
    'P809-3': 43,
    'P809-4': 44,
    'P809-5': 45,
    'P809-6': 46,
    'P811-1': 47,
    'P811-2': 48,
    'P811-X': 49,
    'P813-1': 50,
    'P813-2': 51,
    'P813-X': 52,
    'P815-1': 53,
    'P815-2': 54,
    'P815-X': 55,
    'P817-1': 56,
    'P817-2': 57,
    'P817-3': 58,
    'P819-4': 59,
    'P819-5': 60,
    'P819-6': 61,
    'P823-1': 62,
    'P823-2': 63,
    'P823-X': 64,
    'P825-1': 65,
    'P825-2': 66,
    'P825-X': 67,
    'P827-1': 68,
    'P827-2': 69,
    'P827-X': 70,
    'P829-1': 71,
    'P829-2': 72,
    'P829-X': 161,
    'P835-1': 147,
    'P835-2': 148,
    'P835-3': 149,
    'P835-4': 150,
    'P835-5': 151,
    'P835-6': 160,
    'P913-1': 83,
    'P913-2': 84,
    'P917-0': 85,
    'P919-0': 86,
    'P921-0': 87,
    'P923-0': 88,
    'P925-1': 153,
    'P925-2': 154,
    'P925-3': 155,
    'P925-4': 156,
    'P1023-0': 11,
    'P1027-0': 12,
    'P1029-0': 13,
    'P1111-1': 18,
    'P1111-23': 19,
    'P1111-X': 20,
    'P1219-2': 21,
    'P1315-1': 22,
    'P1315-2': 23,
    'P1315-3': 24,
    'P1427-0': 25,
    'P1615-1': 26,
    'P1615-2': 27,
    'P1615-3': 28,
    'P1615-4': 29,
    'P1615-5': 30,
    'P1643-0': 31,
    'P1733-0': 32,
    'P1735-0': 33,
    'P1809-0': 34,
    'P1829-0': 35,
    'P1919-0': 36,
    'P2031-0': 37,
    'Pe-1722': 89,
    'Pe-1722L': 90,
    'Pe-1724': 91,
    'Pe-1724L': 92,
    'S510-A': 93,
    'S510-B': 94,
    'S510-C': 95,
    'S512-B': 96,
    'S700-102': 97,
    'S700-103': 98,
    'S700-104': 99,
    'S700-106': 100,
    'S700-206': 101,
    'S702-1': 102,
    'S702-2': 103,
    'S702-3': 104,
    'S702-4': 105
}


if 'Dog Fee' in post:
    print('Found a Dog Fee Request')

    # print each line in the post
    for line in post.splitlines():
        if 'Unit' in line:
            break_line = line.split(' ')
            unit = break_line[3]
        elif 'request for unit' in line:
            the_request = line.split('request for unit')[0]
        elif 'Guest Name' in line:
            name = line.split(':')[1].strip()
        elif 'Request Date' in line:
            request_time = line.split(':')[1].strip()
        elif 'Reservation Date' in line:
            res_dates = ':'.join(line.split(':')[1:]).strip()

    text = f"Hey <!channel>, dog cleaning has been added to a reservation Dack!\nUnit: {unit}\nName: {name}\nRequest Time: {request_time}\nReservation Dates: {res_dates}"

    ok_to_post = True

elif 'Early' in post or 'Late' in post:
    print('Found an ECI/LCO Request')
    for line in post.splitlines():
        if 'Unit' in line:
            break_line = line.split(' ')
            unit = break_line[3]
            approval_link = break_line[5]
            approval_link = approval_link[1:-1]
            decline_link = break_line[7]
            decline_link = decline_link[1:-1]
            portal_link = break_line[11]
            portal_link = portal_link[1:-1]
        elif 'request for unit' in line:
            the_request = line.split('request for unit')[0]
        elif 'Guest Name' in line:
            name = line.split(':')[1].strip()
        elif 'Request Date' in line:
            request_time = line.split(':')[1].strip()
        elif 'Reservation Date' in line:
            res_dates = ':'.join(line.split(':')[1:]).strip()
    
    ok_to_post = True

    text = f"Hey <!channel>, a new request has came in from Dack!\nRequest: {the_request}\nUnit: {unit}\nName: {name}\nRequest Time: {request_time}\nReservation Dates: {res_dates}\nApproval Link: <{approval_link} | Approve>\nDecline Link: <{decline_link} | Decline>\nPortal Link: <{portal_link} | Portal>"

elif'new reservation request' in post:
    print('Found a New Reservation Request')
    split = post.splitlines()
    res_request = split[2]
    name = split[5] + ' ' + split[6]
    email = split[7]
    phone = split[8]

    notes = split[10:]

    if 'N/A' in notes:
        notes = 'N/A'
    else:
        notes = ' '.join(notes)


    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Phone: {phone}")
    print(f"Notes: {notes}")
    
    sales = True

    # route to sales channel
    channel = 'C0LB0GGQN'

    text = f"Hey <!channel>\n{res_request}\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nDetails: {notes}"
    
else:
    print('Nothing to report, here is the post:')
    print(post)  

if ok_to_post == True:
    print('ok to post')
    print(f'Request: {the_request}')
    print(f'Unit: {unit}')
    print(f'Name: {name}')
    print(f'Request Time: {request_time}')
    print(f'Reservation Dates: {res_dates}')
    print(f'Approval Link: {approval_link}')
    print(f'Decline Link: {decline_link}')
    print(f'Portal Link: {portal_link}')

    if unit in properties:
        property_to_clean = properties[unit]

    checkout_time = res_dates.split(' ')[-2]
    print(f'Dack\'s checkout time: {checkout_time}')

    # take #3 and #4 from the back of the list
    date = re.findall(r"[A-Z][a-z]+ \d{1,2}", res_dates)
    date = date[1] if len(date) > 1 else None

    print(date)
    pretty_date = date
    # convert 'August 3' to '08-03'
    date = dt.strptime(date, '%B %d').strftime('%m-%d')    
    # get the year
    year = dt.now().year

    checkout_date = f'{year}-{date}'
    print(f'Dack\'s checkout date: {checkout_date}')

    up_task_button = {
        "accessory": {
            "type": "button",
            "action_id": "dog_cleaning",
            "text": {
                "type": "plain_text",
                "text": "Schedule",
                "emoji": True
            },
            "value": f"{property_to_clean}_{checkout_time}_{checkout_date}_{unit}_{pretty_date}",
        }
    }

    payload = {
        "channel": channel,
        "blocks": [
            {
                "type": "section",
                "block_id": "dog_cleaning",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            },
        ]
    }

    if 'Dog' in post:
        # append the first object in the blocks list
        payload['blocks'][0].update(up_task_button)


    json_payload = json.dumps(payload)

    response = requests.request("POST", post_url, headers=headers, data=json_payload)
    print(response.text)

    ts = response.json()['ts']

    print('Posting in thread message to Sales team')

    in_thread_payload = {
            "channel": channel,
            "thread_ts": ts,
            "text": "Hey <!subteam^S05UL6NUWNS>, please make the necessary revisions in Track.\n<@U6EJRHJJK>, please schedule accordingly."
    }

    json_in_thread_payload = json.dumps(in_thread_payload)

    in_thread_response = requests.request("POST", post_url, headers=headers, data=json_in_thread_payload)
    print(in_thread_response.json()['ok'])

elif sales == True:
    payload = {
            "channel": channel,
            "blocks": [
                {
                    "type": "section",
                    "block_id": "dog_cleaning",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
                },
        ]

    }


    json_payload = json.dumps(payload)

    response = requests.request("POST", post_url, headers=headers, data=json_payload)
    print(response.text)

else:
    print('Nothing to post')

