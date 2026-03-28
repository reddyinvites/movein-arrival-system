import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------
# SESSION INIT
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

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

sheet = client.open_by_key("191Fg2-jLtpvziqFrUdQNV2ki1iXYe_fdTGYv3_Tm7wA")

# ✅ Sheet1 used
pickup_sheet = sheet.worksheet("Sheet1")

# =====================
# HOME
# =====================
if st.session_state.page == "home":

    st.title("🏠 Move-in Support System")

    col1, col2 = st.columns(2)

    if col1.button("👤 User"):
        st.session_state.page = "user"
        st.rerun()

    if col2.button("🚗 Pickup Admin"):
        st.session_state.page = "pickup_admin"
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
            st.info("Our team will contact you shortly on WhatsApp")

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

# =====================
# ADMIN PANEL
# =====================
elif st.session_state.page == "pickup_admin":

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
        st.info("No pickup requests yet")
        st.stop()

    headers = data[0]
    rows = data[1:]

    st.subheader("📦 Pickup Requests")

    for i in reversed(range(len(rows))):

        row_index = i + 2
        o = dict(zip(headers, rows[i]))

        st.write(f"👤 {o['name']} | 📞 {o['phone']}")
        st.write(f"🏠 {o['pg_name']}")
        st.write(f"📍 {o['pickup_point']}")

        # STATUS
        if o["status"] == "Pending":
            st.warning("Pending")
        else:
            st.success("Assigned")

        col1, col2 = st.columns(2)

        # -----------------------
        # ASSIGN DRIVER
        # -----------------------
        if o["status"] == "Pending":

            if col1.button("🚖 Assign Driver", key=f"a{i}"):

                driver_name = "Ravi Kumar"
                driver_phone = "919876543210"

                pickup_sheet.update_cell(row_index, 6, "Assigned")
                pickup_sheet.update_cell(row_index, 7, driver_name)
                pickup_sheet.update_cell(row_index, 8, driver_phone)

                msg = f"Hello {o['name']}, your pickup is confirmed! Driver: {driver_name}, Phone: {driver_phone}"

                wa = f"https://wa.me/{o['phone']}?text={msg.replace(' ','%20')}"

                st.markdown(f"[💬 Send WhatsApp]({wa})")

                st.success("Driver Assigned!")
                st.rerun()

        # -----------------------
        # WHATSAPP AFTER ASSIGNED
        # -----------------------
        else:

            msg = f"Hello {o['name']}, your driver {o['driver_name']} is on the way. Call: {o['driver_phone']}"

            wa = f"https://wa.me/{o['phone']}?text={msg.replace(' ','%20')}"

            st.markdown(f"[💬 Message Customer]({wa})")

        # -----------------------
        # CALL DRIVER
        # -----------------------
        if o["driver_phone"]:
            st.markdown(f"[📞 Call Driver](tel:{o['driver_phone']})")

        st.divider()