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

sheet = client.open_by_key("1HS2e5d6MrAQ52gJ8b_99SmVKn_QohyEvslDcnkAo87s")

pickup_sheet = sheet.worksheet("Pickup1")
driver_sheet = sheet.worksheet("Drivers")

# PG DATA
pg_sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")
pg_data_sheet = pg_sheet.worksheet("Sheet1")

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
# USER
# =====================
elif st.session_state.page == "user":

    st.title("🚗 Request Pickup")

    name = st.text_input("Name")
    phone = st.text_input("Phone")

    # PG DROPDOWN
    pg_data = pg_data_sheet.get_all_records()
    pg_list = []

    for row in pg_data:
        val = row.get("pg_name") or row.get("name")
        if val:
            pg_list.append(val)

    pg = st.selectbox("PG Name", pg_list)

    point = st.selectbox("Pickup Point", ["Railway", "Bus", "Metro"])

    if st.button("Submit"):

        if not name or not phone:
            st.error("Fill details")
            st.stop()

        next_row = max(2, len(pickup_sheet.get_all_values()) + 1)

        pickup_sheet.insert_row([
            name, phone, pg, "Yes", point,
            "Pending", "", "", str(datetime.now())
        ], next_row)

        st.success("✅ Request Sent")

# =====================
# ADMIN
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

        next_row = max(2, len(driver_sheet.get_all_values()) + 1)

        driver_sheet.insert_row([d_name, d_phone, d_status, ""], next_row)

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

        if col1.button("Toggle Status", key=f"t{i}"):
            new_status = "Available" if d["status"] == "Busy" else "Busy"
            driver_sheet.update(f"C{i+2}:D{i+2}", [[new_status, ""]])
            st.rerun()

        if col2.button("Delete", key=f"d{i}"):
            driver_sheet.delete_rows(i+2)
            st.rerun()

    # REQUESTS
    st.subheader("📦 Requests")

    data = pickup_sheet.get_all_values()

    if len(data) <= 1:
        st.warning("No data")
        st.stop()

    rows = data[1:]

    for i in reversed(range(len(rows))):

        row = rows[i]
        row_index = i + 2

        name, phone, pg, _, point, status, d_name, d_phone = row[:8]

        st.markdown(f"### 👤 {name} | {phone}")
        st.write(f"{pg} | {point}")

        if status == "Pending":
            st.warning("Pending")
        elif status == "Assigned":
            st.success(f"Assigned → {d_name}")
        elif status == "Completed":
            st.info("Completed")

        col1, col2, col3 = st.columns(3)

        # ✅ MANUAL DRIVER SELECT
        if status == "Pending":

            drivers = driver_sheet.get_all_records()

            available_drivers = [
                f"{d['name']} | {d['phone']}"
                for d in drivers if d["status"] == "Available"
            ]

            if available_drivers:

                selected_driver = col1.selectbox(
                    "Select Driver",
                    available_drivers,
                    key=f"sel{i}"
                )

                if col1.button("🚗 Assign", key=f"a{i}"):

                    d_name_sel, d_phone_sel = selected_driver.split(" | ")

                    pickup_sheet.update(f"F{row_index}:H{row_index}", [[
                        "Assigned", d_name_sel, d_phone_sel
                    ]])

                    for idx, d in enumerate(drivers):
                        if str(d["phone"]) == d_phone_sel:
                            driver_sheet.update(f"C{idx+2}:D{idx+2}", [[
                                "Busy", name
                            ]])
                            break

                    st.success(f"Assigned {d_name_sel}")
                    st.rerun()

            else:
                st.error("No available drivers")

        # DELETE
        if col2.button("❌ Delete", key=f"dreq{i}"):
            pickup_sheet.delete_rows(row_index)
            st.rerun()

        # WHATSAPP
        clean_num = clean_phone(phone)
        msg = f"Hello {name}, your pickup is confirmed!"
        wa = f"https://wa.me/{clean_num}?text={urllib.parse.quote(msg)}"

        col3.link_button("💬 WhatsApp", wa)

        st.divider()

# =====================
# DRIVER APP
# =====================
elif st.session_state.page == "driver":

    st.title("🚗 Driver App")

    phone = st.text_input("Phone")

    if st.button("Login"):

        drivers = driver_sheet.get_all_records()
        driver = None

        input_phone = clean_phone(phone)

        for d in drivers:
            if clean_phone(d["phone"]) == input_phone:
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

            d_index = drivers.index(driver) + 2

            driver_sheet.update(f"C{d_index}:D{d_index}", [["Available", ""]])

            data = pickup_sheet.get_all_values()

            for i, r in enumerate(data[1:]):
                if r[0] == driver["current_ride"]:
                    pickup_sheet.update(f"F{i+2}", [["Completed"]])
                    break

            st.success("Completed")
            st.rerun()