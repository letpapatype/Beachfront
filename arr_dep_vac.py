import pymysql
from sshtunnel import SSHTunnelForwarder
import datetime
import os
import pandas as pd
from slack_sdk import WebClient

# Slack bot configuration
slack_bot_token = os.environ['SLACK_BOT_TOKEN']
slack_client = WebClient(token=slack_bot_token)

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

# recycled property key list for properties
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
property_keys = list(properties.keys())
print(property_keys)

empty_units = []
same_day_turnover = []

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

        print("Connected to MySQL server. Now executing SQL commands...\nGathering arrival data...")

        # get tomorrows date in YYYY-MM-DD format
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        

        today = datetime.date.today().strftime("%Y-%m-%d")


        # Execute SQL query
        sql = f"""
        SELECT
            u.unit_code,
            DATE_FORMAT(CONVERT_TZ(r.checkin_time, '+00:00', '-07:00'), '%H:%i:%s') AS checkin_time
        FROM
            reservation r
            INNER JOIN units u ON u.id = r.cabin_id
        WHERE
            r.status LIKE '%Confirmed%'
            AND r.checkin_date LIKE '%{today}%'
        """

        
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        print("Successfully executed query...")

        """
        Set up the dataframe with the results from the SQL query
        """

        arrival_results = pd.DataFrame(rows, columns=['unit_code', 'checkin_time'])
        print("Today's arrivals:")
        print(arrival_results)

        print("Starting departure query...")
        # Execute SQL query
        sql = f"""
        SELECT
            u.unit_code,
            DATE_FORMAT(CONVERT_TZ(r.checkout_time, '+00:00', '-07:00'), '%H:%i:%s') AS checkout_time
        FROM
            reservation r
            INNER JOIN units u ON u.id = r.cabin_id
        WHERE
            r.status LIKE '%Checked In%'
            AND r.checkout_date LIKE '%{today}%'
        """

        # Run
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()

        print("Successfully executed query...")

        departure_results = pd.DataFrame(rows, columns=['unit_code', 'checkout_time'])
        print("Today's departures:")
        print(departure_results)

        print("Closing connection...")
        connection.close()

        print("Units not in arrival or departure results:")
        for unit in property_keys:
            if unit not in arrival_results['unit_code'].values and unit not in departure_results['unit_code'].values:
                #print(f"Unit {unit} is not in the arrival or departure results. Removing from properties list...")
                empty_units.append(unit)
        print(empty_units)

        print("Units with arrival and departure today:")

        
        for unit in property_keys:
            if unit in arrival_results['unit_code'].values and unit in departure_results['unit_code'].values:
                print(f"{unit}")
                same_day_turnover.append(unit)


except Exception as e:
    print(f"An error occurred: {str(e)}")


arrival_text = ""
arrival_units_list_C = "Carlsbad:\n"
arrival_units_list_E = "Encinitas:\n"
arrival_units_list_P = "Pacific Street:\n"
arrival_units_list_S = "Strand:\n"

for index, row in arrival_results.iterrows():

    if row['unit_code'].startswith('C'):
        arrival_units_list_C += f"{row['unit_code']} - {row['checkin_time']}\n"
    elif row['unit_code'].startswith('E'):
        arrival_units_list_E += f"{row['unit_code']} - {row['checkin_time']}\n"
    elif row['unit_code'].startswith('P'):
        arrival_units_list_P += f"{row['unit_code']} - {row['checkin_time']}\n"
    elif row['unit_code'].startswith('S'):
        arrival_units_list_S += f"{row['unit_code']} - {row['checkin_time']}\n"
    #arrival_text += f"{row['unit_code']} - {row['checkin_time']}\n"

arrival_block = {
    "type": "section",
    "text": {
        "type": "mrkdwn",
        "text": f"*Today's Arrivals:*\n{arrival_units_list_C}\n{arrival_units_list_E}\n{arrival_units_list_P}\n{arrival_units_list_S}"
    }
}

departure_text = ""

departure_units_list_C = "Carlsbad:\n"
departure_units_list_E = "Encinitas:\n"
departure_units_list_P = "Pacific Street:\n"
departure_units_list_S = "Strand:\n"

for index, row in departure_results.iterrows():

    if row['unit_code'].startswith('C'):
        departure_units_list_C += f"{row['unit_code']} - {row['checkout_time']}\n"
    elif row['unit_code'].startswith('E'):
        departure_units_list_E += f"{row['unit_code']} - {row['checkout_time']}\n"
    elif row['unit_code'].startswith('P'):
        departure_units_list_P += f"{row['unit_code']} - {row['checkout_time']}\n"
    elif row['unit_code'].startswith('S'):
        departure_units_list_S += f"{row['unit_code']} - {row['checkout_time']}\n"


    # departure_text += f"{row['unit_code']} - {row['checkout_time']}\n"

departure_block = {
    "type": "section",
    "text": {
        "type": "mrkdwn",
        "text": f"*Today's Departures:*\n{departure_units_list_C}\n{departure_units_list_E}\n{departure_units_list_P}\n{departure_units_list_S}"
    }
}

same_day_turnover_text = ""
same_day_units_list_C = "Carlsbad:\n"
same_day_units_list_E = "Encinitas:\n"
same_day_units_list_P = "Pacific Street:\n"
same_day_units_list_S = "Strand:\n"

for unit in same_day_turnover:

    if unit.startswith('C'):
        same_day_units_list_C += f"{unit}\n"
    elif unit.startswith('E'):
        same_day_units_list_E += f"{unit}\n"
    elif unit.startswith('P'):
        same_day_units_list_P += f"{unit}\n"
    elif unit.startswith('S'):
        same_day_units_list_S += f"{unit}\n"


    # same_day_turnover_text += f"{unit}\n"

same_day_turnover_block = {
    "type": "section",
    "text": {
        "type": "mrkdwn",
        "text": f"*Same Day Turnovers (If Applicable):*\n{same_day_units_list_C}\n{same_day_units_list_E}\n{same_day_units_list_P}\n{same_day_units_list_S}"
    }
}

empty_units_list_C = "Carlsbad:\n"
empty_units_list_E = "Encinitas:\n"
empty_units_list_P = "Pacific Street:\n"
empty_units_list_S = "Strand:\n"

for unit in empty_units:

    if unit.startswith('C'):
        empty_units_list_C += f"{unit}\n"
    elif unit.startswith('E'):
        empty_units_list_E += f"{unit}\n"
    elif unit.startswith('P'):
        empty_units_list_P += f"{unit}\n"
    elif unit.startswith('S'):
        empty_units_list_S += f"{unit}\n"

empty_units_block = {
    "type": "section",
    "text": {
        "type": "mrkdwn",
        "text": f"{empty_units_list_C}\n{empty_units_list_E}\n{empty_units_list_P}\n{empty_units_list_S}"
    }
}

# convert today to MM/DD
today = datetime.date.today().strftime("%m/%d")

print("Sending Slack message...")
arrival_departure_post = slack_client.chat_postMessage(
    channel='C0V03NUFN',
    blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Arrivals and Departures* for {today}",
                "verbatim": True
            }
        },
        {
            "type": "divider"
        },
        arrival_block,
        {
            "type": "divider"
        },
        departure_block,
        {
            "type": "divider"
        },
        same_day_turnover_block     
    ]
)

assert arrival_departure_post["ok"]

print("Sending Departure message to #Housemen...")
hk_departure_post = slack_client.chat_postMessage(
    channel='C0LECM2EQ',
    blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Departures* for {today}",
                "verbatim": True
            }
        },
        {
            "type": "divider"
        },
        departure_block,
        {
            "type": "divider"
        },
        same_day_turnover_block     
    ]
)

assert hk_departure_post["ok"]

# vacant_unit_post = slack_client.chat_postMessage(
#     channel='C04L2BBBYJH',
#     blocks=[
#         {
#             "type": "section",
#             "text": {
#                 "type": "mrkdwn",
#                 "text": f"*Vacant Unit Report* for {today}",
#                 "verbatim": True
#             }
#         },
#         {
#             "type": "divider"
#         },
#         empty_units_block        
#     ]
# )

# assert vacant_unit_post["ok"]
