import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# Firebase configuration for Pyrebase
firebase_config = {
    "apiKey": "AIzaSyDWvJmVNee6L3I1PhI3pKpq2Jdc8HWxRrw",
    "authDomain": "tracker-81552.firebaseapp.com",
    "projectId": "tracker-81552",
    "storageBucket": "tracker-81552.appspot.com",
    "messagingSenderId": "546833361242",
    "appId": "1:546833361242:web:a26d211bc6a6ecee87ab63",
    "measurementId": "G-824XRSR6PG",
    "databaseURL": ""
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Initialize Firebase Admin with service account credentials
cred = credentials.Certificate("C:/Users/prana/Documents/ts.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Function to initialize Firestore with sample data
def initialize_firestore_data():
    # Check and populate 'students' collection
    students_ref = db.collection("students")
    if not students_ref.get():
        students_ref.document("1").set({
            "name": "John Doe",
            "age": 16,
            "class": "10-A",
            "contact_info": "johndoe@example.com",
            "firebase_uid": None  # To be set when user account is created
        })
        st.write("Added sample student to 'students' collection.")

    # Check and populate 'subjects' collection
    subjects_ref = db.collection("subjects")
    if not subjects_ref.get():
        subjects_ref.add({"subject_name": "ENGLISH"})
        subjects_ref.add({"subject_name": "MATHS"})
        subjects_ref.add({"subject_name": "SCIENCE"})
        subjects_ref.add({"subject_name": "ART"})
        st.write("Added sample subjects to 'subjects' collection.")

# Create a student entry in Firestore
def create_student_entry(email, firebase_uid):
    students_ref = db.collection("students")
    students_ref.add({
        "name": email.split("@")[0],  # Use email prefix as name
        "age": 16,  # Placeholder value
        "class": "10-A",  # Placeholder value
        "contact_info": email,
        "firebase_uid": firebase_uid
    })
    st.success("Student entry created successfully.")

# Create a teacher entry in Firestore
def create_teacher_entry(name, subject_name, class_assigned, firebase_uid):
    subjects_ref = db.collection("subjects").where("subject_name", "==", subject_name).stream()
    for subject in subjects_ref:
        subject_id = subject.id
        teachers_ref = db.collection("teachers")
        teacher_data = {
            "name": name,
            "subject_id": subject_id,
            "class_assigned": class_assigned,
            "firebase_uid": firebase_uid 
        }
        teachers_ref.add(teacher_data)
        st.success("Teacher entry created successfully.")

# Post a new assignment
def post_assignment(title, description, due_date, subject_name, class_assigned):
    subject_doc = db.collection("subjects").where("subject_name", "==", subject_name).get()
    if subject_doc:
        assignment_data = {
            "title": title,
            "due_date": due_date,
            "subject_id": subject_doc[0].id,
            "class_assigned": class_assigned
        }
        db.collection("assignments").add(assignment_data)
        st.success("Assignment posted successfully.")

# Fetch student information
def fetch_student_info(firebase_uid):
    students_ref = db.collection("students").where("firebase_uid", "==", firebase_uid).stream()
    for student in students_ref:
        return student.to_dict()
    return None

# Fetch grades for the student
def fetch_grades(firebase_uid):
    grades_ref = db.collection("grades").where("student_uid", "==", firebase_uid).stream()
    return [grade.to_dict() for grade in grades_ref]

# Fetch assignments for the student
def fetch_assignments(class_assigned):
    assignments_ref = db.collection("assignments").where("class_assigned", "==", class_assigned).stream()
    return [assignment.to_dict() for assignment in assignments_ref]

# Display student dashboard
def student_dashboard(firebase_uid):
    st.title("Student Dashboard")

    student_info = fetch_student_info(firebase_uid)
    if student_info:
        st.write("### Student Details")
        st.write(f"**Name:** {student_info.get('name')}")
        st.write(f"**Age:** {student_info.get('age')}")
        st.write(f"**Class:** {student_info.get('class')}")
        st.write(f"**Contact Info:** {student_info.get('contact_info')}")

        # Display grades
        st.write("### Grades Overview")
        grades = fetch_grades(firebase_uid)
        if grades:
            st.write(pd.DataFrame(grades))
        else:
            st.write("No grades available.")

        # Display assignments
        st.write("### Assignment Details")
        assignments = fetch_assignments(student_info.get('class'))
        if assignments:
            st.write(pd.DataFrame(assignments))
        else:
            st.write("No assignments available.")

# Display teacher panel
# Display teacher panel
def teacher_panel(firebase_uid):
    st.title("Teacher Panel")
    
    # Create input fields for teacher details (to create a new account)
    name = st.text_input("Teacher Name")
    subject_name = st.selectbox("Subject", ["ENGLISH", "MATHS", "SCIENCE", "ART"])
    class_assigned = st.selectbox("Class Assigned", ["10-A", "10-B", "10-C"], index=0)

    # Create account button
    if st.button("Create Teacher Account"):
        if name:
            create_teacher_entry(name, subject_name, class_assigned, firebase_uid)
        else:
            st.error("Please fill in all fields before creating a teacher account.")

    st.subheader("Post New Assignment")
    
    # Create input fields for assignment details
    title = st.text_input("Assignment Title")
    due_date = st.date_input("Due Date")

    # Post assignment button
    if st.button("Post Assignment"):
        if title and due_date:
            try:
                post_assignment(title, "", due_date, subject_name, class_assigned)  # Pass an empty string for description
            except Exception as e:
                st.error(f"Failed to post assignment: {str(e)}")
        else:
            st.error("Please fill in all fields before posting the assignment.")

    # Display current assignments for the assigned class
    st.subheader("Current Assignments")
    assignments = fetch_assignments(class_assigned)
    if assignments:
        st.write(pd.DataFrame(assignments))
    else:
        st.write("No assignments available for this class.")

    # Ensure that UI elements are rendered correctly
    st.markdown("---")  # Add a separator for better visual clarity



# Main function to run the Streamlit app
def main():
    st.title("Performance Tracker")
    user_type = st.selectbox("Are you a:", ("Select", "Teacher", "Student"))

    if user_type != "Select":
        action = st.radio("Login or Create an Account", ("Login", "Create Account"))

        if action == "Create Account":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Create Account"):
                try:
                    user = auth.create_user_with_email_and_password(email, password)
                    st.success(f"Account created for {email}")

                    # Save Firebase UID based on user type
                    firebase_uid = user['localId']
                    if user_type == "Student":
                        create_student_entry(email, firebase_uid)
                        student_dashboard(firebase_uid)
                    elif user_type == "Teacher":
                        create_teacher_entry(email.split("@")[0], "ENGLISH", "10-A", firebase_uid)
                        teacher_panel(firebase_uid)

                except Exception as e:
                    st.error(e)

        elif action == "Login":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    st.success(f"Welcome, {email}")

                    # Retrieve Firebase UID and pass it to the dashboard based on user type
                    firebase_uid = user['localId']
                    if user_type == "Student":
                        student_dashboard(firebase_uid)
                    elif user_type == "Teacher":
                        teacher_panel(firebase_uid)

                except Exception as e:
                    st.error(e)

if __name__ == "__main__":
    initialize_firestore_data()  # Initialize Firestore with sample data
    main()