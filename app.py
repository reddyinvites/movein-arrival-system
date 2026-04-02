import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import urllib.parse
import time

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------
# GOOGLE SHEETS SETUP
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
    return gspread.authorize(creds)

client = get_client()

# -----------------------
# SAFE SHEET OPEN (RETRY)
# -----------------------
def open_sheet_safe(sheet_id, sheet_name, retries=3):
    for attempt in range(retries):
        try:
            sh = client.open_by_key(sheet_id)
            return sh.worksheet(sheet_name)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                st.error(f"❌ Sheet error: {sheet_name}")
                st.write(str(e))
                st.stop()

# -----------------------
# SHEET IDS
# -----------------------
MAIN_SHEET_ID = "1HS2e5d6MrAQ52gJ8b_99SmVKn_QohyEvslDcnkAo87s"
PG_SHEET_ID = "1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q"

pickup_sheet = open_sheet_safe(MAIN_SHEET_ID, "Pickup1")
driver_sheet = open_sheet_safe(MAIN_SHEET_ID, "Drivers")
pg_data_sheet = open_sheet_safe(PG_SHEET_ID, "Sheet1")

# -----------------------
# PHONE CLEAN
# -----------------------
def clean_phone(phone):
    p = str(phone).replace("+", "").replace(" ", "").strip()
    if p.startswith("0"):
        p = "91" + p[1:]
    elif not p.startswith("91"):
        p = "91" + p
    return p

# =====================
# HOME
# =====================
if st.session_state.page == "home":

    st.title("🏠 Move-in Support")

    if st.button("👤 User"):
        st.session_state.page = "user"
        st.rerun()

    if st.button("🚗 Admin"):
        st.session_state.page = "admin"
        st.rerun()

    if st.button("🚗 Driver"):
        st.session_state.page = "driver"
        st.rerun()

# =====================
# USER PAGE
# =====================
elif st.session_state.page == "user":

    st.title("🚗 Request Pickup")

    name = st.text_input("Name")
    phone = st.text_input("Phone")

    pg_data = pg_data_sheet.get_all_records()
    pg_list = [row.get("pg_name") for row in pg_data if row.get("pg_name")]

    pg = st.selectbox("PG Name", pg_list)

    point = st.selectbox("Pickup Point", ["Railway", "Bus", "Metro"])

    if st.button("Submit"):

        if not name or not phone:
            st.error("Fill details")
            st.stop()

        pickup_sheet.append_row([
            name, phone, pg, "Yes", point,
            "Pending", "", "", str(datetime.now())
        ])

        st.success("✅ Request Sent")

# =====================
# ADMIN PAGE
# =====================
elif st.session_state.page == "admin":

    st.title("🚗 Admin Dashboard")

    if st.text_input("Password", type="password") != "1234":
        st.stop()

    # ADD DRIVER
    st.subheader("➕ Add Driver")

    d_name = st.text_input("Driver Name")
    d_phone = clean_phone(st.text_input("Driver Phone"))
    d_status = st.selectbox("Status", ["Available", "Busy"])

    if st.button("Add Driver"):

        drivers = driver_sheet.get_all_records()

        for d in drivers:
            if str(d["phone"]) == d_phone:
                st.error("Driver exists")
                st.stop()

        driver_sheet.append_row([d_name, d_phone, d_status, ""])
        st.success("Driver Added")
        st.rerun()

    # DRIVER LIST
    st.subheader("👨‍✈️ Drivers")

    drivers = driver_sheet.get_all_records()

    for i, d in enumerate(drivers):

        st.markdown(f"### 🚗 {d['name']} | {d['phone']}")

        if d["status"] == "Available":
            st.success("Available")
        else:
            st.warning(f"Busy → {d['current_ride']}")

        col1, col2 = st.columns(2)

        if col1.button("Toggle Status", key=f"toggle_{i}"):
            new_status = "Available" if d["status"] == "Busy" else "Busy"
            driver_sheet.update(f"C{i+2}:D{i+2}", [[new_status, ""]])
            st.rerun()

        if col2.button("Delete", key=f"delete_driver_{i}"):
            driver_sheet.delete_rows(i+2)
            st.rerun()

    # REQUESTS
    st.subheader("📦 Requests")

    data = pickup_sheet.get_all_values()

    if len(data) <= 1:
        st.warning("No requests")
        st.stop()

    rows = data[1:]

    for i in reversed(range(len(rows))):

        row = rows[i]
        row_index = i + 2

        name, phone, pg, _, point, status, d_name, d_phone = row[:8]

        st.markdown(f"### 👤 {name} | {phone}")
        st.write(f"{pg} | {point}")

        if status == "Assigned":
            st.success(f"Assigned → {d_name}")
        elif status == "Completed":
            st.info("Completed")
        else:
            st.warning("Pending")

        col1, col2, col3 = st.columns(3)

        # MANUAL ASSIGN
        if status != "Completed":

            drivers = driver_sheet.get_all_records()

            available = [
                f"{d['name']} | {d['phone']}"
                for d in drivers if d["status"] == "Available"
            ]

            if available:

                selected = col1.selectbox(
                    "Select Driver",
                    available,
                    key=f"select_{row_index}"
                )

                if col1.button("🚗 Assign", key=f"assign_{row_index}"):

                    new_name, new_phone = selected.split(" | ")

                    # FREE OLD DRIVER
                    for idx, d in enumerate(drivers):
                        if str(d["phone"]) == str(d_phone):
                            driver_sheet.update(f"C{idx+2}:D{idx+2}", [["Available", ""]])

                    # ASSIGN NEW
                    pickup_sheet.update(f"F{row_index}:H{row_index}", [[
                        "Assigned", new_name, new_phone
                    ]])

                    for idx, d in enumerate(drivers):
                        if str(d["phone"]) == new_phone:
                            driver_sheet.update(f"C{idx+2}:D{idx+2}", [["Busy", name]])

                    st.success(f"Assigned {new_name}")
                    st.rerun()

        # DELETE REQUEST
        if col2.button("❌ Delete", key=f"delete_req_{row_index}"):
            pickup_sheet.delete_rows(row_index)
            st.rerun()

        # WHATSAPP
        wa = f"https://wa.me/{clean_phone(phone)}?text={urllib.parse.quote('Pickup confirmed')}"
        col3.link_button("💬 WhatsApp", wa, key=f"wa_{row_index}")

        st.divider()

# =====================
# DRIVER PAGE
# =====================
elif st.session_state.page == "driver":

    st.title("🚗 Driver App")

    phone = st.text_input("Phone")

    if st.button("Login"):

        drivers = driver_sheet.get_all_records()
        driver = None

        for d in drivers:
            if clean_phone(d["phone"]) == clean_phone(phone):
                driver = d
                break

        if not driver:
            st.error("Not found")
            st.stop()

        st.success(driver["name"])

        if driver["status"] == "Available":
            st.info("No ride")
            st.stop()

        st.warning("Ride Assigned")
        st.write(driver["current_ride"])

        if st.button("Complete Ride"):

            idx = drivers.index(driver) + 2
            driver_sheet.update(f"C{idx}:D{idx}", [["Available", ""]])

            data = pickup_sheet.get_all_values()

            for i, r in enumerate(data[1:]):
                if r[0] == driver["current_ride"]:
                    pickup_sheet.update(f"F{i+2}", [["Completed"]])
                    break

            st.success("Completed")
            st.rerun()