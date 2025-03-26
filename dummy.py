import csv
import random
from faker import Faker

fake = Faker()

# Define headers
headers = [
    "Sr. No.", "EmpID", "Attendance Code", "FName", "Branch Code", "Department Name",
    "Division Name", "Grade Code", "Designation Name", "Direct/Indirect", "Roster", "Attendance Date",
    "In Time", "Out Time", "Total Hours", "OT Hours", "Late Hours", "Application Status", "Final Status", "Attendance Type"
]

# Possible values for some columns
branch_codes = ["P001", "P002", "P003", "P004", "P005"]
departments = ["Quality", "Production", "HR", "Finance", "IT"]
divisions = ["Warranty", "Manufacturing", "Recruitment", "Accounting", "Support"]
grade_codes = ["C1", "C2", "C3", "C4", "C5"]
designations = ["Engineer", "Manager", "Executive", "DM", "Supervisor"]
direct_indirect = ["Direct", "Indirect"]
rosters = ["Working Day (G)", "Holiday", "Weekend"]
final_status = ["Present", "Absent", "Absent Half Day", "Leave"]
attendance_types = ["Full Day", "Half Day", "Leave"]

# Generate data
num_entries = 10000
rows = []

for i in range(1, num_entries + 1):
    emp_id = random.randint(30000, 50000)
    f_name = fake.first_name() + " " + fake.last_name()
    branch_code = random.choice(branch_codes)
    department = random.choice(departments)
    division = random.choice(divisions)
    grade_code = random.choice(grade_codes)
    designation = random.choice(designations)
    direct_indirect = random.choice(direct_indirect)
    roster = random.choice(rosters)
    attendance_date = fake.date_between(start_date="-30d", end_date="today").strftime("%d/%m/%Y")
    in_time = fake.time(pattern="%I:%M %p")
    out_time = fake.time(pattern="%I:%M %p")
    total_hours = round(random.uniform(6, 9), 2)
    ot_hours = round(random.uniform(0, 2), 2)
    late_hours = round(random.uniform(0, 1), 2)
    application_status = ""  # Keeping blank as per example
    final_stat = random.choice(final_status)
    attendance_type = random.choice(attendance_types)
    
    rows.append([
        i, emp_id, emp_id, f_name, branch_code, department, division,
        grade_code, designation, direct_indirect, roster, attendance_date,
        in_time, out_time, total_hours, ot_hours, late_hours, application_status,
        final_stat, attendance_type
    ])

# Write to CSV
csv_filename = "dummy_attendance.csv"
with open(csv_filename, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"CSV file '{csv_filename}' with {num_entries} dummy entries created successfully.")
