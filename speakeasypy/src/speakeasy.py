from openapi import exceptions
from openapi import Configuration
from openapi.api import UserApi
from openapi.api import ChatApi
from openapi.api_client import ApiClient
from openapi.models import LoginRequest
from speakeasypy.src.chatroom import Chatroom
from typing import Dict, List

import atexit
import time


class Speakeasy:
    def __init__(
        self,
        host: str,  # production: host = https://speakeasy.ifi.uzh.ch
        username: str,
        password: str,
    ):

        self.config = Configuration(host=host, username=username, password=password)
        # Create an instance of the API client
        self.api_client = ApiClient(configuration=self.config)
        # Create api for user management (login / logout for bots)
        self.user_api = UserApi(self.api_client)
        # Create api for chat management with the current session token
        self.chat_api = ChatApi(self.api_client)

        self.session_token = None
        self._chatrooms_dict: Dict[str, Chatroom] = (
            {}
        )  # map room_id to Chatroom (cache)
        self.__last_call_for_rooms = 0

        self.__request_limit = 1  # TODO: change the default value here!

        atexit.register(self.logout)

    def login(self) -> str:
        """Self-explanatory method to login to the API.
        """
        # Prepare the login request
        login_request = LoginRequest(
            username=self.config.username, password=self.config.password
        )

        try:
            response = self.user_api.post_api_login(
                login_request=login_request
            )  # user session details
            print("Login successful. Session token:", response.session_token)
            self.session_token = response.session_token
        except exceptions.UnauthorizedException as e:
            e.reason += " (Please try again with the correct username and password)"
            raise e

        return self.session_token

    def logout(self):
        """Self-explanatory method to logout from the API.
        """
        if self.session_token:
            self.user_api.get_api_logout(session=self.session_token)
            self.session_token = None
            print("Logout successful.")
        else:
            print("No active session to logout from.")

    def __update_chat_rooms(self):
        """Cache the list of rooms and implement a request rate limit for this API call."""
        if not self.session_token:
            reason = "Failed to fetch chatrooms because there is no active session (Please check if you are logged in)"
            raise exceptions.UnauthorizedException(status=401, reason=reason)

        current_time = time.time()
        elapsed_time = current_time - self.__last_call_for_rooms
        if elapsed_time >= self.__request_limit:
            try:
                # Call the get_api_rooms endpoint to fetch the list of chat rooms info
                response = self.chat_api.get_api_rooms(session=self.session_token)
                chatroom_info_list = response.rooms
                for room_info in chatroom_info_list:
                    # Convert responses from api into Chatroom instances and add new chatrooms
                    if room_info.uid not in self._chatrooms_dict.keys():
                        self._chatrooms_dict[room_info.uid] = Chatroom(
                            room_id=room_info.uid,
                            my_alias=room_info.alias,
                            prompt=room_info.prompt,
                            start_time=room_info.start_time,
                            remaining_time=room_info.remaining_time,
                            user_aliases=room_info.user_aliases,
                            session_token=self.session_token,
                            chat_api=self.chat_api,
                            request_limit=self.__request_limit,
                        )
                    else:  # update remaining_time of existing chatrooms
                        self._chatrooms_dict[room_info.uid].remaining_time = (
                            room_info.remaining_time
                        )
                self.__last_call_for_rooms = current_time
            except exceptions.UnauthorizedException as e:
                e.reason += (
                    " (Failed to fetch chatrooms, please check if you are logged in "
                    "and have a valid session token)"
                )
                raise e

    def get_rooms(
        self, active=True
    ) -> List[Chatroom]:  # includes non-active chatrooms (i.e., remaining_time == 0)
        """
        Retrieves a list of available chatrooms.

        This method first updates the internal chatrooms dictionary by calling
        the private method `__update_chat_rooms()`, and then returns either all
        chatrooms or only active ones based on the `active` parameter.

        Parameters:
        ----------
        active : bool, optional
            If True, only returns active chatrooms (i.e., with remaining_time > 0).
            If False, returns all chatrooms including inactive ones.
            Defaults to True.

        Returns:
        -------
        List[Chatroom]
            A list of Chatroom objects matching the active criteria.

        Notes:
        -----
        There's a potential lag in active detection that might cause API errors
        when interacting with rooms that have just become inactive.
        """
        self.__update_chat_rooms()

        if active:  # only returns active chatrooms (i.e., remaining_time > 0)
            # TODO: To avoid a lag in active detection that would make room's apis throw errors
            #  (those apis only allow interactions for active rooms),
            #  we can increase the threshold to self.__request_limit * 1000
            return [
                room
                for room in list(self._chatrooms_dict.values())
                if room.remaining_time > 0
            ]

        return list(self._chatrooms_dict.values())
