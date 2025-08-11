import atexit
import json
import time
from enum import Enum
from pprint import pprint
from typing import Dict, List

import sseclient
from alive_progress import alive_it
from alive_progress.styles import Show, showtime
from openapi import Configuration, exceptions
from openapi.api import ChatApi, UserApi
from openapi.api_client import ApiClient
from openapi.models import ChatMessageReaction, LoginRequest, RestChatMessage

from speakeasypy.src.chatroom import Chatroom


class EventType(Enum):
    """
    Enumeration for the different types of events received from the SSE stream.
    """
    MESSAGE = "MESSAGE"
    REACTION = "REACTION"
    ROOMS = "ROOMS"


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

        # Register the logout function to be called on exit. 
        atexit.register(self.logout)

        self.sse_client = None
        self._callbacks_sse: Dict[EventType, List] = {
            EventType.MESSAGE: [],
            EventType.REACTION: [],
            EventType.ROOMS: [],
        }

    def login(self) -> str:
        """Self-explanatory method to login to the API."""
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

    def start_listening(self):
        """Start the listening process and call corresponding callbacks upon receiving events.

        Under the hood, it uses a SSE client to receive events."""
        if self.sse_client is None:
            self.sse_client = self._connect_to_sse()
        for event in alive_it(
            self.sse_client,
            stats=False,
            title="Listening for events",
            bar="bubbles",
            spinner="dots_waves",
        ):
            event_type = (
                EventType(event.event) if event.event in EventType.__members__ else None
            )
            callbacks = self._callbacks_sse[event_type] if event_type else []
            event_data = json.loads(event.data) if event.data else {}

            if event_type == EventType.MESSAGE:
                chatroom = self._get_cached_chatroom(event_data["roomId"])
                # The event does not contain this field, but the parser needs it
                event_data["read"] = True
                message = RestChatMessage.from_dict(event_data)
                # Update the cached chatroom with the new message
                chatroom.update_state_with_new_messages([message])
                if event_data["authorAlias"] != chatroom.my_alias:
                    for callback in callbacks:
                        callback(message.message, chatroom)
            elif event_type == EventType.REACTION:
                chatroom = self._get_cached_chatroom(event_data["roomId"])
                reaction = ChatMessageReaction.from_dict(event_data)
                chatroom.update_state_with_new_reactions([reaction])
                for callback in callbacks:
                    callback(reaction.type, reaction.message_ordinal, chatroom)
            elif event_type == EventType.ROOMS:
                # Update the chatrooms cache when a new room is created or deleted
                self.__update_chat_rooms()
                chatroom = self._get_cached_chatroom(event_data["rooms"][0]["uid"])
                for callback in callbacks:
                    callback(chatroom)
            else:
                print(f"Unknown event type: {event_type}. No callbacks registered.")

    def _get_cached_chatroom(self, room_id: str, _tries=0) -> Chatroom:
        """Returns the cached Chatroom instance for the given room_id."""
        if _tries > 3:
            raise ValueError(
                f"Failed to get chatroom {room_id} after 3 tries. It looks like the room does not exist"
            )
        if room_id in self._chatrooms_dict:
            return self._chatrooms_dict[room_id]
        else:
            self.__update_chat_rooms()
            # Wait a bit and retry, the backend sometimes needs time to add a new room
            time.sleep(0.1)
            return self._get_cached_chatroom(room_id, _tries + 1)

    def _connect_to_sse(self):
        sse_url = f"{self.config.host}/sse/rooms"
        return sseclient.SSEClient(sse_url, cookies={"SESSIONID": self.session_token})

    def register_callback(self, callback, event_type: EventType):
        """Registers a callback function to be called when a specific event occurs."""
        self._callbacks_sse[event_type].append(callback)

    def remove_callback(self, callback, event_type: EventType):
        """Removes a previously registered callback function for a specific event type."""
        if callback in self._callbacks_sse[event_type]:
            self._callbacks_sse[event_type].remove(callback)
        else:
            print(f"Callback {callback} not found for event type {event_type}.")

    def logout(self):
        """Self-explanatory method to logout from the API."""
        if self.session_token:
            self.user_api.get_api_logout(session=self.session_token)
            self.session_token = None
            print("Logout successful.")
        else:
            print("No active session to logout from.")

    def __update_chat_rooms(self):
        """Cache the list of chat rooms and implement a request rate limit for this API call.

        This method does not update the chatrooms messages or reactions, but rather only the chatrooms.
        """
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
        else:
            print("WARNING : It looks like you are polling for chatrooms manually. Consider using event-streaming instead with `client.start_listening`.")

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
