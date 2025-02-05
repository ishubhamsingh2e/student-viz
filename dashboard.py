import streamlit as st
import pandas as pd
import plotly.express as px


# Load data from Excel
def load_data(file):
    xl = pd.ExcelFile(file)
    sheet_names = xl.sheet_names
    data = {sheet: xl.parse(sheet) for sheet in sheet_names}
    return data, sheet_names


# Preprocess data
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


st.set_page_config(layout="wide")
st.title("Employee Attendance Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xls", "xlsx"])

if uploaded_file:
    data, sheets = load_data(uploaded_file)

    # Dashboard Selection
    dashboard_option = st.sidebar.radio(
        "Select Dashboard",
        ["Sheet-wise", "All Sheets Summary", "Employee-Level Statistics"],
    )

    if dashboard_option == "Sheet-wise":
        sheet_selected = st.selectbox("Select Sheet", sheets)
        df = data[sheet_selected]
        df = preprocess_data(df)

    elif dashboard_option == "All Sheets Summary":
        df = pd.concat([preprocess_data(data[sheet]) for sheet in sheets])

    elif dashboard_option == "Employee-Level Statistics":
        df = pd.concat([preprocess_data(data[sheet]) for sheet in sheets])
        employee_selected = st.selectbox(
            "Select Employee ID", df["EmpID"].unique())
        df = df[df["EmpID"] == employee_selected]

    # Metrics
    total_employees = df["EmpID"].nunique()
    present_count = df[df["Final Status"] == "P"]["EmpID"].count()
    absent_count = df[df["Final Status"] == "Absent"]["EmpID"].count()
    overtime_hours = df["OT Hours"].sum()

    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Employees", total_employees)
        col2.metric("Total Present", present_count)
        col3.metric("Total Absent", absent_count)
        col4.metric("Total Overtime Hours", overtime_hours)

    # Graphs
    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Attendance Summary")
            status_counts = df["Final Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig1 = px.bar(
                status_counts,
                x="Status",
                y="Count",
                title="Attendance Status Distribution",
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("Department-wise Attendance")
            dept_counts = df.groupby("Department Name")[
                "EmpID"].count().reset_index()
            dept_counts.columns = ["Department", "Count"]
            fig2 = px.pie(
                dept_counts,
                names="Department",
                values="Count",
                title="Attendance by Department",
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col3:
            st.subheader("Attendance Type Distribution")
            att_type_counts = df["Attendance Type"].value_counts(
            ).reset_index()
            att_type_counts.columns = ["Attendance Type", "Count"]
            fig3 = px.pie(
                att_type_counts,
                names="Attendance Type",
                values="Count",
                title="Attendance Type Distribution",
            )
            st.plotly_chart(fig3, use_container_width=True)

    # New Graphs
    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Peak In & Out Times")
            df["In Time"] = pd.to_datetime(
                df["In Time"], format="%H:%M", errors="coerce"
            )
            df["Out Time"] = pd.to_datetime(
                df["Out Time"], format="%H:%M", errors="coerce"
            )

            in_time_counts = df["In Time"].dt.hour.value_counts().reset_index()
            in_time_counts.columns = ["Hour", "Count"]
            fig4 = px.bar(in_time_counts, x="Hour",
                          y="Count", title="Peak In Times")
            st.plotly_chart(fig4, use_container_width=True)

            out_time_counts = df["Out Time"].dt.hour.value_counts(
            ).reset_index()
            out_time_counts.columns = ["Hour", "Count"]
            fig5 = px.bar(out_time_counts, x="Hour",
                          y="Count", title="Peak Out Times")
            st.plotly_chart(fig5, use_container_width=True)

        with col2:
            st.subheader("Overtime Analysis")
            fig6 = px.histogram(
                df, x="OT Hours", nbins=20, title="Overtime Hours Distribution"
            )
            st.plotly_chart(fig6, use_container_width=True)

        with col3:
            st.subheader("Total Hours Distribution")
            fig7 = px.histogram(
                df, x="Total Hours", nbins=20, title="Total Hours Distribution"
            )
            st.plotly_chart(fig7, use_container_width=True)

    st.subheader("Detailed Data View")
    with st.expander("View Full Data"):
        st.dataframe(df)
