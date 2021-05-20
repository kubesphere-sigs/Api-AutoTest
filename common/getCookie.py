import requests
from config import config


def get_token(server):
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64)", "Connection": "close"}
    data = {
        'username': 'admin',
        'password': 'P@88w0rd',
        'grant_type': 'password'
    }
    try:
        r = requests.post(server + '/oauth/token', headers=header, data=data)
        if r.status_code == 200:
            token = r.json()['access_token']
        else:
            # logger.info('get token response:{}'.format(r))
            raise Exception('get token failed!')
    except requests.exceptions.ConnectionError as e:
        print('Error', e.args)

    ks_token = 'Bearer ' + token
    return ks_token

