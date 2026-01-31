import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

import streamlit as st
from telethon.sync import TelegramClient
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()


API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")


# Make sure sessions folder exists
os.makedirs("sessions", exist_ok=True)

st.title("📊 Telegram Utilization Dashboard")

@st.cache_resource
def get_client(session_file):
    return TelegramClient(session_file, API_ID, API_HASH)

phone = st.text_input("Enter your Telegram phone number (with country code)")

if phone:
    session_file = f"sessions/{phone.replace('+','')}"
    client = get_client(session_file)

    if not client.is_connected():
        client.connect()

    if not os.path.exists(session_file + ".session"):
        st.info("Sending OTP to Telegram...")
        client.send_code_request(phone)

        code = st.text_input("Enter OTP sent to Telegram")

        if code:
            try:
                client.sign_in(phone, code)
                st.success("Logged in successfully!")
            except Exception as e:
                st.error(f"Login failed: {e}")

    if client.is_user_authorized():

        st.success("Connected to Telegram")

        rows = []

        for dialog in client.iter_dialogs(limit=20):
            for msg in client.iter_messages(dialog.id, limit=500):
                if msg.date:
                    rows.append({
                        "chat": dialog.name,
                        "date": msg.date
                    })

        if rows:
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            df["day"] = df["date"].dt.date
            df["hour"] = df["date"].dt.hour

            st.subheader("📅 Daily Activity")
            st.line_chart(df.groupby("day").size())

            st.subheader("💬 Top Chats")
            st.bar_chart(df["chat"].value_counts().head(10))

            st.subheader("⏰ Hourly Usage")
            st.bar_chart(df.groupby("hour").size())
        else:
            st.warning("No messages found yet.")