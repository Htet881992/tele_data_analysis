from telethon.sync import TelegramClient
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()


API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")


@st.cache_resource
def get_client(session_file):
    return TelegramClient(session_file, API_ID, API_HASH)

client = get_client(session_file)

if not client.is_connected():
    client.connect()

rows = []

for dialog in client.iter_dialogs(limit=20):   # top 20 chats
    chat_name = dialog.name

    for msg in client.iter_messages(dialog.id, limit=500):
        if msg.date:
            rows.append({
                "chat": chat_name,
                "date": msg.date
            })

df = pd.DataFrame(rows)

df["date"] = pd.to_datetime(df["date"])
df["day"] = df["date"].dt.date
df["hour"] = df["date"].dt.hour

print(df.head())
print("Total messages:", len(df))