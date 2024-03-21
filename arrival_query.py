import pymysql
from sshtunnel import SSHTunnelForwarder
import datetime
import os
import pandas as pd
import json
import requests
import sys

# SSH tunnel configuration
ssh_host = os.environ['SSH_HOST']
ssh_port = 8022
ssh_username = 'beachfrontvr-bi'
ssh_pem_key = 'beachfrontvr.pem'

# MySQL server configuration
mysql_host = os.environ['MYSQL_HOST']
mysql_port = 3306
mysql_username = 'beachfrontvr-bi'
mysql_password = os.environ['MYSQL_PASSWORD']
mysql_database = os.environ['MYSQL_DATABASE']

ref_id = ''

# Declare dictionary to associate unit codes with Breezeway IDs
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

def get_property_tasks(ref_id):

    # Breezeway base URL
    brzw_url = 'https://api.breezeway.io'

    # get the token from Breezeway
    # declare auth variables
    client_id = os.environ['BRZW_CLIENT_ID']
    client_secret = os.environ['BRZW_CLIENT_SECRET']

    # get the token
    url_for_token = f"{brzw_url}/public/auth/v1/"

    payload = json.dumps({
    "client_id": client_id,
    "client_secret": client_secret
    })
    headers = {
    'Content-Type': 'application/json'
    }

    token_response = requests.request("POST", url_for_token, headers=headers, data=payload)

    if token_response.status_code != 200:
        print("Error getting token")
        print(token_response.text)
        sys.exit(1)



    token = token_response.json()['access_token']

    get_task_url = f"{brzw_url}/public/inventory/v1/task/?reference_property_id={ref_id}"

    today = datetime.date.today()

    """
    In Dev:
    get tomorrows date in YYYY-MM-DD format
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    """

    payload={
        'limit': 100,
        'scheduled_date': f'{today},{today}'
    }


    headers = {
        'Authorization': f"JWT {token}"
    }


    get_tasks_response = requests.request("GET", get_task_url, headers=headers, params=payload)

    for tasks in get_tasks_response.json()['results']:
        if 'Meet and Greet' in tasks['name']:
            print(f"Task Name: {tasks['name']}")
            if tasks['assignments']:
                assigned_to = tasks['assignments'][0]['name']
                return assigned_to
        else:
            assigned_to = 'Not Scheduled'
            return assigned_to

    
def post_meet_and_greet(arrivals):

    mng_channel = 'CLXLM8X6J'

    url = 'https://slack.com/api/chat.postMessage'

    slack_token = os.environ['SLACK_BOT_TOKEN']

    headers = {
        # declare the charset to avoid errors
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {slack_token}',
    }

    arrival_data = {
        "channel": mng_channel,
        "blocks": [		
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Today's Arrivals (Schedule accordingly):",
                    "emoji": True
                }
		    },
            {
                "type": "divider"
            }

        ]
    }

    for index, row in arrivals.iterrows():

        if row['unit_code'] in properties:
            ref_id = properties[row['unit_code']]

        arrival = {
			"type": "section",
            "block_id": f"{ref_id}",
			"text": {
                "type": "mrkdwn",
                "text": f"<https://bovr.trackhs.com/pms/reservations/view/{row['reservation_id']}|*Reservation {row['reservation_id']}:*> {row['first_name']} {row['last_name']}\n*Property:* {row['unit_code']}\n*Early Checkin:* {row['ECI']}\n*Code:* {row['code']}"
            },
            "accessory": {
                "type": "button",
                "action_id": "schedule_meet_and_greet",
                "text": {
                    "type": "plain_text",
                    "text": "Schedule",
                    "emoji": True
                },
                "value": f"{row['unit_code']}_{ref_id}_{row['code']}",
            }
		}

        arrival_data['blocks'].append(arrival)

    print(arrival_data)
    
    # export arrival to json
    """    
    Dev:
    with open('arrival_data.json', 'w') as outfile:
        json.dump(arrival_data, outfile)
        
    """

    response = requests.request("POST", url, headers=headers, data=json.dumps(arrival_data))
    print(response.text)
    



try:
    # Set up the SSH tunnel
    with SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_username,
        ssh_pkey=ssh_pem_key,
        remote_bind_address=(mysql_host, mysql_port)
    ) as tunnel:
        # Connect to the MySQL server through the SSH tunnel
        connection = pymysql.connect(
            host='127.0.0.1',
            port=tunnel.local_bind_port,
            user=mysql_username,
            password=mysql_password,
            database=mysql_database
        )

        print("Connected to MySQL server. Now executing SQL commands...")

        # get tomorrows date in YYYY-MM-DD format
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        

        today = datetime.date.today().strftime("%Y-%m-%d")

        # Execute SQL query
        sql = f"""
        SELECT
            r.id,
            r.checkin_date,
            c.first_name,
            c.last_name,
            u.unit_code,
            DATE_FORMAT(CONVERT_TZ(r.checkin_time, '+00:00', '-07:00'), '%H:%i:%s') AS checkin_time,
            uc.code
        FROM
            reservation r
            INNER JOIN customer c ON c.id = r.customer_id
            INNER JOIN unit_code uc ON uc.unit_id = r.cabin_id
            INNER JOIN units u ON u.id = r.cabin_id
        WHERE
            r.status LIKE '%Confirmed%'
            AND r.checkin_date LIKE '%{today}%'
            AND uc.last_name LIKE c.last_name
            AND uc.first_name LIKE c.first_name
        """

        # Execute a sample query
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        print("Successfully executed query...")

        """
        Set up the dataframe with the results from the SQL query
        """

        structured_results = pd.DataFrame(rows, columns=['reservation_id', 'checkin_date', 'first_name', 'last_name', 'unit_code', 'checkin_time', 'code'])
    
        

        # add a column name ECI, the default value is N, but if checkin_time is before 4pm, then set ECI to Y
        structured_results['ECI'] = 'No'
        structured_results.loc[structured_results['checkin_time'] < '16:00:00', 'ECI'] = 'Yes'

        structured_results['code'] = structured_results['code'].str.extract(r'(\d{6})')

        #Create a column named assigned_to and set the default value to 'Not Assigned', then call the get_property_tasks function to get the assigned_to value
        #structured_results['assigned_to'] = 'Not Assigned'

        for unit in structured_results['unit_code']:
            # find the unit code in the properties dictionary and print the Breezeway ID
            if unit in properties:
                print(f"{unit} Breezeway ID: {properties[unit]}")
                ref_id = properties[unit]
                #assigned_to = get_property_tasks(ref_id)
                # print(f"{unit} Meet and Greet assigned to: {assigned_to}")
                #structured_results.loc[structured_results['unit_code'] == unit, 'assigned_to'] = assigned_to

            else:
                print(f'Unit code {unit} not found in dictionary')

        print("Closing connection...")
        connection.close()

    post_meet_and_greet(structured_results)




except Exception as e:
    print(f"An error occurred: {str(e)}")
