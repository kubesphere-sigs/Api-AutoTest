import requests


def get_token(server):
    header = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'close'
    }
    data = {
        'username': 'admin',
        'password': 'P@88w0rd',
        'grant_type': 'password'
    }

    r = requests.post(server + '/oauth/token', headers=header, data=data)

    if r.status_code == 200:
        token = r.json()['access_token']
    else:
        # logger.info('get token response:{}'.format(r))
        raise Exception('get token failed!')

    ks_token = 'Bearer ' + token
    return ks_token
