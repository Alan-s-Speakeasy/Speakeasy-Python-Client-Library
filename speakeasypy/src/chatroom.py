from datetime import datetime
import logging


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

    def __get_chat_room_state(self):  # TODO: rate limit
        pass

    def get_messages(self):
        pass

    def get_reactions(self):
        pass

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
