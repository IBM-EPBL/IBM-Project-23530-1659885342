import json, random, requests, string,time
from urllib.parse import urlparse, parse_qs
from selenium import webdriver

def auth(credentials):
    creds = read_creds(credentials)
    client_id, client_secret = creds['client_id'], creds['client_secret']
    redirect_uri = creds['redirect_uri']
    api_url = 'https://www.linkedin.com/oauth/v2' 
    
    args = client_id,client_secret,redirect_uri
    auth_code = authorize(api_url,*args)
    access_token = refresh_token(auth_code,*args)
    creds.update({'access_token':access_token})
    save_token(credentials,creds)

    return access_token

def headers(access_token):
    headers = {
    'Authorization': f'Bearer {access_token}',
    'cache-control': 'no-cache',
    'X-Restli-Protocol-Version': '2.0.0'
    }
    return headers

def read_creds(filename):
    with open(filename) as f:
        credentials = json.load(f)
    return credentials

def save_token(filename,data):
    data = json.dumps(data, indent = 4) 
    with open(filename, 'w') as f: 
        f.write(data)

def create_CSRF_token():
    letters = string.ascii_lowercase
    token = ''.join(random.choice(letters) for i in range(20))
    return token
    
def parse_redirect_uri(redirect_response):
    url = urlparse(redirect_response)
    url = parse_qs(url.query)
    return url['code'][0]

def authorize(api_url,client_id,client_secret,redirect_uri):
    csrf_token = create_CSRF_token()
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': csrf_token,
        'scope': 'r_liteprofile,r_emailaddress'
    }
    response = requests.get(f'{api_url}/authorization',params=params)

    driver = webdriver.Chrome()
    driver.get(response.url)
    time.sleep(30)
    get_url = driver.current_url
    print("The current url is:"+str(get_url))
    redirect_response = driver.current_url
    driver.quit()
    auth_code = parse_redirect_uri(redirect_response)
    return auth_code

def refresh_token(auth_code,client_id,client_secret,redirect_uri):
    access_token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
        }
    response = requests.post(access_token_url, data=data, timeout=30)
    response = response.json()
    access_token = response['access_token']
    return access_token

def start():
    credentials = 'data/linkedin_credentials.json'
    access_token = auth(credentials)
    return access_token

def get_user_info(access_token):
    h = headers(access_token)
    response1 = requests.get('https://api.linkedin.com/v2/me', headers = h)
    response2 = requests.get('https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))', headers = h)
    user_name_info = response1.json()
    user_mail_info = response2.json()
    return user_name_info, user_mail_info