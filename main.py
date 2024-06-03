import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import os
import threading
import json
from PIL import Image, ImageDraw, ImageFont

# Load configurations
with open('config.json', 'r') as f:
    DATA = json.load(f)

def getenv(var):
    return os.environ.get(var) or DATA.get(var, None)

# Initialize Pyrogram clients
bot_token = getenv("TOKEN")
api_hash = getenv("HASH")
api_id = getenv("ID")
bot = Client("mybot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ss = getenv("STRING")
if ss is not None:
    acc = Client("myacc", api_id=api_id, api_hash=api_hash, session_string=ss)
    acc.start()
else:
    acc = None

# Function to add watermark to an image
def add_watermark(image_path, watermark_text):
    base = Image.open(image_path).convert('RGBA')
    width, height = base.size

    txt = Image.new('RGBA', base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt)

    font_size = width // 20
    font = ImageFont.truetype("arial.ttf", font_size)

    text_width, text_height = draw.textsize(watermark_text, font)
    position = (width - text_width - 10, height - text_height - 10)

    draw.text(position, watermark_text, fill=(255, 255, 255, 128), font=font)
    watermarked = Image.alpha_composite(base, txt)

    watermarked_path = "watermarked_thumbnail.png"
    watermarked.save(watermarked_path, "PNG")

    return watermarked_path

# Function to handle downloading status
def downstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
        time.sleep(3)
    
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Downloaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)

# Function to handle uploading status
def upstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
        time.sleep(3)
    
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Uploaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)

# Function to track progress
def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

# Function to get message type
def get_message_type(msg):
    try:
        msg.document.file_id
        return "Document"
    except: pass

    # Add other types of messages here as needed

# Start command
@bot.on_message(filters.command(["start"]))
def send_start(client, message):
    bot.send_message(
        message.chat.id, 
        f"**__👋 Hi** **{message.from_user.mention}**, **I am Save Restricted Bot, I can send you restricted content by its post link__**\n\n{USAGE}",
        reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("🌐 Update Channel", url="https://t.me/Electric_Hacker_Team")]]),
        reply_to_message_id=message.id
    )

# Save command
@bot.on_message(filters.text)
def save(client, message):
    # Joining chats
    if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:
        if acc is None:
            bot.send_message(message.chat.id, "**String Session is not Set**", reply_to_message_id=message.id)
            return

        try:
            acc.join_chat(message.text)
            bot.send_message(message.chat.id, "**Chat Joined**", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            bot.send_message(message.chat.id, "**Chat already Joined**", reply_to_message_id=message.id)
        except InviteHashExpired:
            bot.send_message(message.chat.id, "**Invalid Link**", reply_to_message_id=message.id)
        except Exception as e:
            bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

    # Getting message
    elif "https://t.me/" in message.text:
        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except:
            toID = fromID

        for msgid in range(fromID, toID + 1):
            # Private
            if "https://t.me/c/" in message.text:
                chatid = int("-100" + datas[4])

                if acc is None:
                    bot.send_message(message.chat.id, "**String Session is not Set**", reply_to_message_id=message.id)
                    return

                handle_private(message, chatid, msgid)
            
            # Bot
            elif "https://t.me/b/" in message.text:
                username = datas[4]

                if acc is None:
                    bot.send_message(message.chat.id, "**String Session is not Set**", reply_to_message_id=message.id)
                    return
                try:
                    handle_private(message, username, msgid)
                except Exception as e:
                    bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

            # Public
            else:
                username = datas[3]

                try:
                    msg = bot.get_messages(username, msgid)
                except UsernameNotOccupied:
                    bot.send_message(message.chat.id, "**The username is not occupied by anyone**", reply_to_message_id=message.id)
                    return

                try:
                    handle_public(message, msg)
                except Exception as e:
                    bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

            time.sleep(3)

# Handle private messages
def handle_private(message, chatid, msgid):
    msg = acc.get_messages(chatid, msgid)
    msg_type = get_message_type(msg)
    new_caption = (msg.caption or "") + " [Electric Hacker]"

    if msg_type == "Document":
        file = acc.download_media(msg, progress=progress)

        # Add watermark to thumbnail
        watermarked_thumbnail = add_watermark(file, "Electric Hacker")

        bot.send_document(
            message.chat.id, 
            file, 
            thumb=watermarked_thumbnail,
            caption=new_caption
        )

USAGE = """**FOR PUBLIC CHATS**

**__just send post/s link__**

**FOR PRIVATE CHATS**

**__first send invite link of the chat (unnecessary if the account of string session already member of the chat)
then send post/s link__**

**FOR BOT CHATS**

**__send link with** '/b/', **bot's username and message id, you might want to install some unofficial client to get the id like below__**

```
https://t.me/b/botusername/4321
```

**MULTI POSTS**

**__send public/private posts link as explained above with formate "from - to" to send multiple messages like below__**

```
https://t.me/xxxx/1001-1010

https://t.me/c/xxxx/101 - 120
```

**__note that space in between doesn't matter__**
"""


# infinty polling
bot.run()
