from common.getCookie import get_token
from common.getConfig import get_config

env_url = get_config()['env']['url']


def get_header():
    header = {
        'Authorization': get_token(env_url),
        'Content-Type': 'application/json',
        'Connection': 'close'
    }
    return header


def get_header_for_urlencoded():
    header = {
        'Authorization': get_token(env_url),
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'close'
    }
    return header


def get_header_for_patch():
    header = {
        'Authorization': get_token(env_url),
        'Content-Type': 'application/merge-patch+json'
    }
    return header

