import sqlite3
import datetime
import calendar
from contextlib import contextmanager

from dt_functions.data_formatting_functions import change_str_to_date_format
from config import PATH_TO_DB, PATH_TO_BACKUP_DB


# Connect to database
@contextmanager
def open_db():
    connection = sqlite3.connect(PATH_TO_DB)
    try:
        cursor = connection.cursor()
        yield cursor
    finally:
        connection.commit()
        connection.close()


# Get a generator that contains active users from database
def get_id_list():

    with open_db() as cursor:
        cursor.execute("SELECT id FROM users")
        res = (id[0] for id in cursor.fetchall())

    return res


# Add new user to database
def add_user_to_db(id, username, first_name, last_name):

    with open_db() as cursor:
        # id, username, first_name, last_name, start_date, notification, status, link_name, link_address
        insert_query = "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"
        user_data = (id, username, first_name, last_name, "2000-01-01", "2000-01-01", 0, None, None)
        cursor.execute(insert_query, user_data)


# Create a database backup
def create_backup_db():

    con = sqlite3.connect(PATH_TO_DB)
    bck = sqlite3.connect(PATH_TO_BACKUP_DB)
    with bck:
        con.backup(bck, pages=1)
    bck.close()
    con.close()


# Return from database subscription finish date
def get_finish_date(user_id):

    with open_db() as cursor:
        sql_finish_date = f"SELECT finish_date FROM users WHERE id IS ?"
        cursor.execute(sql_finish_date, (user_id,))
        res = cursor.fetchone()[0]

    return res


# Get subscription status for a specific user from database
def get_status(user_id):

    with open_db() as cursor:
        sql_status = f"SELECT status FROM users WHERE id IS ?"
        cursor.execute(sql_status, (user_id,))
        res = cursor.fetchone()[0]

    return res


# Get the date to send a notification to the user when their subscription expires
# Based on the module Datetime, the date is calculated from the principle: finish date minus 3 days
def get_payment_notice(user_id):

    finish_date = get_finish_date(user_id)
    finish_date = change_str_to_date_format(finish_date)
    payment_notice = str(finish_date - datetime.timedelta(days=3))

    return payment_notice


# change user status to active
def update_status(user_id):

    with open_db() as cursor:
        sql_update_status = f"UPDATE users SET status = 1 WHERE id = ?"
        cursor.execute(sql_update_status, (user_id,))


# change user status to inactive
def cancel_status(user_id):

    with open_db() as cursor:
        sql_update_status = f"UPDATE users SET status = 0 WHERE id = ?"
        cursor.execute(sql_update_status, (user_id,))


# When renewing a subscription for 1 month, it extends the expiration date
def update_finish_day(user_id):

    with open_db() as cursor:
        finish_date = get_finish_date(user_id)
        finish_date = change_str_to_date_format(finish_date)

        days = calendar.monthrange(finish_date.year, finish_date.month)[1]
        next_month_date = str(finish_date + datetime.timedelta(days=days))

        sql_update_finish_date = "UPDATE users SET finish_date= ? WHERE id = ?"
        data = (next_month_date, user_id)
        cursor.execute(sql_update_finish_date, data)


# Returns today's date
def get_today_date() -> str:

    today = datetime.date.today()
    today = str(today)

    return today


# Changes the default value to a the subscription date to the database
def update_start_day(user_id):

    with open_db() as cursor:
        today = get_today_date()
        sql_update_start_date = "UPDATE users SET start_date= ? WHERE id = ?"
        data = (today, user_id)
        cursor.execute(sql_update_start_date, data)


# Assigns an expiration date for the subscription based on today's date
def set_finish_date(user_id):

    with open_db() as cursor:
        today = get_today_date()
        today = change_str_to_date_format(today)

        days = calendar.monthrange(today.year, today.month)[1]
        finish_date = str(today + datetime.timedelta(days=days))

        sql_get_finish_date = "UPDATE users SET finish_date= ? WHERE id = ?"
        data = (finish_date, user_id)
        cursor.execute(sql_get_finish_date, data)


# Get data(id, username, first_name, last_name) about a specific user from database
def get_information_from_db(user_id):

    with open_db() as cursor:
        sql_get_info_query = "SELECT username, first_name, last_name FROM users WHERE id IS ?"
        cursor.execute(sql_get_info_query, (user_id,))
        result = cursor.fetchall()

    return result


# Return tuple(link_name, link_address) from db
def get_link_to_connection() -> tuple:
    with open_db() as cursor:
        cursor.execute("SELECT * FROM links")
        link_data = cursor.fetchone()

        return link_data


# Delete link_name and link_address from database
def delete_address_data(link_address):
    with open_db() as cursor:
        sql_delete_link = "DELETE FROM links WHERE link_address IS ?"
        cursor.execute(sql_delete_link, (link_address,))


# Update link_address assigned a specific user from database
def update_link_address(user_id, link_address):
    with open_db() as cursor:
        sql_update_link_address = "UPDATE users SET link_address = ? WHERE id = ?"
        cursor.execute(sql_update_link_address, (link_address, user_id))


# Update link_name assigned a specific user from database
def update_link_name(user_id, link_name):
    with open_db() as cursor:
        sql_update_link_address = "UPDATE users SET link_name = ? WHERE id = ?"
        cursor.execute(sql_update_link_address, (link_name, user_id))


# Get a number of active links from database
def get_number_of_link_address():

    with open_db() as cursor:

        cursor.execute("SELECT count(link_address) FROM links")
        result = cursor.fetchone()[0]

    return result
