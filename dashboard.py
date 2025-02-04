import streamlit as st
import pandas as pd
import plotly.express as px


def load_data(file):
    xl = pd.ExcelFile(file)
    sheet_names = xl.sheet_names
    data = {sheet: xl.parse(sheet) for sheet in sheet_names}
    return data, sheet_names


def preprocess_data(df):
    df = df.fillna(
        {
            "EmpID": 0,
            "FName": "Unknown",
            "Attendance Code": "N/A",
            "In Time": "00:00",
            "Out Time": "00:00",
            "Total Hours": 0,
            "OT Hours": 0,
            "Late Hours": 0,
            "Final Status": "Pending",
        }
    )
    df.dropna(inplace=True)
    return df


st.title("Employee Attendance Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xls", "xlsx"])

if uploaded_file:
    data, sheets = load_data(uploaded_file)
    sheet_selected = st.selectbox("Select Sheet", sheets)
    df = data[sheet_selected]
    df = preprocess_data(df)

    department_filter = st.selectbox(
        "Filter by Department", ["All"] +
        df["Department Name"].unique().tolist()
    )
    division_filter = st.selectbox(
        "Filter by Division", ["All"] + df["Division Name"].unique().tolist()
    )

    if department_filter != "All":
        df = df[df["Department Name"] == department_filter]
    if division_filter != "All":
        df = df[df["Division Name"] == division_filter]

    total_employees = df["EmpID"].nunique()
    present_count = df[df["Final Status"] == "P"]["EmpID"].count()
    absent_count = df[df["Final Status"] == "Absent"]["EmpID"].count()
    overtime_hours = df["OT Hours"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Employees", total_employees)
    col2.metric("Present Today", present_count)
    col3.metric("Absent Today", absent_count)
    col4.metric("Total Overtime Hours", overtime_hours)

    st.subheader("Attendance Summary")
    status_counts = df["Final Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    fig = px.bar(
        status_counts, x="Status", y="Count", title="Attendance Status Distribution"
    )
    st.plotly_chart(fig)

    st.subheader("Department-wise Attendance")
    dept_counts = df.groupby("Department Name")["EmpID"].count().reset_index()
    dept_counts.columns = ["Department", "Count"]
    fig2 = px.pie(
        dept_counts,
        names="Department",
        values="Count",
        title="Attendance by Department",
    )
    st.plotly_chart(fig2)

    st.subheader("Attendance Type Distribution")
    att_type_counts = df["Attendance Type"].value_counts().reset_index()
    att_type_counts.columns = ["Attendance Type", "Count"]
    fig3 = px.pie(
        att_type_counts,
        names="Attendance Type",
        values="Count",
        title="Attendance Type Distribution",
    )
    st.plotly_chart(fig3)

    st.subheader("Attendance Over Time")
    df["Attendance Date"] = pd.to_datetime(
        df["Attendance Date"], errors="coerce")
    df_time_series = df.groupby("Attendance Date")[
        "EmpID"].count().reset_index()
    df_time_series.columns = ["Date", "Count"]

    st.subheader("Detailed Data View")
    with st.expander("View Full Data"):
        st.dataframe(df)
