import asyncio
import streamlit as st
import pandas as pd
import os
from telethon import TelegramClient
from dotenv import load_dotenv
load_dotenv()


API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")


SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

st.set_page_config(page_title="Telegram Utilization Dashboard")
st.title("📊 Telegram Utilization Dashboard")

# ---------- SINGLE LOOP ----------
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()

loop = st.session_state.loop

# ---------- STATE ----------
if "client" not in st.session_state:
    st.session_state.client = None
if "phone_hash" not in st.session_state:
    st.session_state.phone_hash = None
if "logged" not in st.session_state:
    st.session_state.logged = False

phone = st.text_input("Enter Telegram phone (with country code)")

def create_client(phone):
    session_path = os.path.join(SESSION_DIR, phone.replace("+",""))
    return TelegramClient(session_path, API_ID, API_HASH)

# ---------- ASYNC HELPERS ----------
async def connect(client):
    if not client.is_connected():
        await client.connect()

async def authorized(client):
    return await client.is_user_authorized()

async def send_code(client, phone):
    return await client.send_code_request(phone)

async def sign_in(client, phone, code, phone_hash):
    await client.sign_in(phone, code, phone_code_hash=phone_hash)

async def collect_data(client):
    rows = []
    async for dialog in client.iter_dialogs(limit=15):
        async for msg in client.iter_messages(dialog.id, limit=300):
            if msg.date:
                rows.append({
                    "chat": dialog.name,
                    "date": msg.date
                })
    return rows

# ---------- LOGIN ----------
if phone and not st.session_state.logged:

    if st.session_state.client is None:
        st.session_state.client = create_client(phone)

    client = st.session_state.client

    loop.run_until_complete(connect(client))

    is_auth = loop.run_until_complete(authorized(client))

    if not is_auth:

        if st.session_state.phone_hash is None:
            sent = loop.run_until_complete(send_code(client, phone))
            st.session_state.phone_hash = sent.phone_code_hash
            st.success("OTP sent to Telegram")

        code = st.text_input("Enter OTP")

        if code:
            loop.run_until_complete(
                sign_in(client, phone, code, st.session_state.phone_hash)
            )
            st.session_state.logged = True
            st.rerun()

    else:
        st.session_state.logged = True
        st.rerun()

# ---------- DASHBOARD ----------
if st.session_state.logged:

    client = st.session_state.client
    loop.run_until_complete(connect(client))

    st.subheader("📥 Loading Telegram activity...")

    rows = loop.run_until_complete(collect_data(client))

    if not rows:
        st.warning("No messages found")
    else:
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df["day"] = df["date"].dt.date
        df["hour"] = df["date"].dt.hour
        
        st.subheader("📅 Daily Activity")
        st.line_chart(df.groupby("day").size())

        st.subheader("💬 Number of Chats by Channels")
        st.bar_chart(df["chat"].value_counts().head(10))

        st.subheader("⏰ Number of Chats by  Hours (0 to 23 hr)")
        st.bar_chart(df.groupby("hour").size())




