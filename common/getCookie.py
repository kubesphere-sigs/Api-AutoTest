import requests


def get_token(server):
    header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/90.0.4430.212 Safari/537.36",
              "connection": "close",
              "verify": "false"}
    data = {
        'username': 'admin',
        'password': 'P@88w0rd',
        'grant_type': 'password'
    }
    url = server + '/oauth/token'
    try:
        r = requests.post(url=url, headers=header, data=data)
        if r.status_code == 200:
            token = r.json()['access_token']
        else:
            raise Exception('get token failed!')
    except requests.exceptions.ConnectionError as e:
        print('Error', e.args)

    ks_token = 'Bearer ' + token
    return ks_token


