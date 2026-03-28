import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.title("🚗 Arrival & Pickup Assistance")

# -----------------------
# GOOGLE SHEETS CONNECT
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

# 👉 YOUR SHEET ID
sheet = client.open_by_key("191Fg2-jLtpvziqFrUdQNV2ki1iXYe_fdTGYv3_Tm7wA")

# ✅ FIX HERE (Sheet1)
pickup_sheet = sheet.worksheet("Sheet1")

# -----------------------
# USER INPUT
# -----------------------
name = st.text_input("Your Name")
phone = st.text_input("Phone Number")
pg_name = st.text_input("PG Name")

st.divider()

choice = st.radio(
    "Do you need help reaching your PG?",
    ["Yes, I need pickup", "No, I will go myself"]
)

# -----------------------
# PICKUP OPTION
# -----------------------
if choice == "Yes, I need pickup":

    pickup_point = st.selectbox(
        "Select Pickup Point",
        ["Railway Station", "Bus Stand", "Metro Station"]
    )

    if st.button("Confirm Pickup"):

        pickup_sheet.append_row([
            name,
            phone,
            pg_name,
            "Yes",
            pickup_point,
            "Pending",
            "",
            "",
            str(datetime.now())
        ])

        st.success("🚖 Pickup request submitted!")

# -----------------------
# SELF NAVIGATION
# -----------------------
else:

    st.subheader("🧭 Self Navigation")

    st.markdown("[📍 Open Google Maps](https://maps.google.com)")

    st.video("https://res.cloudinary.com/demo/video/upload/sample.mp4")

    st.write("""
    📌 Directions:
    1. Exit main road  
    2. Take left at signal  
    3. Walk 100 meters  
    4. PG on right side  
    """)

    st.success("You can reach easily 👍")