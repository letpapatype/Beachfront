import pymysql
from sshtunnel import SSHTunnelForwarder
import datetime
import os
import pandas as pd
import json
import requests
import sys


# def get_credentials():
#     """
#     Get credentials from AWS Secrets Manager
#     """

#     parameters = []
#     return parameters




def get_reservation(unit, check_date, in_or_out):
    # TODO: Convert to digesting secrects from AWS Secrets Manager
    # SSH tunnel configuration
    ssh_host = os.environ['SSH_HOST']
    ssh_port = 8022
    ssh_username = 'beachfrontvr-bi'
    

    # MySQL server configuration
    mysql_host = os.environ['MYSQL_HOST']
    mysql_port = 3306
    mysql_username = 'beachfrontvr-bi'
    mysql_password = os.environ['MYSQL_PASSWORD']
    mysql_database = os.environ['MYSQL_DATABASE']

    # take env var SSH_PEM_KEY and write it to a file named beachfrontvr.pem
    with open('beachfrontvr.pem', 'w') as f:
        f.write(os.environ['SSH_PEM_KEY'])
    ssh_pem_key = './beachfrontvr.pem'


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

            if in_or_out == 'in':
                in_or_out = 'r.checkin_date'
            elif in_or_out == 'out':
                in_or_out = 'r.checkout_date'
            # Execute SQL query
            sql = f"""
            SELECT
                r.id,
                r.checkin_date,
                r.checkout_date,
                c.first_name,
                c.last_name,
                u.unit_code
            FROM
                reservation r
                INNER JOIN customer c ON c.id = r.customer_id
                INNER JOIN unit_code uc ON uc.unit_id = r.cabin_id
                INNER JOIN units u ON u.id = r.cabin_id
            WHERE
                {in_or_out} LIKE '%{check_date}%'
                AND u.unit_code LIKE '%{unit}%'
            """

            # Execute a sample query
            cursor = connection.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            print("Successfully executed query...")

            """
            Set up the dataframe with the results from the SQL query
            """

            structured_results = pd.DataFrame(rows, columns=['reservation_id', 'checkin_date', 'checkout_date', 'first_name', 'last_name', 'unit_code'])

            unit = structured_results['unit_code'][0]
            reservation = structured_results['reservation_id'][0]

            track_url = f"https://bovr.trackhs.com/pms/reservations/view/{reservation}"

            return unit, reservation, track_url

    except Exception as e:
        print(f"An error occurred: {str(e)}")

# def main():
#     parameters = get_credentials()
#     unit, reservation, track_url = get_reservation('B1', '2021-07-01', 'in', parameters)
#     return unit, reservation, track_url