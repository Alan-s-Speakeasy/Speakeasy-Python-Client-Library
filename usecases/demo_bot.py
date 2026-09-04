import time
from speakeasypy import Chatroom, EventType, Speakeasy, get_logger

DEFAULT_HOST_URL = 'https://speakeasy.ifi.uzh.ch'
logger = get_logger("speakeasy_bot")

# TODO: Replace with bot credentials
BOT_USERNAME = 'TODO'
BOT_PASSWORD = 'TODO'

class Agent:
    def __init__(self, username, password):
        self.username = username
        # Initialize the Speakeasy Python framework and login.
        self.speakeasy = Speakeasy(host=DEFAULT_HOST_URL, username=username, password=password, logger=logger)
        self.speakeasy.login()  # This framework will help you log out automatically when the program terminates.

        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)
        self.speakeasy.register_callback(self.on_new_reaction, EventType.REACTION)

    def listen(self):
        """Start listening for events."""
        self.speakeasy.start_listening()

    def on_new_message(self, message : str, room : Chatroom):
        """Callback function to handle new messages."""
        try:
            logger.info(f"Room: [{room.room_id}], Msg: [{message}]")

            # TODO: Implement your agent logic here and respond to the message.
            answer = f"Received your message: '{message}'"

            room.post_messages(answer)
            logger.info(f"Room: [{room.room_id}], Reply: [{answer}]")

        except Exception:
            logger.exception(f"Room: [{room.room_id}], Reply Failed")

    def on_new_reaction(self, reaction : str, message_ordinal : int, room : Chatroom):
        """Callback function to handle new reactions."""
        try:
            logger.info(f"Room: [{room.room_id}], Reaction: [{reaction}] on #{message_ordinal}")
            # Implement your agent logic here, e.g., respond to the reaction.
            room.post_messages(f"Thanks for your reaction: '{reaction}'")
        except Exception:
            logger.exception(f"Room: [{room.room_id}], Reaction Failed")

    @staticmethod
    def get_time():
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())


if __name__ == '__main__':
    demo_bot = Agent(BOT_USERNAME, BOT_PASSWORD)
    demo_bot.listen()