from fastapi import Request
from datetime import datetime
import requests
import json


def get_current_time():
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    return current_datetime_str


async def get_parsed_data(request: Request):
    json_string = await request.body()
    json_string = json_string.decode("utf-8")
    parsed_data = json.loads(json_string)

    return parsed_data


def get_user_info_from_google(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo', headers=headers)

    return response