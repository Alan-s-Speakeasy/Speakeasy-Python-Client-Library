from datetime import datetime
import logging
import time


class Chatroom:
    def __init__(self,
                 room_id: str,
                 my_alias: str,
                 prompt: str,
                 start_time: int,
                 remaining_time: int,
                 user_aliases: list[str],
                 **kwargs
                 ):
        """Chatroom - a model representing a chatroom for bots to interact.

        Args:
            room_id (str): A unique identifier for the chatroom.
            my_alias (str): The alias of this bot for the chatroom.
            prompt (str): The prompt associated with the chatroom.
            start_time (int): The starting time of the chatroom.
            remaining_time (int): The remaining time for the chatroom's activity.
            user_aliases (list[str]): A list of user aliases participating in the chatroom (generally including a chat partner and your bot).
        """

        self.room_id = room_id
        self.my_alias = my_alias
        self.prompt = prompt
        self.start_time = start_time
        self.remaining_time = remaining_time
        self.user_aliases = user_aliases
        self.initiated = False  # This flag indicates whether a welcome message has been sent

        logging.basicConfig(level=logging.INFO)

        self.session_token = kwargs.get('session_token', None)
        self.chat_api = kwargs.get('chat_api', None)
        if self.session_token is None or self.chat_api is None:
            logging.error(f"No session_token or chat_api for chatroom {self.room_id}, "
                          f"api requests by this chatroom will result in an error")
        # TODO: store answered ordinals for message and reaction

        self.__request_limit = 3  # seconds
        self.__state_cache = None  # ChatRoomState (including messages and reactions from api call)
        self.__last_state_call = 0
        self.__last_post_call = 0  # TODO: message queue?

    def __update_chat_room_state(self):
        """ Cache the state of this room and implement a request rate limit for this API call. """
        if self.session_token:
            current_time = time.time()
            elapsed_time = current_time - self.__last_state_call
            if elapsed_time >= self.__request_limit or self.__state_cache is None:
                try:
                    response = self.chat_api.get_api_room_with_roomid_with_since(
                        room_id=self.room_id, since=0, session=self.session_token)
                    if response:
                        self.__state_cache = response
                    else:
                        logging.error(f"Failed to update the state of room {self.room_id}.")
                    self.__last_state_call = current_time
                except Exception as e:
                    logging.error(f"An error occurred while updating the state of room {self.room_id}:", e)

        else:
            logging.error(f"This room {self.room_id} has no active session. Updating room state failed.")

    def get_messages(self):
        self.__update_chat_room_state()
        if self.__state_cache is None:
            logging.error(f"Updating room state failed. No messages in room {self.room_id}.")
            return []
        return self.__state_cache.messages

    def get_reactions(self):
        self.__update_chat_room_state()
        if self.__state_cache is None:
            logging.error(f"Updating room state failed. No reactions in room {self.room_id}.")
            return []
        return self.__state_cache.reactions

    def post_messages(self):
        pass

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
        start_time_formatted = datetime.fromtimestamp(self.start_time // 1000).strftime("%H:%M:%S, %d-%m-%Y")
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
