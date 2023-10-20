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


        # Execute SQL query
        sql = f"""
        SELECT
            r.id,
            u.unit_code,
            STR_TO_DATE(DATE_FORMAT(r.cancelled_at, '%Y-%m-%d'), '%Y-%m-%d'),
            r.checkin_date,
            r.checkout_date,
            r.rent,
            c.name,
            u.bedrooms,
            # difference in day between checkin_date and cancelled_at
            DATEDIFF(r.checkin_date, r.cancelled_at) AS dtc
        FROM
            reservation r
            INNER JOIN units u ON u.id = r.cabin_id
            INNER JOIN channel c ON c.id = r.channel_id
        WHERE
            r.cancelled_at > DATE_SUB(NOW(), INTERVAL 366 DAY)
            AND r.cancelled_at < DATE_SUB(r.checkin_date, INTERVAL 61 DAY)
        """

        # Execute a sample query
        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        print("Successfully executed cancellation query...")

        """
        Set up the dataframe with the results from the SQL query
        """

        cancellations_results = pd.DataFrame(rows, columns=['res_is', 'unit', 'cancelled_at', 'checkin_date', 'checkout_date', 'rent', 'channel', 'bedrooms', 'dtc'])

        

        cancellations_results.to_csv('cancellations_results.csv', index=False)
        print(cancellations_results)

        reservations_sql = f"""
        SELECT
            r.id,
            u.unit_code,
            STR_TO_DATE(DATE_FORMAT(r.created_at, '%Y-%m-%d'), '%Y-%m-%d'),
            #r.created_at,
            r.checkin_date,
            r.checkout_date,
            r.rent,
            u.bedrooms,
            c.name
        FROM
            reservation r
            INNER JOIN units u ON u.id = r.cabin_id
            INNER JOIN channel c ON c.id = r.channel_id
        WHERE
            # where r.status is not 'Cancelled' or 'Hold', and r.created_at is within the last year
            r.status NOT IN ('Cancelled', 'Hold')
            AND r.created_at > DATE_SUB(NOW(), INTERVAL 366 DAY)
            AND r.owner_revenue > 0.00

        """

        # Execute a sample query
        cursor = connection.cursor()
        cursor.execute(reservations_sql)
        res_rows = cursor.fetchall()
        
        print("Successfully executed reservation query...")

        """
        Set up the dataframe with the results from the SQL query
        """

        current_reservation_results = pd.DataFrame(res_rows, columns=['res_id', 'unit', 'created_at', 'checkin_date', 'checkout_date', 'rent', 'bedrooms', 'channel'])
        current_reservation_results.to_csv('current_reservation_results.csv', index=False)
        print(current_reservation_results)
    print("Information has been gathered.\nClosing connection...")
    connection.close()


    print("Comparing results...")
    comparison_results = pd.DataFrame(columns=['unit', 'bedrooms', 'can_res', 'cancelled_at', 'can_checkin_date', 'can_checkout_date', 'can_rent', 'can_channel', 'new_res', 'new_created_at', 'new_checkin_date', 'new_checkout_date', 'new_rent', 'new_channel', 'diff_rent'])

    # create a dataframe with the unit number, total cancelled reservations, total new reservations and the total difference in rent
    difference_results = pd.DataFrame(columns=['unit', 'total_cancelled_reservations', 'total_new_reservations', 'total_difference_in_rent'])

    # dataframe to tally total cancelled reservations, total rebooked
    total_results = pd.DataFrame(columns=['total_cancelled_reservations', 'total_rebooked_reservations'])
    # set both columns to 0
    total_results.loc[0, 'total_cancelled_reservations'] = 0
    total_results.loc[0, 'total_rebooked_reservations'] = 0

    combo_units = ['P811-X', 'P813-X', 'P815-X', 'P823-X', 'P825-X', 'P827-X', 'P829-X', 'P1111-X']
    combo_results = pd.DataFrame(columns=['unit', 'cancelled_at', 'can_check_in', 'can_checkout', 'can_rent', 'can_channel', 'new_unit', 'new_created_at', 'new_checkin_date', 'new_checkout_date', 'new_rent', 'new_channel'])
    # find reservations in current_reservation_results that were made after the cancellation date, and before the cancellation checkin date
    # ensure the unit code is the same
    for cancelled_reservation in cancellations_results.itertuples():
        difference_results.loc[difference_results['unit'] == cancelled_reservation.unit, 'total_cancelled_reservations'] += 1
        # add to the total_cancelled_reservations column in the total_results dataframe
        total_results.loc[0, 'total_cancelled_reservations'] += 1


        for current_reservation in current_reservation_results.itertuples():
 
            if cancelled_reservation.unit == 'P811-X':
                one_one = ['P811-1', 'P811-2']
                for unit in one_one:
                    if current_reservation.unit == unit:
                        if cancelled_reservation.cancelled_at < current_reservation.created_at and cancelled_reservation.checkin_date <= current_reservation.checkin_date < cancelled_reservation.checkout_date:
                            # add the cancelled reservations unit, cancelled_at, checkin_date, checkout_date, and rent to the combo_results dataframe
                            # add the current reservations created_at, checkin_date, checkout_date, and rent to the combo_results dataframe
                            combo_results = pd.concat([combo_results, pd.DataFrame({'unit': [cancelled_reservation.unit], 'cancelled_at': [cancelled_reservation.cancelled_at], 'can_check_in': [cancelled_reservation.checkin_date], 'can_checkout': [cancelled_reservation.checkout_date], 'can_rent': [cancelled_reservation.rent], 'can_channel': [cancelled_reservation.channel], 'new_unit': [current_reservation.unit], 'new_created_at': [current_reservation.created_at], 'new_checkin_date': [current_reservation.checkin_date], 'new_checkout_date': [current_reservation.checkout_date], 'new_rent': [current_reservation.rent], 'new_channel': [current_reservation.channel]})], ignore_index=True)
            elif cancelled_reservation.unit == 'P813-X':
                one_three = ['P813-1', 'P813-2']
                for unit in one_three:
                    if current_reservation.unit == unit:
                        if cancelled_reservation.cancelled_at < current_reservation.created_at and cancelled_reservation.checkin_date <= current_reservation.checkin_date < cancelled_reservation.checkout_date:
                            combo_results = pd.concat([combo_results, pd.DataFrame({'unit': [cancelled_reservation.unit], 'cancelled_at': [cancelled_reservation.cancelled_at], 'can_check_in': [cancelled_reservation.checkin_date], 'can_checkout': [cancelled_reservation.checkout_date], 'can_rent': [cancelled_reservation.rent], 'can_channel': [cancelled_reservation.channel], 'new_unit': [current_reservation.unit], 'new_created_at': [current_reservation.created_at], 'new_checkin_date': [current_reservation.checkin_date], 'new_checkout_date': [current_reservation.checkout_date], 'new_rent': [current_reservation.rent], 'new_channel': [current_reservation.channel]})], ignore_index=True)
            elif cancelled_reservation.unit == 'P815-X':
                one_five = ['P815-1', 'P815-2']
                for unit in one_five:
                    if current_reservation.unit == unit:
                        if cancelled_reservation.cancelled_at < current_reservation.created_at and cancelled_reservation.checkin_date <= current_reservation.checkin_date < cancelled_reservation.checkout_date:
                            combo_results = pd.concat([combo_results, pd.DataFrame({'unit': [cancelled_reservation.unit], 'cancelled_at': [cancelled_reservation.cancelled_at], 'can_check_in': [cancelled_reservation.checkin_date], 'can_checkout': [cancelled_reservation.checkout_date], 'can_rent': [cancelled_reservation.rent], 'can_channel': [cancelled_reservation.channel], 'new_unit': [current_reservation.unit], 'new_created_at': [current_reservation.created_at], 'new_checkin_date': [current_reservation.checkin_date], 'new_checkout_date': [current_reservation.checkout_date], 'new_rent': [current_reservation.rent], 'new_channel': [current_reservation.channel]})], ignore_index=True)
            elif cancelled_reservation.unit == 'P823-X':
                two_three = ['P823-1', 'P823-2']
                for unit in two_three:
                    if current_reservation.unit == unit:
                        if cancelled_reservation.cancelled_at < current_reservation.created_at and cancelled_reservation.checkin_date <= current_reservation.checkin_date < cancelled_reservation.checkout_date:
                            combo_results = pd.concat([combo_results, pd.DataFrame({'unit': [cancelled_reservation.unit], 'cancelled_at': [cancelled_reservation.cancelled_at], 'can_check_in': [cancelled_reservation.checkin_date], 'can_checkout': [cancelled_reservation.checkout_date], 'can_rent': [cancelled_reservation.rent], 'can_channel': [cancelled_reservation.channel], 'new_unit': [current_reservation.unit], 'new_created_at': [current_reservation.created_at], 'new_checkin_date': [current_reservation.checkin_date], 'new_checkout_date': [current_reservation.checkout_date], 'new_rent': [current_reservation.rent], 'new_channel': [current_reservation.channel]})], ignore_index=True)
            elif cancelled_reservation.unit == 'P825-X':
                two_five = ['P825-1', 'P825-2']
                for unit in two_five:
                    if current_reservation.unit == unit:
                        if cancelled_reservation.cancelled_at < current_reservation.created_at and cancelled_reservation.checkin_date <= current_reservation.checkin_date < cancelled_reservation.checkout_date:
                            combo_results = pd.concat([combo_results, pd.DataFrame({'unit': [cancelled_reservation.unit], 'cancelled_at': [cancelled_reservation.cancelled_at], 'can_check_in': [cancelled_reservation.checkin_date], 'can_checkout': [cancelled_reservation.checkout_date], 'can_rent': [cancelled_reservation.rent], 'can_channel': [cancelled_reservation.channel], 'new_unit': [current_reservation.unit], 'new_created_at': [current_reservation.created_at], 'new_checkin_date': [current_reservation.checkin_date], 'new_checkout_date': [current_reservation.checkout_date], 'new_rent': [current_reservation.rent], 'new_channel': [current_reservation.channel]})], ignore_index=True)
            elif cancelled_reservation.unit == 'P827-X':
                two_seven = ['P827-1', 'P827-2']
                for unit in two_seven:
                    if current_reservation.unit == unit:
                        if cancelled_reservation.cancelled_at < current_reservation.created_at and cancelled_reservation.checkin_date <= current_reservation.checkin_date < cancelled_reservation.checkout_date:
                            combo_results = pd.concat([combo_results, pd.DataFrame({'unit': [cancelled_reservation.unit], 'cancelled_at': [cancelled_reservation.cancelled_at], 'can_check_in': [cancelled_reservation.checkin_date], 'can_checkout': [cancelled_reservation.checkout_date], 'can_rent': [cancelled_reservation.rent], 'can_channel': [cancelled_reservation.channel], 'new_unit': [current_reservation.unit], 'new_created_at': [current_reservation.created_at], 'new_checkin_date': [current_reservation.checkin_date], 'new_checkout_date': [current_reservation.checkout_date], 'new_rent': [current_reservation.rent], 'new_channel': [current_reservation.channel]})], ignore_index=True)
            elif cancelled_reservation.unit == 'P829-X':
                two_nine = ['P829-1', 'P829-2']
                for unit in two_nine:
                    if current_reservation.unit == unit:
                        if cancelled_reservation.cancelled_at < current_reservation.created_at and cancelled_reservation.checkin_date <= current_reservation.checkin_date < cancelled_reservation.checkout_date:
                            combo_results = pd.concat([combo_results, pd.DataFrame({'unit': [cancelled_reservation.unit], 'cancelled_at': [cancelled_reservation.cancelled_at], 'can_check_in': [cancelled_reservation.checkin_date], 'can_checkout': [cancelled_reservation.checkout_date], 'can_rent': [cancelled_reservation.rent], 'can_channel': [cancelled_reservation.channel], 'new_unit': [current_reservation.unit], 'new_created_at': [current_reservation.created_at], 'new_checkin_date': [current_reservation.checkin_date], 'new_checkout_date': [current_reservation.checkout_date], 'new_rent': [current_reservation.rent], 'new_channel': [current_reservation.channel]})], ignore_index=True)
            elif cancelled_reservation.unit == 'P1111-X':
                eleven_eleven = ['P1111-1', 'P1111-23']
                for unit in eleven_eleven:
                    if current_reservation.unit == unit:
                        if cancelled_reservation.cancelled_at < current_reservation.created_at and cancelled_reservation.checkin_date <= current_reservation.checkin_date < cancelled_reservation.checkout_date:
                            combo_results = pd.concat([combo_results, pd.DataFrame({'unit': [cancelled_reservation.unit], 'cancelled_at': [cancelled_reservation.cancelled_at], 'can_check_in': [cancelled_reservation.checkin_date], 'can_checkout': [cancelled_reservation.checkout_date], 'can_rent': [cancelled_reservation.rent], 'can_channel': [cancelled_reservation.channel], 'new_unit': [current_reservation.unit], 'new_created_at': [current_reservation.created_at], 'new_checkin_date': [current_reservation.checkin_date], 'new_checkout_date': [current_reservation.checkout_date], 'new_rent': [current_reservation.rent], 'new_channel': [current_reservation.channel]})], ignore_index=True)


            if cancelled_reservation.unit == current_reservation.unit:
                if cancelled_reservation.cancelled_at < current_reservation.created_at and cancelled_reservation.checkin_date <= current_reservation.checkin_date < cancelled_reservation.checkout_date:
                    # add the cancelled reservations unit, cancelled_at, checkin_date, checkout_date, and rent to the comparison_results dataframe
                    # add the current reservations created_at, checkin_date, checkout_date, and rent to the comparison_results dataframe
                    # add the difference in can_rent and new_rent to the comparison_results dataframe
                    comparison_results = pd.concat([comparison_results, pd.DataFrame({'unit': [cancelled_reservation.unit], 'can_res': [cancelled_reservation.res_is], 'cancelled_at': [cancelled_reservation.cancelled_at], 'can_checkin_date': [cancelled_reservation.checkin_date], 'can_checkout_date': [cancelled_reservation.checkout_date], 'can_rent': [cancelled_reservation.rent], 'can_channel': [cancelled_reservation.channel], 'new_res': [current_reservation.res_id], 'new_created_at': [current_reservation.created_at], 'new_checkin_date': [current_reservation.checkin_date], 'new_checkout_date': [current_reservation.checkout_date], 'new_rent': [current_reservation.rent],  'new_channel': [current_reservation.channel], 'diff_rent': [current_reservation.rent - cancelled_reservation.rent], 'bedrooms': [cancelled_reservation.bedrooms]})], ignore_index=True)
                    
                    # add the unit to the difference_results dataframe
                    # add 1 to the total_cancelled_reservations column
                    # add 1 to the total_new_reservations column
                    # add the difference in rent to the total_difference_in_rent column
                    # No duplicates in the unit column
                    if cancelled_reservation.unit not in difference_results['unit'].values:
                        new_row = {'unit': cancelled_reservation.unit, 'total_cancelled_reservations': 1, 'total_new_reservations': 1, 'total_difference_in_rent': current_reservation.rent - cancelled_reservation.rent}
                        difference_results = pd.concat([difference_results, pd.DataFrame(new_row, index=[0])], ignore_index=True)
                    else:
                        # difference_results.loc[difference_results['unit'] == cancelled_reservation.unit, 'total_cancelled_reservations'] += 1
                        difference_results.loc[difference_results['unit'] == cancelled_reservation.unit, 'total_new_reservations'] += 1

                        # if the unit already exists in the difference_results dataframe, add current_reservation.rent to the total_difference_in_rent column for that unit
                        if cancelled_reservation.unit in difference_results['unit'].values:
                            difference_results.loc[difference_results['unit'] == cancelled_reservation.unit, 'total_difference_in_rent'] += current_reservation.rent
                        else:
                            difference_results.loc[difference_results['unit'] == cancelled_reservation.unit, 'total_difference_in_rent'] += current_reservation.rent - cancelled_reservation.rent
                    # add to the total_rebooked_reservations column in the total_results dataframe
                    total_results.loc[0, 'total_rebooked_reservations'] += 1

    # sort the comparison_results dataframe by unit number
    comparison_results = comparison_results.sort_values(by=['unit'])
    # sort the difference_results dataframe by unit number
    difference_results = difference_results.sort_values(by=['unit'])

    # sort the combo_results dataframe by unit number
    combo_results = combo_results.sort_values(by=['unit'])
    combo_results.to_csv('combo_results.csv', index=False)
    
    difference_results.to_csv('difference_results.csv', index=False)

    print(comparison_results)
    comparison_results.to_csv('comparison_results.csv', index=False)


    cancellations_results.to_csv('cancellations_results.csv', index=False)
    # export the comparison_results dataframe to a csv file



        




except Exception as e:
    print(f"An error occurred: {str(e)}")
