import streamlit as st
import pandas as pd
import sqlite3
from streamlit_option_menu import option_menu
from auth import login_user, hash_password
from utils import (
    create_user_auto,
    get_mapped_employees,
    insert_attendance_from_csv,
    get_attendance
)

st.set_page_config(page_title="Employee Dashboard", layout="wide")
st.title("📊 Employee Attendance & Performance Dashboard")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.name = None
    st.session_state.emp_id = None

if not st.session_state.logged_in:
    st.sidebar.title("Login")
    emp_id = st.sidebar.text_input("Employee ID")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        success, role, name = login_user(emp_id, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.session_state.name = name
            st.session_state.emp_id = emp_id
            st.rerun()
        else:
            st.error("Invalid login credentials")
else:
    st.sidebar.title(f"Logged in as: {st.session_state.name} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.name = None
        st.session_state.emp_id = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.number_input("Refresh Interval (seconds)", min_value=0, max_value=60, step=1, key="refresh_interval")
    if st.sidebar.button("🔄 Refresh Dashboard"):
        st.rerun()

    def show_attendance_insights(df):
        with st.expander("📅 Filter Attendance Data by Month & Year"):
            df["log_in_date"] = pd.to_datetime(df["log_in_date"])
            years = sorted(df['log_in_date'].dt.year.unique())
            months = sorted(df['log_in_date'].dt.month.unique())
            selected_year = st.selectbox("Select Year", years)
            selected_month = st.selectbox("Select Month", months)
            df = df[(df['log_in_date'].dt.year == selected_year) & (df['log_in_date'].dt.month == selected_month)]

        st.write("### Attendance Insights")
        df["log_in_datetime"] = pd.to_datetime(df["log_in_date"].dt.strftime("%Y-%m-%d") + " " + df["log_in_time"])
        df["log_out_datetime"] = pd.to_datetime(df["log_out_date"] + " " + df["log_out_time"])
        df["hours_worked"] = (df["log_out_datetime"] - df["log_in_datetime"]).dt.total_seconds() / 3600

        late_threshold = 9
        underutilized_threshold = 6
        overworked_threshold = 9

        late_days = df[df["log_in_datetime"].dt.hour > late_threshold].shape[0]
        underutilized_days = df[df["hours_worked"] < underutilized_threshold].shape[0]
        overworked_days = df[df["hours_worked"] > overworked_threshold].shape[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⏰ Late Arrivals", late_days)
        with col2:
            st.metric("📉 Underutilized Days", underutilized_days)
        with col3:
            st.metric("📈 Overworked Days", overworked_days)

        st.write("#### 📊 Daily Work Hours")
        st.bar_chart(df.set_index(df["log_in_date"].dt.strftime("%Y-%m-%d"))["hours_worked"])

        return df

    if st.session_state.role == "Admin":
        with st.sidebar:
            admin_menu = option_menu("Admin Menu", ["Create HR"])
        if admin_menu == "Create HR":
            st.subheader("Create HR User")
            name = st.text_input("Name")
            pw = st.text_input("Password", type="password")
            if st.button("Create HR"):
                hashed = hash_password(pw)
                emp_id = create_user_auto(name, hashed, "HR")
                st.success(f"HR User Created with Employee ID: {emp_id}")

    elif st.session_state.role == "HR":
        with st.sidebar:
            hr_menu = option_menu("HR Menu", ["Upload CSV", "Create User", "Update Manager Mapping"])

        if hr_menu == "Upload CSV":
            file = st.file_uploader("Upload Attendance CSV", type=["csv"])
            if file:
                insert_attendance_from_csv(file)
                st.success("Attendance uploaded")

        elif hr_menu == "Create User":
            st.subheader("Create New User")
            name = st.text_input("Name")
            pw = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Employee", "Manager", "HR"])
            manager = st.text_input("Manager ID (optional)", "")
            if st.button("Create"):
                hashed = hash_password(pw)
                emp_id = create_user_auto(name, hashed, role, manager or None)
                st.success(f"{role} User Created with Employee ID: {emp_id}")

        elif hr_menu == "Update Manager Mapping":
            st.subheader("Update Manager Mapping")
            conn = sqlite3.connect("data/database.db")
            c = conn.cursor()
            c.execute("SELECT employee_id, name, manager_id FROM users WHERE role != 'Admin'")
            users = c.fetchall()
            conn.close()

            user_dict = {f"{u[0]} - {u[1]}": u for u in users}
            selected_user = st.selectbox("Select Employee", list(user_dict.keys()))
            current_manager = user_dict[selected_user][2] or ""
            new_manager = st.text_input("New Manager ID", value=current_manager)

            if st.button("Update Mapping"):
                emp_id = user_dict[selected_user][0]
                if new_manager:
                    conn = sqlite3.connect("data/database.db")
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM users WHERE employee_id = ?", (new_manager,))
                    exists = c.fetchone()[0]
                    conn.close()
                    if exists == 0:
                        st.error("❌ Manager ID does not exist.")
                    else:
                        conn = sqlite3.connect("data/database.db")
                        c = conn.cursor()
                        c.execute("UPDATE users SET manager_id = ? WHERE employee_id = ?", (new_manager, emp_id))
                        conn.commit()
                        conn.close()
                        st.success("✅ Manager mapping updated.")
                else:
                    conn = sqlite3.connect("data/database.db")
                    c = conn.cursor()
                    c.execute("UPDATE users SET manager_id = NULL WHERE employee_id = ?", (emp_id,))
                    conn.commit()
                    conn.close()
                    st.success("✅ Manager mapping cleared.")

    elif st.session_state.role == "Manager":
        st.sidebar.subheader("Mapped Employees")
        conn = sqlite3.connect("data/database.db")
        c = conn.cursor()
        c.execute("SELECT employee_id, name, role FROM users WHERE manager_id = ?", (st.session_state.emp_id,))
        rows = c.fetchall()
        conn.close()
        emp_list = [f"{emp[0]} - {emp[1]} ({emp[2]})" for emp in rows]

        selected = st.sidebar.selectbox("Select Employee", emp_list)
        if selected:
            emp_id = selected.split(" - ")[0]
            df = get_attendance(emp_id)
            st.subheader(f"Attendance for {selected}")
            if not df.empty:
                df_filtered = show_attendance_insights(df)
                st.write("### Attendance Table")
                st.dataframe(df_filtered)

        with st.expander("📄 View My Own Attendance"):
            self_df = get_attendance(st.session_state.emp_id)
            if not self_df.empty:
                df_filtered = show_attendance_insights(self_df)
                st.write("### Your Attendance Table")
                st.dataframe(df_filtered)

    elif st.session_state.role == "Employee":
        st.subheader("Your Attendance")
        df = get_attendance(st.session_state.emp_id)
        if not df.empty:
            df_filtered = show_attendance_insights(df)
            st.write("### Attendance Table")
            st.dataframe(df_filtered)
