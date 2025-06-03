import datetime


# Example input data format 2022-04-05
# Example output data format 05.04.2022
def change_date_format(date_string):

    date_list = date_string.split("-")
    formatted_string = ".".join(reversed(date_list))

    return formatted_string


# Converts an object of format Str to format Datetime
def change_str_to_date_format(date_string):
    date = datetime.datetime.strptime(date_string, "%Y-%m-%d").date()

    return date


def get_users_data_from_photo(data):
    users_data = data.split("&??&")[1].split("\n")

    return users_data
