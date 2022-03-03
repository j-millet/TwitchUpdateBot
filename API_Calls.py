import requests
from Authentication import Authentication
from functools import lru_cache

auth = Authentication()

@lru_cache(maxsize=512)
async def user_exists(name:str)->bool:    #check if user with name exists
    headers = {
        'Client-Id': auth.client_id,
        'Authorization': auth.get_oauth(),
    }
    params = (
        ('login', name),
    )
    response = requests.get('https://api.twitch.tv/helix/users?',headers=headers, params=params)
    return response.json()["data"] != []


def is_live(name:str)->bool: #check live status of a single channel
    headers = {
        'Client-Id': auth.client_id,
        'Authorization': auth.get_oauth(),
    }
    params = (
        ('user_login', name),
    )
    response = requests.get('https://api.twitch.tv/helix/streams?',headers=headers, params=params)
    return response.json()['data'] != []
