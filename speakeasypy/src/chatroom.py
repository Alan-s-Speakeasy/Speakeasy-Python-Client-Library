import time
import warnings
import requests

from datetime import datetime
from typing import List, Union
from openapi.api.chat_api import ChatApi
from openapi import exceptions
from openapi.models import RestChatMessage, ChatMessageReaction


class Chatroom:
    def __init__(
        self,
        room_id: str,
        my_alias: str,
        prompt: str,
        start_time: int,
        remaining_time: int,
        user_aliases: List[str],
        **kwargs,
    ):
        """Chatroom - a model representing a chatroom for bots to interact.

        Args:
            room_id (str): A unique identifier for the chatroom.
            my_alias (str): The alias of this bot for the chatroom.
            prompt (str): The prompt associated with the chatroom.
            start_time (int): The starting time of the chatroom.
            remaining_time (int): The remaining time for the chatroom's activity.
            user_aliases (List[str]): A list of user aliases participating in the chatroom (generally including a chat partner and your bot).
        """

        self.room_id = room_id
        self.my_alias = my_alias
        self.prompt = prompt
        self.start_time = start_time
        self.remaining_time = remaining_time
        self.user_aliases = user_aliases
        self.initiated = (
            False  # This flag indicates whether a welcome message has been sent
        )

        self.session_token = kwargs.get("session_token", None)
        self.chat_api: ChatApi = kwargs.get("chat_api", None)
        if self.session_token is None or self.chat_api is None:
            warnings.warn(
                f"No session_token or chat_api for chatroom {self.room_id}, "
                f"API requests by this chatroom will result in an error."
            )
        # Store ordinals for processed messages and reactions to exclude them from "new" messages.
        self.processed_ordinals = {
            "messages": [],
            "reactions": [],
        }

        self.__request_limit = kwargs.get("request_limit", 1)  # seconds
        self.__state_api_cache = (
            None  # ChatRoomState (including messages and reactions from api call)
        )
        self.__last_msg_timestamp = 0
        self.__last_state_call = 0
        self.__last_post_call = 0

    def __update_chat_room_state(self):
        """Cache the state of this room and implement a request rate limit for this API call."""
        if not self.session_token:
            reason = f"Failed to update room state because the room {self.room_id} has no active session."
            raise exceptions.UnauthorizedException(status=401, reason=reason)

        current_time = time.time()
        elapsed_time = current_time - self.__last_state_call
        if elapsed_time < self.__request_limit and self.__state_api_cache is not None:
            return
        try:
            # TODO : This will fetch the entire chat history of the room, which is not efficient.
            # This will be fixed soon when SSE streaming is implemented.
            response = self.chat_api.get_api_room_by_room_id(
                room_id=self.room_id, session=self.session_token
            )

            if self.__state_api_cache is None:
                self.__state_api_cache = response
            else:
                # The reactions returned by the backend have nothing to do with the "since" parameter for now,
                # so just copy all reactions here.
                self.__state_api_cache.reactions = response.reactions
                # Append new messages and update the last timestamp
                for m in response.messages:
                    if m.ordinal not in [
                        msg.ordinal for msg in self.__state_api_cache.messages
                    ]:
                        self.__state_api_cache.messages.append(m)
                        self.__last_msg_timestamp = max(
                            self.__last_msg_timestamp, m.time_stamp
                        )
            self.__last_state_call = current_time
        except exceptions.UnauthorizedException as e:
            e.reason += f" (Failed to update the state of room {self.room_id})"
            raise e
        except exceptions.NotFoundException as e:
            e.reason += f" (Failed to find the room {self.room_id})"
            raise e

    def get_messages(self, only_partner=True, only_new=True) -> List[RestChatMessage]:
        self.__update_chat_room_state()
        if self.__state_api_cache is None:
            return []

        filtered_messages = self.__state_api_cache.messages

        if only_partner:
            filtered_messages = [
                message
                for message in filtered_messages
                if message.author_alias != self.my_alias
            ]

        if only_new:
            filtered_messages = [
                message
                for message in filtered_messages
                if message.ordinal not in self.processed_ordinals["messages"]
            ]

        return filtered_messages

    def get_reactions(self, only_new=True) -> List[ChatMessageReaction]:
        self.__update_chat_room_state()
        if self.__state_api_cache is None:
            return []

        filtered_reactions = self.__state_api_cache.reactions
        if only_new:
            filtered_reactions = [
                reaction
                for reaction in filtered_reactions
                if reaction.message_ordinal not in self.processed_ordinals["reactions"]
            ]
        return filtered_reactions

    def post_messages(self, message: str):
        """
        Posts a message to the current chatroom.

        This method sends the provided message to the chatroom identified by room_id.
        It implements rate limiting to prevent sending messages too frequently and
        handles authentication and connection errors.

        Args:
            message (str): The message content to post to the chatroom.

        Raises:
            UnauthorizedException: If the room has no active session or invalid credentials.
            NotFoundException: If the specified room is not found.
            HTTPError: For other HTTP-related errors.

        Note:
            This method implements rate limiting and may pause execution to avoid
            exceeding the request frequency limit.
        """
        if not self.session_token:
            reason = f"Failed to post messages because the room {self.room_id} has no active session."
            raise exceptions.UnauthorizedException(status=401, reason=reason)

        # Check if the time elapsed since the last post call is less than the request limit.
        current_time = time.time()
        elapsed_time = current_time - self.__last_post_call
        # If elapsed time is less than the request limit, sleep for the remaining time to enforce rate limiting.
        if elapsed_time < self.__request_limit:
            time.sleep(self.__request_limit - elapsed_time)
            print(
                f"(Sleep {self.__request_limit - elapsed_time} secs to avoid posting requests too frequently.)"
            )

        # TODO: When using `self.chat_api.post_api_room_with_roomid()`, it's challenging to address
        #  issues related to UTF-8 due to the complex relationships in the generated library and its
        #  many dependencies. The current solution is to directly use the `requests` library.
        # self.chat_api.post_api_room_with_roomid(room_id=self.room_id, session=self.session_token, body=message)
        res = requests.post(
            url=self.chat_api.api_client.configuration.host
            + f"/api/room/{self.room_id}",
            params={"session": self.session_token},
            data=message.encode("utf-8"),
        )
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            if res.status_code == 401:
                raise exceptions.UnauthorizedException(
                    status=res.status_code,
                    reason="Failed to post a message. Please check your credentials.",
                ) from http_err
            elif res.status_code == 404:
                raise exceptions.NotFoundException(
                    status=res.status_code,
                    reason=f"Failed to post a message because the room {self.room_id} is not found.",
                ) from http_err
            else:
                raise http_err

        self.__last_post_call = time.time()  # store the completed time

    def mark_as_processed(
        self, msg_or_rec: Union[RestChatMessage, ChatMessageReaction]
    ):
        """
        Marks a chatroom message or reaction as processed.

        This method keeps track of which messages and reactions have been processed
        by adding their ordinal values to the appropriate tracking list within
        the processed_ordinals dictionary.

        Args:
            msg_or_rec (Union[RestChatMessage, ChatMessageReaction]): The message or
                reaction object to mark as processed.

        Raises:
            TypeError: If the provided object is neither a RestChatMessage nor a
                ChatMessageReaction.

        Note:
            For messages, the message's ordinal is added to processed_ordinals['messages'].
            For reactions, the message's ordinal is added to processed_ordinals['reactions'].
        """
        if isinstance(msg_or_rec, RestChatMessage):
            self.processed_ordinals["messages"].append(msg_or_rec.ordinal)
        elif isinstance(msg_or_rec, ChatMessageReaction):
            self.processed_ordinals["reactions"].append(msg_or_rec.message_ordinal)
        else:
            raise TypeError(
                "Please pass a message or reaction object to mark it as processed."
            )

    def get_chat_partner(self) -> str:
        # get the alias of your chat partner
        return next(alias for alias in self.user_aliases if alias != self.my_alias)

    def __eq__(self, other):
        if isinstance(other, Chatroom):
            return self.room_id == other.room_id
        return False

    def __contains__(self, chatroom_list):
        return any(self == room for room in chatroom_list)

    def __str__(self):
        start_time_formatted = datetime.fromtimestamp(self.start_time // 1000).strftime(
            "%H:%M:%S, %d-%m-%Y"
        )
        remaining_min, remaining_sec = divmod(self.remaining_time // 1000, 60)

        return f"""
        room_id: {self.room_id};
        my_alias: {self.my_alias};
        prompt: {self.prompt};
        start_time: {start_time_formatted};
        remaining_time: {remaining_min}min {remaining_sec}sec.
        """

    def __repr__(self):
        return str(self)
