import requests

PROXY_POOL_URL = 'http://139.198.112.88:5555/random'


def get_proxy():
    try:
        qheaders = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64)", "Connection": "close"}
        response = requests.get(PROXY_POOL_URL, headers=qheaders)
        if response.status_code == 200:
            return response.text
    except ConnectionError:
        return None