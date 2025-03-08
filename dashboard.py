import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import random
from datetime import datetime, timedelta
from streamlit_extras.add_vertical_space import add_vertical_space 

# Define expected columns
EXPECTED_COLUMNS = [
    "Sr. No.",
    "EmpID",
    "Attendance Code",
    "FName",
    "Branch Code",
    "Department Name",
    "Division Name",
    "ReportingEmpCode",
    "ReportingEmpName",
    "Grade Code",
    "Designation Name",
    "Direct/Indirect",
    "Roster",
    "Auto Shift Name",
    "Date of Joining",
    "Attendance Date",
    "In Time",
    "Out Time",
    "Total Hours",
    "OT Hours",
    "Late Hours",
    "Application Status",
    "Final Status",
    "Attendance Type",
]

# Load data from Excel
def load_data(file):
    xl = pd.ExcelFile(file)
    sheet_names = xl.sheet_names
    data = {sheet: xl.parse(sheet) for sheet in sheet_names}
    return data, sheet_names

# Preprocess data
def preprocess_data(df):
    # Keep only expected columns
    df = df[[col for col in df.columns if col in EXPECTED_COLUMNS]]

    # Ensure all expected columns exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Convert columns to string where necessary
    for col in ["Attendance Code", "Roster", "EmpID"]:  
        if col in df.columns:
            df[col] = df[col].astype(str)

    # Convert 'Attendance Date' to datetime safely
    df["Attendance Date"] = pd.to_datetime(df["Attendance Date"], errors="coerce")

    # Remove rows where 'Attendance Date' couldn't be converted
    df = df.dropna(subset=["Attendance Date"])

    df = df.fillna(
        {col: "Unknown" if df[col].dtype == "O" else 0 for col in EXPECTED_COLUMNS}
    )
    return df

# Generate synthetic data for new metrics
def generate_synthetic_data(df):
    """Generate additional data that might not be in the original dataset"""
    num_employees = df["EmpID"].nunique() or 100
    
    # Add skill levels (L1, L2, L3, L4)
    unique_employees = df["EmpID"].unique()
    skill_levels = {}
    for emp in unique_employees:
        skill_levels[emp] = random.choice(["L1", "L2", "L3", "L4"])
    
    df["Skill Level"] = df["EmpID"].map(skill_levels)
    
    # Add employment type (Permanent/Temporary)
    employment_types = {}
    for emp in unique_employees:
        employment_types[emp] = random.choice(["Permanent", "Temporary"])
    
    df["Employment Type"] = df["EmpID"].map(employment_types)
    
    # Add production line assignment
    production_lines = {}
    for emp in unique_employees:
        production_lines[emp] = f"Line {random.randint(1, 10)}"
    
    df["Production Line"] = df["EmpID"].map(production_lines)
    
    # Add gender information
    genders = {}
    for emp in unique_employees:
        genders[emp] = random.choice(["Male", "Female"])
    
    df["Gender"] = df["EmpID"].map(genders)
    
    # Add shift information if not present
    if "Auto Shift Name" not in df.columns or df["Auto Shift Name"].isnull().all():
        shifts = {}
        for emp in unique_employees:
            shifts[emp] = random.choice(["Morning", "Afternoon", "Night"])
        df["Auto Shift Name"] = df["EmpID"].map(shifts)
    
    # Generate historical attendance data
    today = datetime.now()
    all_data = []
    
    # Get range of dates to simulate history
    date_range = [today - timedelta(days=x) for x in range(180)]
    
    for emp in unique_employees:
        emp_rows = df[df["EmpID"] == emp].iloc[0].to_dict() if len(df[df["EmpID"] == emp]) > 0 else {}
        
        for date in date_range:
            # Skip weekends with higher probability
            if date.weekday() >= 5 and random.random() < 0.8:
                continue
                
            attendance_status = random.choices(
                ["P", "Absent", "Leave", "Half Day"], 
                weights=[0.85, 0.07, 0.05, 0.03],
                k=1
            )[0]
            
            # Copy the employee data
            new_row = emp_rows.copy() if emp_rows else {col: None for col in EXPECTED_COLUMNS}
            new_row["EmpID"] = emp
            new_row["Attendance Date"] = date
            new_row["Final Status"] = attendance_status
            all_data.append(new_row)
    
    # Create synthetic attrition data
    attrition_df = pd.DataFrame({
        "Month": pd.date_range(start=today-timedelta(days=365), end=today, freq='M').strftime('%Y-%m'),
        "Attrition_Rate": [random.uniform(0.01, 0.08) for _ in range(12)]
    })
    
    # Create buffer manpower data
    buffer_df = pd.DataFrame({
        "Date": pd.date_range(start=today-timedelta(days=30), end=today, freq='D'),
        "Required": [random.randint(80, 100) for _ in range(31)],
        "Available": [random.randint(70, 95) for _ in range(31)]
    })
    
    # If there's existing data, combine it with the synthetic data
    if len(df) > 0:
        synthetic_df = pd.DataFrame(all_data)
        for col in df.columns:
            if col not in synthetic_df.columns:
                synthetic_df[col] = None
        
        for col in synthetic_df.columns:
            if col not in df.columns:
                df[col] = None
                
        combined_df = pd.concat([df, synthetic_df])
    else:
        combined_df = pd.DataFrame(all_data)
    
    return combined_df, attrition_df, buffer_df

st.set_page_config(layout="wide")
st.title("Employee Attendance Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xls", "xlsx"])

if uploaded_file:
    data, sheets = load_data(uploaded_file)

    # Dashboard Selection
    dashboard_option = st.sidebar.radio(
        "Select Dashboard",
        ["General", "Employee Statistics", "Manpower Analysis", "Attendance Trends"],
    )

    try:
        # Process data
        all_sheets_df = pd.concat([preprocess_data(data[sheet]) for sheet in sheets])
        # Add synthetic data
        df, attrition_df, buffer_df = generate_synthetic_data(all_sheets_df)
        
        min_date, max_date = df["Attendance Date"].min(), df["Attendance Date"].max()
        
        # Filters in sidebar
        with st.sidebar:
            add_vertical_space(1)
            st.subheader("Filters")
            
            # Date filter - adjust based on dashboard
            if dashboard_option in ["General", "Manpower Analysis", "Attendance Trends"]:
                filter_period = st.selectbox(
                    "Select Time Period",
                    ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]
                )
                
                if filter_period == "Daily":
                    start_date, end_date = st.date_input(
                        "Select Date Range", 
                        [max_date - timedelta(days=7), max_date], 
                        min_value=min_date, 
                        max_value=max_date
                    )
                elif filter_period == "Weekly":
                    start_date = max_date - timedelta(days=30)
                    end_date = max_date
                elif filter_period == "Monthly":
                    start_date = max_date - timedelta(days=90)
                    end_date = max_date
                elif filter_period == "Quarterly":
                    start_date = max_date - timedelta(days=180)
                    end_date = max_date
                else:  # Yearly
                    start_date = max_date - timedelta(days=365)
                    end_date = max_date
            else:
                # For employee stats, just use the whole date range
                start_date, end_date = min_date, max_date
            
            filtered_df = df[(df["Attendance Date"] >= pd.Timestamp(start_date)) & 
                             (df["Attendance Date"] <= pd.Timestamp(end_date))]

            # Other common filters
            department_filter = st.selectbox(
                "Filter by Department",
                ["All"] + sorted(filtered_df["Department Name"].dropna().unique().tolist()),
            )
            
            division_filter = st.selectbox(
                "Filter by Division",
                ["All"] + sorted(filtered_df["Division Name"].dropna().unique().tolist()),
            )
            
            direct_filter = st.selectbox(
                "Filter by Direct/Indirect",
                ["All"] + sorted(filtered_df["Direct/Indirect"].dropna().unique().tolist()),
            )
            
            skill_filter = st.selectbox(
                "Filter by Skill Level",
                ["All", "L1", "L2", "L3", "L4"],
            )
            
            employment_filter = st.selectbox(
                "Filter by Employment Type",
                ["All", "Permanent", "Temporary"],
            )
            
            shift_filter = st.selectbox(
                "Filter by Shift",
                ["All"] + sorted(filtered_df["Auto Shift Name"].dropna().unique().tolist()),
            )
            
            # Apply filters
            if department_filter != "All":
                filtered_df = filtered_df[filtered_df["Department Name"] == department_filter]
            if division_filter != "All":
                filtered_df = filtered_df[filtered_df["Division Name"] == division_filter]
            if direct_filter != "All":
                filtered_df = filtered_df[filtered_df["Direct/Indirect"] == direct_filter]
            if skill_filter != "All":
                filtered_df = filtered_df[filtered_df["Skill Level"] == skill_filter]
            if employment_filter != "All":
                filtered_df = filtered_df[filtered_df["Employment Type"] == employment_filter]
            if shift_filter != "All":
                filtered_df = filtered_df[filtered_df["Auto Shift Name"] == shift_filter]
        
        # Different dashboard views
        if dashboard_option == "General":
            # Metrics
            total_employees = filtered_df["EmpID"].nunique()
            present_count = filtered_df[filtered_df["Final Status"] == "P"]["EmpID"].count()
            absent_count = filtered_df[filtered_df["Final Status"] == "Absent"]["EmpID"].count()
            overtime_hours = filtered_df["OT Hours"].sum()

            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Employees", total_employees)
                col2.metric("Present Today", present_count)
                col3.metric("Absent Today", absent_count)
                col4.metric("Total Overtime Hours", f"{overtime_hours:.2f}")

            add_vertical_space(2)

            # Graphs
            with st.container():
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.subheader("Attendance Summary")
                    status_counts = filtered_df["Final Status"].value_counts().reset_index()
                    status_counts.columns = ["Status", "Count"]
                    fig1 = px.bar(
                        status_counts,
                        x="Status",
                        y="Count",
                        title="Attendance Status Distribution",
                        color="Status",
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                with col2:
                    st.subheader("Department-wise Attendance")
                    dept_counts = filtered_df.groupby("Department Name")[
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
                    att_type_counts = filtered_df["Attendance Type"].value_counts().reset_index()
                    att_type_counts.columns = ["Attendance Type", "Count"]
                    fig3 = px.pie(
                        att_type_counts,
                        names="Attendance Type",
                        values="Count",
                        title="Attendance Type Distribution",
                    )
                    st.plotly_chart(fig3, use_container_width=True)

            # Additional Graphs from original dashboard
            with st.container():
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.subheader("Peak In & Out Times")
                    filtered_df["In Time"] = pd.to_datetime(filtered_df["In Time"], errors="coerce")
                    filtered_df["Out Time"] = pd.to_datetime(filtered_df["Out Time"], errors="coerce")

                    in_time_counts = filtered_df["In Time"].dt.hour.value_counts().reset_index()
                    in_time_counts.columns = ["Hour", "Count"]
                    in_time_counts = in_time_counts.sort_values("Hour")
                    fig4 = px.bar(in_time_counts, x="Hour",
                                y="Count", title="Peak In Times")
                    st.plotly_chart(fig4, use_container_width=True)

                    out_time_counts = filtered_df["Out Time"].dt.hour.value_counts().reset_index()
                    out_time_counts.columns = ["Hour", "Count"]
                    out_time_counts = out_time_counts.sort_values("Hour")
                    fig5 = px.bar(out_time_counts, x="Hour",
                                y="Count", title="Peak Out Times")
                    st.plotly_chart(fig5, use_container_width=True)

                with col2:
                    st.subheader("Overtime Analysis")
                    fig6 = px.histogram(
                        filtered_df, x="OT Hours", nbins=20, title="Overtime Hours Distribution"
                    )
                    st.plotly_chart(fig6, use_container_width=True)

                with col3:
                    st.subheader("Total Hours Distribution")
                    fig7 = px.histogram(
                        filtered_df, x="Total Hours", nbins=20, title="Total Hours Distribution"
                    )
                    st.plotly_chart(fig7, use_container_width=True)

        elif dashboard_option == "Employee Statistics":
            employee_selected = st.selectbox(
                "Select Employee ID", sorted(df["EmpID"].unique()))
            employee_df = df[df["EmpID"] == employee_selected]
            
            # Employee details
            emp_details = employee_df.iloc[0]
            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Name", emp_details.get("FName", "Unknown"))
                col2.metric("Department", emp_details.get("Department Name", "Unknown"))
                col3.metric("Skill Level", emp_details.get("Skill Level", "Unknown"))
                col4.metric("Employment Type", emp_details.get("Employment Type", "Unknown"))
            
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    # Attendance history
                    st.subheader("Attendance History")
                    attendance_history = employee_df.groupby("Attendance Date")["Final Status"].first().reset_index()
                    attendance_history = attendance_history.sort_values("Attendance Date")
                    
                    # Create a color map for status
                    status_colors = {"P": "green", "Absent": "red", "Leave": "blue", "Half Day": "orange"}
                    attendance_history["Color"] = attendance_history["Final Status"].map(status_colors)
                    
                    fig = px.scatter(
                        attendance_history, 
                        x="Attendance Date", 
                        y=[1]*len(attendance_history),
                        color="Final Status",
                        size=[5]*len(attendance_history),
                        title="Attendance Status by Date"
                    )
                    fig.update_layout(yaxis_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Monthly attendance summary
                    st.subheader("Monthly Attendance Summary")
                    employee_df["Month"] = employee_df["Attendance Date"].dt.strftime('%Y-%m')
                    monthly_summary = employee_df.groupby("Month")["Final Status"].value_counts().unstack().fillna(0)
                    
                    if not monthly_summary.empty:
                        fig = px.bar(
                            monthly_summary, 
                            barmode="group",
                            title="Monthly Attendance Breakdown"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Overtime trends
            st.subheader("Overtime Trends")
            overtime_data = employee_df.groupby("Attendance Date")["OT Hours"].sum().reset_index()
            overtime_data = overtime_data.sort_values("Attendance Date")
            
            fig = px.line(
                overtime_data,
                x="Attendance Date",
                y="OT Hours",
                title="Daily Overtime Hours"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif dashboard_option == "Manpower Analysis":
            st.header("Manpower Analysis Dashboard")
            
            # 1. Availability of Skilled Manpower
            st.subheader("1. Availability of Skilled Manpower")
            skill_distribution = filtered_df.drop_duplicates("EmpID")["Skill Level"].value_counts().reset_index()
            skill_distribution.columns = ["Skill Level", "Count"]
            
            fig = px.bar(
                skill_distribution,
                x="Skill Level",
                y="Count",
                color="Skill Level",
                title="Distribution of Skill Levels"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 2. Permanent vs Temporary Attendance Monitoring
            st.subheader("2. Attendance by Employment Type")
            # Group data by date and employment type
            emp_type_attendance = filtered_df.groupby(["Attendance Date", "Employment Type"])["EmpID"].nunique().reset_index()
            emp_type_attendance = emp_type_attendance.pivot(index="Attendance Date", columns="Employment Type", values="EmpID").reset_index()
            
            fig = px.line(
                emp_type_attendance,
                x="Attendance Date",
                y=emp_type_attendance.columns[1:],
                title="Attendance Trends by Employment Type",
                labels={"value": "Employee Count", "variable": "Employment Type"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. Manpower Monitoring Shift Wise with Line Wise
            st.subheader("3. Manpower by Shift and Production Line")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Shift-wise distribution
                shift_distribution = filtered_df.drop_duplicates("EmpID").groupby("Auto Shift Name")["EmpID"].count().reset_index()
                shift_distribution.columns = ["Shift", "Employee Count"]
                
                fig = px.pie(
                    shift_distribution,
                    names="Shift",
                    values="Employee Count",
                    title="Employee Distribution by Shift"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Line-wise distribution
                line_distribution = filtered_df.drop_duplicates("EmpID").groupby("Production Line")["EmpID"].count().reset_index()
                line_distribution.columns = ["Production Line", "Employee Count"]
                
                fig = px.bar(
                    line_distribution,
                    x="Production Line",
                    y="Employee Count",
                    title="Employee Distribution by Production Line"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Combined heatmap
            st.subheader("Shift and Production Line Heatmap")
            shift_line_heatmap = filtered_df.drop_duplicates("EmpID").groupby(["Auto Shift Name", "Production Line"])["EmpID"].count().reset_index()
            shift_line_heatmap.columns = ["Shift", "Production Line", "Employee Count"]
            
            # Create pivot table for heatmap
            heatmap_data = shift_line_heatmap.pivot(index="Shift", columns="Production Line", values="Employee Count").fillna(0)
            
            fig = px.imshow(
                heatmap_data,
                labels=dict(x="Production Line", y="Shift", color="Employee Count"),
                x=heatmap_data.columns,
                y=heatmap_data.index,
                title="Employee Distribution by Shift and Production Line",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 4. Manpower monitoring with Date Range 
            st.subheader("4. Manpower Trends Over Time")
            
            # Group by date
            date_manpower = filtered_df.groupby("Attendance Date")["EmpID"].nunique().reset_index()
            date_manpower.columns = ["Date", "Employee Count"]
            
            fig = px.line(
                date_manpower,
                x="Date",
                y="Employee Count",
                title="Daily Manpower Trends"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 5. Manpower monitoring Gender wise
            st.subheader("5. Gender Distribution Analysis")
            
            gender_distribution = filtered_df.drop_duplicates("EmpID")["Gender"].value_counts().reset_index()
            gender_distribution.columns = ["Gender", "Count"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    gender_distribution,
                    names="Gender",
                    values="Count",
                    title="Gender Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Gender by department
                gender_dept = filtered_df.drop_duplicates("EmpID").groupby(["Department Name", "Gender"])["EmpID"].count().reset_index()
                gender_dept.columns = ["Department", "Gender", "Count"]
                
                fig = px.bar(
                    gender_dept,
                    x="Department",
                    y="Count",
                    color="Gender",
                    barmode="group",
                    title="Gender Distribution by Department"
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        elif dashboard_option == "Attendance Trends":
            st.header("Attendance Trends Dashboard")
            
            # 6. Absenteeism graph
            st.subheader("6. Absenteeism Trends")
            
            # Calculate daily absenteeism rate
            daily_attendance = filtered_df.groupby("Attendance Date")["Final Status"].value_counts().unstack().fillna(0)
            if "Absent" in daily_attendance.columns:
                daily_attendance["Absenteeism Rate"] = daily_attendance["Absent"] / daily_attendance.sum(axis=1) * 100
                daily_attendance = daily_attendance.reset_index()
                
                fig = px.line(
                    daily_attendance,
                    x="Attendance Date",
                    y="Absenteeism Rate",
                    title="Daily Absenteeism Rate (%)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No absence data available for the selected period.")
            
            # Department-wise absenteeism
            dept_absence = filtered_df.groupby("Department Name")["Final Status"].value_counts().unstack().fillna(0)
            if "Absent" in dept_absence.columns:
                dept_absence["Absenteeism Rate"] = dept_absence["Absent"] / dept_absence.sum(axis=1) * 100
                dept_absence = dept_absence.reset_index()
                
                fig = px.bar(
                    dept_absence,
                    x="Department Name",
                    y="Absenteeism Rate",
                    title="Absenteeism Rate by Department (%)"
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # 7. Attrition graph
            st.subheader("7. Attrition Analysis")
            
            fig = px.line(
                attrition_df,
                x="Month",
                y="Attrition_Rate",
                title="Monthly Attrition Rate (%)"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # 8. Buffer Manpower Graph
            st.subheader("8. Buffer Manpower Analysis")
            
            fig = px.line(
                buffer_df,
                x="Date",
                y=["Required", "Available"],
                title="Required vs Available Manpower"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate buffer percentage
            buffer_df["Buffer Percentage"] = (buffer_df["Available"] / buffer_df["Required"]) * 100 - 100
            
            fig = px.bar(
                buffer_df,
                x="Date",
                y="Buffer Percentage",
                title="Buffer Manpower Percentage",
                color="Buffer Percentage",
                color_continuous_scale=["red", "yellow", "green"],
                range_color=[-20, 20]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 9. Short manpower against available manpower
            st.subheader("9. Manpower Shortage Analysis")
            
            # Calculate shortage
            buffer_df["Shortage"] = buffer_df["Required"] - buffer_df["Available"]
            buffer_df["Shortage"] = buffer_df["Shortage"].apply(lambda x: max(x, 0))
            
            fig = px.bar(
                buffer_df,
                x="Date",
                y="Shortage",
                title="Daily Manpower Shortage"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Department wise shortage (simulated)
            dept_list = filtered_df["Department Name"].unique()
            shortage_by_dept = pd.DataFrame({
                "Department": dept_list,
                "Required": [random.randint(15, 30) for _ in range(len(dept_list))],
                "Available": [random.randint(10, 25) for _ in range(len(dept_list))]
            })
            shortage_by_dept["Shortage"] = shortage_by_dept["Required"] - shortage_by_dept["Available"]
            shortage_by_dept["Shortage"] = shortage_by_dept["Shortage"].apply(lambda x: max(x, 0))
            shortage_by_dept["Shortage Percentage"] = (shortage_by_dept["Shortage"] / shortage_by_dept["Required"]) * 100
            
            fig = px.bar(
                shortage_by_dept,
                x="Department",
                y="Shortage Percentage",
                title="Manpower Shortage by Department (%)"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Data View (Common)
        st.subheader("Detailed Data View")
        with st.expander("View Full Data"):
            st.dataframe(filtered_df)
    
    except Exception as e:
        st.error(f"An error occurred while processing the data: {e}")
        st.info("Using demo data instead...")
        
        # Generate completely synthetic data for demo
        from datetime import datetime, timedelta
        
        # Generate sample employee data
        num_employees = 100
        departments = ["Production", "Quality", "Maintenance", "HR", "Administration"]
        divisions = ["A", "B", "C"]
        skill_levels = ["L1", "L2", "L3", "L4"]
        shifts = ["Morning", "Afternoon", "Night"]
        genders = ["Male", "Female"]
        
        # Generate employee base data
        employee_data = []
        for i in range(1, num_employees + 1):
            emp_id = f"EMP{i:03d}"
            department = random.choice(departments)
            division = random.choice(divisions)
            skill_level = random.choice(skill_levels)
            shift = random.choice(shifts)
            gender = random.choice(genders)
            emp_type = random.choice(["Permanent", "Temporary"])
            line = f"Line {random.randint(1, 10)}"
            
            employee_data.append({
                "EmpID": emp_id,
                "FName": f"Employee {i}",
                "Department Name": department,
                "Division Name": division,
                "Skill Level": skill_level,
                "Auto Shift Name": shift,
                "Gender": gender,
                "Employment Type": emp_type,
                "Production Line": line
            })
        
        # Generate attendance data
        attendance_data = []
        today = datetime.now()
        
        for day in range(90):
            date = today - timedelta(days=day)
            for emp in employee_data:
                # Skip weekends with higher probability
                if date.weekday() >= 5 and random.random() < 0.8:
                    continue
                    
                status = random.choices(
                    ["P", "Absent", "Leave", "Half Day"], 
                    weights=[0.85, 0.07, 0.05, 0.03],
                    k=1
                )[0]
                
                in_time = datetime.combine(date.date(), datetime.min.time()) + timedelta(hours=8, minutes=random.randint(0, 60))
                out_time = in_time + timedelta(hours=8, minutes=random.randint(0, 60))
                total_hours = (out_time - in_time).total_seconds() / 3600
                
                # Add attendance record
                attendance_data.append({
                    **emp,
                    "Attendance Date": date,
                    "Final Status": status,
                    "In Time": in_time if status in ["P", "Half Day"] else None,
                    "Out Time": out_time if status in ["P", "Half Day"] else None,
                    "Total Hours": total_hours if status in ["P", "Half Day"] else 0,
                    "OT Hours": max(0, total_hours - 8) if status == "P" else 0,
                    "Late Hours": random.uniform(0, 1) if random.random() < 0.2 else 0,
                    "Attendance Type": "Regular" if status == "P" else status
                })
        
        # Create dataframe
        df = pd.DataFrame(attendance_data)
        
        # Create synthetic attrition data
        attrition_df = pd.DataFrame({
            "Month": pd.date_range(start=today-timedelta(days=365), end=today, freq='M').strftime('%Y-%m'),
            "Attrition_Rate": [random.uniform(0.01, 0.08) for _ in range(12)]
        })
        
        # Create buffer manpower data
        buffer_df = pd.DataFrame({
            "Date": pd.date_range(start=today-timedelta(days=30), end=today, freq='D'),
            "Required": [random.randint(80, 100) for _ in range(31)],
            "Available": [random.randint(70, 95) for _ in range(31)]
        })
        
        # Display dashboard with demo data
        dashboard_option = st.sidebar.radio(
            "Select Dashboard",
            ["General", "Employee Statistics", "Manpower Analysis", "Attendance Trends"],
        )

        min_date, max_date = df["Attendance Date"].min(), df["Attendance Date"].max()
        
        # Filters in sidebar
        with st.sidebar:
            add_vertical_space(1)
            st.subheader("Filters")
            
            # Date filter - adjust based on dashboard
            if dashboard_option in ["General", "Manpower Analysis", "Attendance Trends"]:
                filter_period = st.selectbox(
                    "Select Time Period",
                    ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]
                )
                
                if filter_period == "Daily":
                    start_date, end_date = st.date_input(
                        "Select Date Range", 
                        [max_date - timedelta(days=7), max_date], 
                        min_value=min_date, 
                        max_value=max_date
                    )
                elif filter_period == "Weekly":
                    start_date = max_date - timedelta(days=30)
                    end_date = max_date
                elif filter_period == "Monthly":
                    start_date = max_date - timedelta(days=90)
                    end_date = max_date
                elif filter_period == "Quarterly":
                    start_date = max_date - timedelta(days=180)
                    end_date = max_date
                else:  # Yearly
                    start_date = max_date - timedelta(days=365)
                    end_date = max_date
            else:
                # For employee stats, just use the whole date range
                start_date, end_date = min_date, max_date
            
            filtered_df = df[(df["Attendance Date"] >= pd.Timestamp(start_date)) & 
                            (df["Attendance Date"] <= pd.Timestamp(end_date))]

            # Other common filters
            department_filter = st.selectbox(
                "Filter by Department",
                ["All"] + sorted(filtered_df["Department Name"].dropna().unique().tolist()),
            )
            
            division_filter = st.selectbox(
                "Filter by Division",
                ["All"] + sorted(filtered_df["Division Name"].dropna().unique().tolist()),
            )
            
            skill_filter = st.selectbox(
                "Filter by Skill Level",
                ["All", "L1", "L2", "L3", "L4"],
            )
            
            employment_filter = st.selectbox(
                "Filter by Employment Type",
                ["All", "Permanent", "Temporary"],
            )
            
            shift_filter = st.selectbox(
                "Filter by Shift",
                ["All"] + sorted(filtered_df["Auto Shift Name"].dropna().unique().tolist()),
            )
            
            # Apply filters
            if department_filter != "All":
                filtered_df = filtered_df[filtered_df["Department Name"] == department_filter]
            if division_filter != "All":
                filtered_df = filtered_df[filtered_df["Division Name"] == division_filter]
            if skill_filter != "All":
                filtered_df = filtered_df[filtered_df["Skill Level"] == skill_filter]
            if employment_filter != "All":
                filtered_df = filtered_df[filtered_df["Employment Type"] == employment_filter]
            if shift_filter != "All":
                filtered_df = filtered_df[filtered_df["Auto Shift Name"] == shift_filter]
                
        # Display the selected dashboard
        st.info("Using demo data - upload an Excel file for actual analysis")
        
        if dashboard_option == "General":
            # Metrics
            total_employees = filtered_df["EmpID"].nunique()
            present_count = filtered_df[filtered_df["Final Status"] == "P"]["EmpID"].count()
            absent_count = filtered_df[filtered_df["Final Status"] == "Absent"]["EmpID"].count()
            overtime_hours = filtered_df["OT Hours"].sum()

            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Employees", total_employees)
                col2.metric("Present Today", present_count)
                col3.metric("Absent Today", absent_count)
                col4.metric("Total Overtime Hours", f"{overtime_hours:.2f}")

            add_vertical_space(2)

            # Graphs
            with st.container():
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.subheader("Attendance Summary")
                    status_counts = filtered_df["Final Status"].value_counts().reset_index()
                    status_counts.columns = ["Status", "Count"]
                    fig1 = px.bar(
                        status_counts,
                        x="Status",
                        y="Count",
                        title="Attendance Status Distribution",
                        color="Status",
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                with col2:
                    st.subheader("Department-wise Attendance")
                    dept_counts = filtered_df.groupby("Department Name")[
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
                    att_type_counts = filtered_df["Attendance Type"].value_counts().reset_index()
                    att_type_counts.columns = ["Attendance Type", "Count"]
                    fig3 = px.pie(
                        att_type_counts,
                        names="Attendance Type",
                        values="Count",
                        title="Attendance Type Distribution",
                    )
                    st.plotly_chart(fig3, use_container_width=True)

            # Additional Graphs from original dashboard
            with st.container():
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.subheader("Peak In & Out Times")
                    filtered_df["In Time"] = pd.to_datetime(filtered_df["In Time"], errors="coerce")
                    filtered_df["Out Time"] = pd.to_datetime(filtered_df["Out Time"], errors="coerce")

                    in_time_counts = filtered_df["In Time"].dt.hour.value_counts().reset_index()
                    in_time_counts.columns = ["Hour", "Count"]
                    in_time_counts = in_time_counts.sort_values("Hour")
                    fig4 = px.bar(in_time_counts, x="Hour",
                                y="Count", title="Peak In Times")
                    st.plotly_chart(fig4, use_container_width=True)

                    out_time_counts = filtered_df["Out Time"].dt.hour.value_counts().reset_index()
                    out_time_counts.columns = ["Hour", "Count"]
                    out_time_counts = out_time_counts.sort_values("Hour")
                    fig5 = px.bar(out_time_counts, x="Hour",
                                y="Count", title="Peak Out Times")
                    st.plotly_chart(fig5, use_container_width=True)

                with col2:
                    st.subheader("Overtime Analysis")
                    fig6 = px.histogram(
                        filtered_df, x="OT Hours", nbins=20, title="Overtime Hours Distribution"
                    )
                    st.plotly_chart(fig6, use_container_width=True)

                with col3:
                    st.subheader("Total Hours Distribution")
                    fig7 = px.histogram(
                        filtered_df, x="Total Hours", nbins=20, title="Total Hours Distribution"
                    )
                    st.plotly_chart(fig7, use_container_width=True)
        
        elif dashboard_option == "Employee Statistics":
            employee_selected = st.selectbox(
                "Select Employee ID", sorted(df["EmpID"].unique()))
            employee_df = df[df["EmpID"] == employee_selected]
            
            # Employee details
            emp_details = employee_df.iloc[0]
            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Name", emp_details.get("FName", "Unknown"))
                col2.metric("Department", emp_details.get("Department Name", "Unknown"))
                col3.metric("Skill Level", emp_details.get("Skill Level", "Unknown"))
                col4.metric("Employment Type", emp_details.get("Employment Type", "Unknown"))
            
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    # Attendance history
                    st.subheader("Attendance History")
                    attendance_history = employee_df.groupby("Attendance Date")["Final Status"].first().reset_index()
                    attendance_history = attendance_history.sort_values("Attendance Date")
                    
                    # Create a color map for status
                    status_colors = {"P": "green", "Absent": "red", "Leave": "blue", "Half Day": "orange"}
                    attendance_history["Color"] = attendance_history["Final Status"].map(status_colors)
                    
                    fig = px.scatter(
                        attendance_history, 
                        x="Attendance Date", 
                        y=[1]*len(attendance_history),
                        color="Final Status",
                        size=[5]*len(attendance_history),
                        title="Attendance Status by Date"
                    )
                    fig.update_layout(yaxis_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Monthly attendance summary
                    st.subheader("Monthly Attendance Summary")
                    employee_df["Month"] = employee_df["Attendance Date"].dt.strftime('%Y-%m')
                    monthly_summary = employee_df.groupby("Month")["Final Status"].value_counts().unstack().fillna(0)
                    
                    if not monthly_summary.empty:
                        fig = px.bar(
                            monthly_summary, 
                            barmode="group",
                            title="Monthly Attendance Breakdown"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Overtime trends
            st.subheader("Overtime Trends")
            overtime_data = employee_df.groupby("Attendance Date")["OT Hours"].sum().reset_index()
            overtime_data = overtime_data.sort_values("Attendance Date")
            
            fig = px.line(
                overtime_data,
                x="Attendance Date",
                y="OT Hours",
                title="Daily Overtime Hours"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif dashboard_option == "Manpower Analysis":
            st.header("Manpower Analysis Dashboard")
            
            # 1. Availability of Skilled Manpower
            st.subheader("1. Availability of Skilled Manpower")
            skill_distribution = filtered_df.drop_duplicates("EmpID")["Skill Level"].value_counts().reset_index()
            skill_distribution.columns = ["Skill Level", "Count"]
            
            fig = px.bar(
                skill_distribution,
                x="Skill Level",
                y="Count",
                color="Skill Level",
                title="Distribution of Skill Levels"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 2. Permanent vs Temporary Attendance Monitoring
            st.subheader("2. Attendance by Employment Type")
            # Group data by date and employment type
            emp_type_attendance = filtered_df.groupby(["Attendance Date", "Employment Type"])["EmpID"].nunique().reset_index()
            emp_type_attendance = emp_type_attendance.pivot(index="Attendance Date", columns="Employment Type", values="EmpID").reset_index()
            
            fig = px.line(
                emp_type_attendance,
                x="Attendance Date",
                y=emp_type_attendance.columns[1:],
                title="Attendance Trends by Employment Type",
                labels={"value": "Employee Count", "variable": "Employment Type"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. Manpower Monitoring Shift Wise with Line Wise
            st.subheader("3. Manpower by Shift and Production Line")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Shift-wise distribution
                shift_distribution = filtered_df.drop_duplicates("EmpID").groupby("Auto Shift Name")["EmpID"].count().reset_index()
                shift_distribution.columns = ["Shift", "Employee Count"]
                
                fig = px.pie(
                    shift_distribution,
                    names="Shift",
                    values="Employee Count",
                    title="Employee Distribution by Shift"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Line-wise distribution
                line_distribution = filtered_df.drop_duplicates("EmpID").groupby("Production Line")["EmpID"].count().reset_index()
                line_distribution.columns = ["Production Line", "Employee Count"]
                
                fig = px.bar(
                    line_distribution,
                    x="Production Line",
                    y="Employee Count",
                    title="Employee Distribution by Production Line"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Combined heatmap
            st.subheader("Shift and Production Line Heatmap")
            shift_line_heatmap = filtered_df.drop_duplicates("EmpID").groupby(["Auto Shift Name", "Production Line"])["EmpID"].count().reset_index()
            shift_line_heatmap.columns = ["Shift", "Production Line", "Employee Count"]
            
            # Create pivot table for heatmap
            heatmap_data = shift_line_heatmap.pivot(index="Shift", columns="Production Line", values="Employee Count").fillna(0)
            
            fig = px.imshow(
                heatmap_data,
                labels=dict(x="Production Line", y="Shift", color="Employee Count"),
                x=heatmap_data.columns,
                y=heatmap_data.index,
                title="Employee Distribution by Shift and Production Line",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 4. Manpower monitoring with Date Range 
            st.subheader("4. Manpower Trends Over Time")
            
            # Group by date
            date_manpower = filtered_df.groupby("Attendance Date")["EmpID"].nunique().reset_index()
            date_manpower.columns = ["Date", "Employee Count"]
            
            fig = px.line(
                date_manpower,
                x="Date",
                y="Employee Count",
                title="Daily Manpower Trends"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 5. Manpower monitoring Gender wise
            st.subheader("5. Gender Distribution Analysis")
            
            gender_distribution = filtered_df.drop_duplicates("EmpID")["Gender"].value_counts().reset_index()
            gender_distribution.columns = ["Gender", "Count"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    gender_distribution,
                    names="Gender",
                    values="Count",
                    title="Gender Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Gender by department
                gender_dept = filtered_df.drop_duplicates("EmpID").groupby(["Department Name", "Gender"])["EmpID"].count().reset_index()
                gender_dept.columns = ["Department", "Gender", "Count"]
                
                fig = px.bar(
                    gender_dept,
                    x="Department",
                    y="Count",
                    color="Gender",
                    barmode="group",
                    title="Gender Distribution by Department"
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        elif dashboard_option == "Attendance Trends":
            st.header("Attendance Trends Dashboard")
            
            # 6. Absenteeism graph
            st.subheader("6. Absenteeism Trends")
            
            # Calculate daily absenteeism rate
            daily_attendance = filtered_df.groupby("Attendance Date")["Final Status"].value_counts().unstack().fillna(0)
            if "Absent" in daily_attendance.columns:
                daily_attendance["Absenteeism Rate"] = daily_attendance["Absent"] / daily_attendance.sum(axis=1) * 100
                daily_attendance = daily_attendance.reset_index()
                
                fig = px.line(
                    daily_attendance,
                    x="Attendance Date",
                    y="Absenteeism Rate",
                    title="Daily Absenteeism Rate (%)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No absence data available for the selected period.")
            
            # Department-wise absenteeism
            dept_absence = filtered_df.groupby("Department Name")["Final Status"].value_counts().unstack().fillna(0)
            if "Absent" in dept_absence.columns:
                dept_absence["Absenteeism Rate"] = dept_absence["Absent"] / dept_absence.sum(axis=1) * 100
                dept_absence = dept_absence.reset_index()
                
                fig = px.bar(
                    dept_absence,
                    x="Department Name",
                    y="Absenteeism Rate",
                    title="Absenteeism Rate by Department (%)"
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # 7. Attrition graph
            st.subheader("7. Attrition Analysis")
            
            fig = px.line(
                attrition_df,
                x="Month",
                y="Attrition_Rate",
                title="Monthly Attrition Rate (%)"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # 8. Buffer Manpower Graph
            st.subheader("8. Buffer Manpower Analysis")
            
            fig = px.line(
                buffer_df,
                x="Date",
                y=["Required", "Available"],
                title="Required vs Available Manpower"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate buffer percentage
            buffer_df["Buffer Percentage"] = (buffer_df["Available"] / buffer_df["Required"]) * 100 - 100
            
            fig = px.bar(
                buffer_df,
                x="Date",
                y="Buffer Percentage",
                title="Buffer Manpower Percentage",
                color="Buffer Percentage",
                color_continuous_scale=["red", "yellow", "green"],
                range_color=[-20, 20]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 9. Short manpower against available manpower
            st.subheader("9. Manpower Shortage Analysis")
            
            # Calculate shortage
            buffer_df["Shortage"] = buffer_df["Required"] - buffer_df["Available"]
            buffer_df["Shortage"] = buffer_df["Shortage"].apply(lambda x: max(x, 0))
            
            fig = px.bar(
                buffer_df,
                x="Date",
                y="Shortage",
                title="Daily Manpower Shortage"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Department wise shortage (simulated)
            dept_list = filtered_df["Department Name"].unique()
            shortage_by_dept = pd.DataFrame({
                "Department": dept_list,
                "Required": [random.randint(15, 30) for _ in range(len(dept_list))],
                "Available": [random.randint(10, 25) for _ in range(len(dept_list))]
            })
            shortage_by_dept["Shortage"] = shortage_by_dept["Required"] - shortage_by_dept["Available"]
            shortage_by_dept["Shortage"] = shortage_by_dept["Shortage"].apply(lambda x: max(x, 0))
            shortage_by_dept["Shortage Percentage"] = (shortage_by_dept["Shortage"] / shortage_by_dept["Required"]) * 100
            
            fig = px.bar(
                shortage_by_dept,
                x="Department",
                y="Shortage Percentage",
                title="Manpower Shortage by Department (%)"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Data View (Common)
        st.subheader("Detailed Data View")
        with st.expander("View Full Data"):
            st.dataframe(filtered_df)

else:
    st.info("Please upload an Excel file to start analysis")