<div align="center">

# Python library for [Speakeasy](https://github.com/Alan-s-Speakeasy/speakeasy)

</div>

## Quick start
### 1. Install

```zsh
pip install -e .
```
### 2. Example Code
You can find a complete example in `usecases/demo_bot.py`.


## Getting started
### 1. Install

Recommended: Set up a venv
```zsh
python3 -m venv venv
source venv/bin/activate
```

Do actual installation
```zsh
pip install -e .
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

### 5. Example Code
You can find a complete example in `usecases/demo_bot.py`.



