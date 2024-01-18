import requests
import json
import os

approval_notice = input_data['approval_notice']

# For DEV
#approval_notice = open('approval.txt', 'r').read()

print(approval_notice)

# declare variables
slack_token = ""
channel = 'C0LB0GGQN'
post_url = 'https://slack.com/api/chat.postMessage'
text = 'Hey <!subteam^S05UL6NUWNS>!'

approval_body = approval_notice.splitlines()

line_1 = f"We've {approval_body[1].split('Beachfront Only has ')[1]}"

text = text + '\n' + line_1 + '\n' + "Please make the necessary revisions in Track to reflect the charges."

# payload headers
headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Authorization': f"Bearer {slack_token}"
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

print(text)


json_payload = json.dumps(payload)

response = requests.request("POST", post_url, headers=headers, data=json_payload)
print(response.text)


