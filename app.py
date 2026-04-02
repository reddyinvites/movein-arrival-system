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
# MAIN SHEET
# -----------------------
sheet = client.open_by_key("1HS2e5d6MrAQ52gJ8b_99SmVKn_QohyEvslDcnkAo87s")

pickup_sheet = sheet.worksheet("Pickup1")
driver_sheet = sheet.worksheet("Drivers")

# -----------------------
# PG DATA
# -----------------------
pg_sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")
pg_data_sheet = pg_sheet.worksheet("Sheet1")
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

    if st.button("👤 User"):
        st.session_state.page = "user"
        st.rerun()

    if st.button("🚗 Pickup Admin"):
        st.session_state.page = "admin"
        st.rerun()

    if st.button("🚗 Driver Login"):
        st.session_state.page = "driver"
        st.rerun()

# =====================
# USER PAGE
# =====================
elif st.session_state.page == "user":

    st.title("🚗 Arrival & Pickup Assistance")

    name = st.text_input("Your Name")
    phone = st.text_input("Phone Number")
    pg_name = st.selectbox("PG Name", pg_list)

    choice = st.radio(
        "Need pickup?",
        ["Yes, I need pickup", "No, I will go myself"]
    )

    if choice == "Yes, I need pickup":

        pickup_point = st.selectbox(
            "Pickup Point",
            ["Railway Station", "Bus Stand", "Metro Station"]
        )

        if st.button("Confirm Pickup"):

            if not name or not phone:
                st.error("Fill all details")
                st.stop()

            next_row = max(2, len(pickup_sheet.get_all_values()) + 1)

            pickup_sheet.insert_row([
                name,
                phone,
                pg_name,
                "Yes",
                pickup_point,
                "Pending",
                "",
                "",
                str(datetime.now())
            ], next_row)

            st.success("✅ Request Submitted")

# =====================
# ADMIN PAGE
# =====================
elif st.session_state.page == "admin":

    st.title("🚗 Admin Dashboard")

    if st.text_input("Password", type="password") != "1234":
        st.stop()

    data = pickup_sheet.get_all_values()

    if len(data) <= 1:
        st.warning("No requests")
        st.stop()

    rows = data[1:]
    drivers = driver_sheet.get_all_records()

    for i in reversed(range(len(rows))):

        row_index = i + 2
        row = rows[i]

        name = row[0]
        phone = row[1]
        pg = row[2]
        point = row[4]
        status = row[5]
        driver_name = row[6]
        driver_phone = row[7]

        st.markdown(f"### 👤 {name} | 📞 {phone}")
        st.write(f"🏠 {pg}")
        st.write(f"📍 {point}")

        if status == "Pending":
            st.warning("Pending")
        elif status == "Completed":
            st.success("Completed")
        else:
            st.success(f"Assigned: {driver_name}")

        col1, col2 = st.columns(2)

        # ASSIGN DRIVER
        if status == "Pending":

            if col1.button("🚗 Assign", key=f"a{i}"):

                available_driver = None

                for d in drivers:
                    if d["status"] == "Available":
                        available_driver = d
                        break

                if not available_driver:
                    st.error("❌ No drivers available")

                else:
                    driver_name = available_driver["name"]
                    driver_phone = available_driver["phone"]

                    pickup_sheet.update(f"F{row_index}:H{row_index}", [[
                        "Assigned",
                        driver_name,
                        driver_phone
                    ]])

                    d_index = drivers.index(available_driver) + 2

                    driver_sheet.update(f"C{d_index}:D{d_index}", [[
                        "Busy",
                        name
                    ]])

                    st.success(f"Assigned {driver_name}")
                    st.rerun()

        # WHATSAPP BUTTON
        msg = f"Hello {name}, your pickup is confirmed!"
        wa = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"

        if col2.button("💬 WhatsApp", key=f"w{i}"):
            st.markdown(
                f"<script>window.open('{wa}', '_blank');</script>",
                unsafe_allow_html=True
            )

        if driver_phone:
            st.markdown(f"[📞 Call Driver](tel:{driver_phone})")

        st.divider()

# =====================
# DRIVER APP
# =====================
elif st.session_state.page == "driver":

    st.title("🚗 Driver App")

    phone = st.text_input("Enter Phone Number")

    if st.button("Login"):

        drivers = driver_sheet.get_all_records()

        driver = None
        for d in drivers:
            if d["phone"] == phone:
                driver = d
                break

        if not driver:
            st.error("Driver not found")
            st.stop()

        st.success(f"Welcome {driver['name']}")

        if driver["status"] == "Available":
            st.info("No ride assigned")
            st.stop()

        st.warning("🚨 Ride Assigned")
        st.write("Customer:", driver["current_ride"])

        if st.button("✅ Complete Ride"):

            d_index = drivers.index(driver) + 2

            # Set driver available
            driver_sheet.update(f"C{d_index}:D{d_index}", [[
                "Available",
                ""
            ]])

            # Update pickup sheet
            pickup_data = pickup_sheet.get_all_values()

            for i, r in enumerate(pickup_data[1:]):
                if r[0] == driver["current_ride"]:
                    pickup_sheet.update(f"F{i+2}", [["Completed"]])
                    break

            st.success("🎉 Ride Completed")
            st.rerun()