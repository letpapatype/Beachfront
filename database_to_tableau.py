import pymysql
from sshtunnel import SSHTunnelForwarder
import csv
import dropbox
import datetime
import os

# SSH tunnel configuration
ssh_host = os.environ['SSH_HOST']
ssh_port = 8022
ssh_username = 'beachfrontvr-bi'
ssh_pem_key = 'key.pem'

# MySQL server configuration
mysql_host = os.environ['MYSQL_HOST']
mysql_port = 3306
mysql_username = 'beachfrontvr-bi'
mysql_password = os.environ['MYSQL_PASSWORD']
mysql_database = os.environ['MYSQL_DATABASE']

queries = ['customtrack', 'customrates']

for query in queries:

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

            # read the sql command from a file within the same directory
            with open(f'{query}.sql', 'r') as file:
                sql = file.read()

            # Execute a sample query
            cursor = connection.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            print("Successfully executed query. Exporting results to CSV...")

            csv_file_name = f'{query}.csv'

            # output the results to a csv file
            with open(csv_file_name, 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow([i[0] for i in cursor.description])
                csv_writer.writerows(rows)

            print("Successfully exported results to CSV. Closing connection...")
            # Close the cursor and connection
            cursor.close()
            connection.close()

    except Exception as e:
        print(f"An error occurred: {str(e)}")


    #I would then want to take the csv file and upload it to a dropbox folder
    access_token = os.environ['DROPBOX_ACCESS_TOKEN']
    # connect to dropbox
    dbx = dropbox.Dropbox(access_token)
    
    print("Successfully connected to Dropbox. Removing old file...")
    # remove old file
    try:
        dbx.files_delete(f'/9 Booking Export List/{csv_file_name}')
        print(f"Successfully removed the old {csv_file_name}.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


    print(f"Uploading {query}.csv...")


    dropbox_file_path = f'/9 Booking Export List/{csv_file_name}'

    try:
        # Upload the file to Dropbox
        with open(csv_file_name, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_file_path)

        # Get the uploaded file's metadata
        file_metadata = dbx.files_get_metadata(dropbox_file_path)

        # Print the uploaded file's metadata
        print("Uploaded file:", file_metadata.path_display)
    except Exception as e:
        print(f"An error occurred: {str(e)}")



