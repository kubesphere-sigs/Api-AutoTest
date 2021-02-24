from common.getCookie import get_token
from config import config



def get_header():
    header = {
            'Authorization': get_token(config.url),
            'Content-Type': 'application/json',
            'Connection': 'close'
        }
    return header

def get_header_for_patch():
    header = {
        'Authorization': get_token(config.url),
        'Content-Type': 'application/merge-patch+json'
    }
    return header