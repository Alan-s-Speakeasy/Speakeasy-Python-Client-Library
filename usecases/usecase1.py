from speakeasypy import Speakeasy, Chatroom
import time

DEFAULT_HOST_URL = 'http://127.0.0.1:8080'

test_username = 'bot1'
test_password = 'bot1'

speakeasy = Speakeasy(host=DEFAULT_HOST_URL, username=test_username, password=test_password)

speakeasy.login()

while True:
    # print('All rooms: ', speakeasy.get_rooms())
    # print('Active rooms: ', speakeasy.get_active_rooms())
    rooms = speakeasy.get_active_rooms()
    for room in rooms:
        print(f"-> room {room.room_id}:")
        messages = room.get_messages()
        reactions = room.get_reactions()

        print(f"\tmessages: {messages}")
        print(f"\treactions: {reactions}")
    time.sleep(2)


