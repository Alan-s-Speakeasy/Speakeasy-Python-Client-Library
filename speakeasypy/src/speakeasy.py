from speakeasy_python_scripts import Configuration
from speakeasy_python_scripts.apis import UserApi
from speakeasy_python_scripts.api_client import ApiClient
from speakeasy_python_scripts.model.login_request import LoginRequest
import logging
import atexit


class Speakeasy:
    def __init__(self,
                 host: str,  # production: host = https://speakeasy.ifi.uzh.ch
                 username: str,
                 password: str):

        self.config = Configuration(host=host, username=username, password=password)
        # Create an instance of the API client
        self.api_client = ApiClient(configuration=self.config)
        # Create apis for user management (login / logout for bots)
        self.user_api = UserApi(self.api_client)

        self.session_token = None
        logging.basicConfig(level=logging.INFO)
        atexit.register(self.logout)

    def login(self) -> str:
        # Prepare the login request
        login_request = LoginRequest(username=self.config.username, password=self.config.password)

        try:
            response = self.user_api.post_api_login(login_request=login_request)
            if response:
                user_session_details = response
                # store the session token
                self.session_token = user_session_details.session_token
                print("Login successful. Session token:", self.session_token)
            else:
                logging.error("Login failed.")
        except Exception as e:
            logging.error("An error occurred: %s", e)

        input("Type anything to logout:")  # TODO: just for test

        return self.session_token

    def logout(self):
        if self.session_token:
            try:
                response = self.user_api.get_api_logout(session=self.session_token)
                if response:
                    print("Logout successful.")
                else:
                    logging.error("Logout failed.")
            except Exception as e:
                logging.error("An error occurred during logout:", e)
        else:
            print("No active session to logout from.")

