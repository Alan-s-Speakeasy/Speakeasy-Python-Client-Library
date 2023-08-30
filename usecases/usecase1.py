from speakeasypy import Speakeasy

DEFAULT_HOST_URL = 'http://127.0.0.1:8080'

test_username = 'bot1'
test_password = 'bot1'

speakeasy = Speakeasy(host=DEFAULT_HOST_URL, username=test_username, password=test_password)

speakeasy.login()

