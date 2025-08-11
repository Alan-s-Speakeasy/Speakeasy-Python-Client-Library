<div align="center">

# Python library for [Speakeasy](https://github.com/Alan-s-Speakeasy/speakeasy)

</div>



## Getting started
### 1. Install

```zsh
pip install git+https://github.com/Alan-s-Speakeasy/Speakeasy-Python-Client-Library
```

### 2. Initialize the Speakeasy Python framework and login

Please ensure that you are using the valid username and password of your bot.
```python
from speakeasypy import Speakeasy, EventType
speakeasy = Speakeasy(host='https://speakeasy.ifi.uzh.ch', username='name', password='pass')
speakeasy.login()  
```

### 3. Register callbacks for handling events

```python
# Register callbacks for different event types
speakeasy.register_callback(on_new_message, EventType.MESSAGE)
speakeasy.register_callback(on_new_reaction, EventType.REACTION)

# Define callback functions
def on_new_message(message, room):
    print(f"New message in room {room.room_id}: {message}")
    # Implement your agent logic here
    room.post_messages(f"Received your message: '{message}'")

def on_new_reaction(reaction, message_ordinal, room): 
    print(f"New reaction '{reaction}' on message #{message_ordinal} in room {room.room_id}")
    # Implement your agent logic here
    room.post_messages(f"Thanks for your reaction: '{reaction}'")
```

### 4. Start listening for events

```python
# This will start listening for events in the background
speakeasy.start_listening()
```

### 6. Example Code
You can find a complete example in `usecases/demo_bot.py`.

## Documentation for Relevant Classes

### Class Speakeasy
The `Speakeasy` class is the main entry point for `speakeasypy` library.

#### Methods
| Method      | Description                           | Parameters                                                                                                           | Returns                                                                   |
|-------------|---------------------------------------|----------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `login`     | Logs in to the Speakeasy platform.    | None                                                                                                                 | `str`: Session token.                                                     |
| `logout`    | Logs out from the Speakeasy platform. | None                                                                                                                 | None                                                                      |
| `get_rooms` | Retrieves a list of chat rooms.       | `active` (bool, optional): If `True`, returns active chat rooms (rooms with remaining time > 0). Defaults to `True`. | `List[Chatroom]`: A list of Chatroom objects representing the chat rooms. |


### Class Chatroom

#### Methods
| Method              | Description                                          | Parameters                                                                                                                                                                                                            | Returns                                                        |
|---------------------|------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| `get_messages`      | Retrieves chat messages from the chatroom.           | `only_partner` (bool, optional): If `True`, returns messages from the chat partner only. Defaults to `True`. <br> `only_new` (bool, optional): If `True`, returns only new, unprocessed messages. Defaults to `True`. | `List[RestChatMessage]`: A list of chat messages.              |
| `get_reactions`     | Retrieves reactions from the chatroom.               | `only_new` (bool, optional): If `True`, returns only new, unprocessed reactions. Defaults to `True`.                                                                                                                  | `List[ChatMessageReaction]`: A list of chat message reactions. |
| `post_messages`     | Posts a message to the chatroom.                     | `message` (str): The message to be posted.                                                                                                                                                                            | None                                                           |
| `mark_as_processed` | Marks a message or reaction as processed.            | `msg_or_rec` (RestChatMessage or ChatMessageReaction]): The message or reaction to mark as processed.                                                                                                                 | None                                                           |
| `get_chat_partner`  | Gets the alias of your chat partner in the chatroom. | None                                                                                                                                                                                                                  | `str`: The alias of your chat partner.                         |

#### Properties
| Property Name    | Description                                                                                             | Type        |
|------------------|---------------------------------------------------------------------------------------------------------|-------------|
| `room_id`        | A unique identifier for the chatroom.                                                                   | `str`       |
| `my_alias`       | The alias of this bot for the chatroom.                                                                 | `str`       |
| `prompt`         | The prompt associated with the chatroom.                                                                | `str`       |
| `start_time`     | The starting time of the chatroom.                                                                      | `int`       |
| `remaining_time` | The remaining time for the chatroom's activity.                                                         | `int`       |
| `user_aliases`   | A list of user aliases participating in the chatroom (generally including a chat partner and your bot). | `List[str]` |
| `initiated`      | A flag indicating whether a welcome message has been sent.                                              | `bool`      |
| `session_token`  | The session token associated with the chatroom.                                                         | `str`       |

### Class RestChatMessage
#### Properties
| Property Name  | Type  |
|----------------|-------|
| `time_stamp`   | `int` |
| `author_alias` | `str` |
| `ordinal`      | `int` |
| `message`      | `str` |

### Class ChatMessageReaction
#### Properties
| Property Name     | Type                                                        |
|-------------------|-------------------------------------------------------------|
| `message_ordinal` | `int`                                                       |
| `type`            | `str` (possible values: "THUMBS_UP", "THUMBS_DOWN", "STAR") |

## Development for this package
This pacakge `speakeasypy` depends on an internal package `speakeasypy.openapi.client` which is generated by openapi. 
Therefore, developers need to re-build this internal package if the openapi specification (inputSpec) changed.

Install `speakeasypy` locally:

The following command generates `egg` files instead of `whl`.
```shell
python setup.py install
````

Distribute `speakeasypy` and test it locally:

The following command generates the source code and a `whl` file, then you can test it.
```shell
python setup.py sdist bdist_wheel
pip install [local]/[path]/[to]/[your]/dist/speakeasypy_xxx.whl
```

Note: make sure you have installed `wheel` for development.
```shell
pip install wheel
```

