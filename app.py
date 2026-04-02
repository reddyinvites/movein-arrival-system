import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import urllib.parse

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------
# GOOGLE SHEETS
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

# -----------------------
# PICKUP SHEET
# -----------------------
sheet = client.open_by_key("191Fg2-jLtpvziqFrUdQNV2ki1iXYe_fdTGYv3_Tm7wA")

try:
    pickup_sheet = sheet.worksheet("Pickup1")
except:
    pickup_sheet = sheet.get_worksheet(0)

# -----------------------
# PG DATA SHEET
# -----------------------
pg_sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")

try:
    pg_data_sheet = pg_sheet.worksheet("Sheet1")
except:
    pg_data_sheet = pg_sheet.get_worksheet(0)

pg_data = pg_data_sheet.get_all_records()

pg_list = []
for row in pg_data:
    name = row.get("pg_name") or row.get("name") or ""
    if name and name not in pg_list:
        pg_list.append(name)

# =====================
# HOME
# =====================
if st.session_state.page == "home":

    st.title("🏠 Move-in Support")

    col1, col2 = st.columns(2)

    if col1.button("👤 User"):
        st.session_state.page = "user"
        st.rerun()

    if col2.button("🚗 Pickup Admin"):
        st.session_state.page = "admin"
        st.rerun()

# =====================
# USER PAGE
# =====================
elif st.session_state.page == "user":

    st.title("🚗 Arrival & Pickup Assistance")

    name = st.text_input("Your Name")
    phone = st.text_input("Phone Number")
    pg_name = st.selectbox("PG Name", pg_list)

    st.divider()

    choice = st.radio(
        "Do you need help reaching your PG?",
        ["Yes, I need pickup", "No, I will go myself"]
    )

    if choice == "Yes, I need pickup":

        pickup_point = st.selectbox(
            "Select Pickup Point",
            ["Railway Station", "Bus Stand", "Metro Station"]
        )

        if st.button("Confirm Pickup"):

            if not name or not phone or not pg_name:
                st.error("⚠️ Please fill all details")
                st.stop()

            try:
                pickup_sheet.append_row([
                    str(name),
                    str(phone),
                    str(pg_name),
                    "Yes",
                    str(pickup_point),
                    "Pending",
                    "",
                    "",
                    str(datetime.now())
                ])

                st.success("✅ Saved to Google Sheet")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Save failed: {e}")

    else:

        st.subheader("🧭 Self Navigation")

        st.markdown("[📍 Open Google Maps](https://maps.google.com)")
        st.video("https://res.cloudinary.com/demo/video/upload/sample.mp4")

        st.write("""
        📌 Directions:
        1. Exit main road  
        2. Take left  
        3. Walk 100 meters  
        4. PG on right  
        """)

        st.success("Easy to reach 👍")

# =====================
# ADMIN PANEL
# =====================
elif st.session_state.page == "admin":

    st.title("🚗 Pickup Admin Dashboard")

    password = st.text_input("Password", type="password")

    if password != "1234":
        st.stop()

    st.success("Logged in")

    if st.button("🚪 Logout"):
        st.session_state.page = "home"
        st.rerun()

    st.divider()

    data = pickup_sheet.get_all_values()

    if len(data) <= 1:
        st.info("No requests yet")
        st.stop()

    rows = data[1:]

    st.subheader("📦 Pickup Requests")

    for i in reversed(range(len(rows))):

        row_index = i + 2

        # DIRECT MAPPING (FIXED)
        row = rows[i]

        name_val = row[0] if len(row) > 0 else ""
        phone_val = row[1] if len(row) > 1 else ""
        pg_val = row[2] if len(row) > 2 else ""
        point_val = row[4] if len(row) > 4 else ""
        status_val = row[5] if len(row) > 5 else "Pending"
        driver_name = row[6] if len(row) > 6 else ""
        driver_phone = row[7] if len(row) > 7 else ""

        # DISPLAY
        st.markdown(f"### 👤 {name_val} | 📞 {phone_val}")
        st.markdown(f"🏠 **{pg_val}**")
        st.markdown(f"📍 {point_val}")

        if status_val == "Pending":
            st.warning("⏳ Pending")
        else:
            st.success("✅ Assigned")

        col1, col2 = st.columns(2)

        # ASSIGN DRIVER
        if status_val != "Assigned":
            if col1.button("✅ Assign", key=f"a{i}"):

                driver_name = "Ravi Kumar"
                driver_phone = "919876543210"

                pickup_sheet.update(f"F{row_index}:H{row_index}", [[
                    "Assigned",
                    driver_name,
                    driver_phone
                ]])

                st.success("Driver Assigned 🚗")
                st.rerun()

        # WHATSAPP
        msg = f"Hello {name_val}, your pickup is confirmed!"
        encoded_msg = urllib.parse.quote(msg)
        wa = f"https://wa.me/{phone_val}?text={encoded_msg}"

        col2.markdown(f"[💬 WhatsApp]({wa})")

        # CALL DRIVER
        if driver_phone:
            st.markdown(f"[📞 Call Driver](tel:{driver_phone})")

        st.divider()