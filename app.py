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

sheet = client.open_by_key("191Fg2-jLtpvziqFrUdQNV2ki1iXYe_fdTGYv3_Tm7wA")

# ✅ FIXED HERE (no other changes)
try:
    pickup_sheet = sheet.worksheet("Pickup1")
except:
    pickup_sheet = sheet.get_worksheet(0)

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
    pg_name = st.text_input("PG Name")

    st.divider()

    choice = st.radio(
        "Do you need help reaching your PG?",
        ["Yes, I need pickup", "No, I will go myself"]
    )

    # PICKUP OPTION
    if choice == "Yes, I need pickup":

        pickup_point = st.selectbox(
            "Select Pickup Point",
            ["Railway Station", "Bus Stand", "Metro Station"]
        )

        if st.button("Confirm Pickup") and name and phone and pg_name:

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
            st.info("We will contact you on WhatsApp shortly")

    # SELF NAVIGATION
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

    headers = data[0]
    rows = data[1:]

    st.subheader("📦 Pickup Requests")

    for i in reversed(range(len(rows))):

        row_index = i + 2

        # SAFE DATA FIX
        o = {h.strip().lower(): v for h, v in zip(headers, rows[i])}

        name_val = o.get("name", "")
        phone_val = o.get("phone", "")
        pg_val = o.get("pg_name", "")
        point_val = o.get("pickup_point", "")
        status_val = o.get("status", "")
        driver_name = o.get("driver_name", "")
        driver_phone = o.get("driver_phone", "")

        # SHOW DATA
        st.write(f"👤 {name_val if name_val else 'No Name'} | 📞 {phone_val if phone_val else 'No Phone'}")
        st.write(f"🏠 {pg_val}")
        st.write(f"📍 {point_val}")

        if status_val == "Pending":
            st.warning("Pending")
        else:
            st.success("Assigned")

        col1, col2 = st.columns(2)

        # ASSIGN DRIVER
        if status_val == "Pending":

            if col1.button("🚖 Assign Driver", key=f"a{i}"):

                driver_name = "Ravi Kumar"
                driver_phone = "919876543210"

                try:
                    pickup_sheet.update(f"F{row_index}:H{row_index}", [[
                        "Assigned",
                        driver_name,
                        driver_phone
                    ]])
                    st.success("✅ Updated in Google Sheet")
                except Exception as e:
                    st.error(f"Update failed: {e}")

                msg = f"Hello {name_val}, your pickup is confirmed! Driver: {driver_name}, Phone: {driver_phone}"
                encoded_msg = urllib.parse.quote(msg)

                wa = f"https://wa.me/{phone_val}?text={encoded_msg}"

                st.markdown(f"[💬 Open WhatsApp]({wa})")

                st.rerun()

        # AFTER ASSIGNED
        else:

            msg = f"Hello {name_val}, your driver {driver_name} is on the way. Call: {driver_phone}"
            encoded_msg = urllib.parse.quote(msg)

            wa = f"https://wa.me/{phone_val}?text={encoded_msg}"

            st.markdown(f"[💬 Message Customer]({wa})")

        # CALL DRIVER
        if driver_phone:
            st.markdown(f"[📞 Call Driver](tel:{driver_phone})")

        st.divider()