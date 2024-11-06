import streamlit as st
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.graph_objects as go

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
@st.cache_data





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
def post_assignment(title, description, due_date, subject_name, class_assigned, teacher_name):
    # Retrieve the subject document
    subject_doc = db.collection("subjects").where("subject_name", "==", subject_name).get()
    
    # Ensure subject exists
    if subject_doc:
        subject_id = subject_doc[0].id  # Get subject_id from the document
        assignment_data = {
            "title": title,
            "description": description,
            "due_date": due_date.strftime("%Y-%m-%d"),  # Convert date to string format
            "subject_id": subject_id,
            "class_assigned": class_assigned,
            "teacher_name": teacher_name  # Store teacher's name for display in student panel
        }
        
        # Attempt to add the assignment
        try:
            db.collection("assignments").add(assignment_data)
            st.success("Assignment posted successfully.")
        except Exception as e:
            st.error(f"Failed to post assignment: {str(e)}")
    else:
        st.error("Subject not found. Please select a valid subject.")



def submit_grade(firebase_uid, subject_name, grade):
    grades_ref = db.collection("grades")
    grades_ref.add({
        "student_uid": firebase_uid,
        "subject_name": subject_name,
        "grade": grade
    })
    st.success("Grade submitted successfully.")



# Fetch student information
def fetch_student_info(firebase_uid):
    students_ref = db.collection("students").where("firebase_uid", "==", firebase_uid).stream()
    for student in students_ref:
        return student.to_dict()
    return None



# Fetch grades for the student
def fetch_latest_grades(firebase_uid):
    # Fetch all grades for the student
    grades_ref = db.collection("grades").where("student_uid", "==", firebase_uid).stream()
    grades_by_subject = {}

    for grade in grades_ref:
        grade_data = grade.to_dict()
        subject_name = grade_data['subject_name']
        
        # Keep only the latest grade entry for each subject
        # Since there's no timestamp, you can choose to just overwrite the existing entry
        # This assumes the last entry fetched is the most recent, which may not always be true.
        grades_by_subject[subject_name] = grade_data

    # Return only the latest grade entries
    return list(grades_by_subject.values())



# Fetch assignments for the student
def fetch_class_assignments(class_assigned):
    assignments_ref = db.collection("assignments").where("class_assigned", "==", class_assigned).stream()
    formatted_assignments = []
    
    for assignment in assignments_ref:
        assignment_data = assignment.to_dict()
        teacher_name = assignment_data.get('teacher_name', 'Unknown')
        formatted_text = f"{assignment_data['title']} ({assignment_data['description']}) - {teacher_name}"
        formatted_assignments.append(formatted_text)
    
    return formatted_assignments


# Display student dashboard

def fetch_teacher_info(firebase_uid):
    """
    Fetches teacher information from Firestore based on the provided firebase_uid.
    
    Args:
        firebase_uid (str): The unique identifier for the teacher in Firebase.
        
    Returns:
        dict: A dictionary containing the teacher's information, or None if the teacher is not found.
    """
    try:
        # Query the 'teachers' collection to find the document with the specified firebase_uid
        teacher_ref = db.collection("teachers").where("firebase_uid", "==", firebase_uid).stream()
        
        # Get the first matching document (if any)
        for doc in teacher_ref:
            return doc.to_dict()  # Return teacher information as a dictionary
        
        # If no matching teacher is found, return None
        return None
    except Exception as e:
        print(f"Error fetching teacher info: {e}")
        return None
def student_dashboard(firebase_uid):
    st.title("Student Dashboard")

    # Fetch student info
    student_info = fetch_student_info(firebase_uid)
    if student_info:
        st.write("### Student Details")
        st.write(f"**Name:** {student_info.get('name')}")
        st.write(f"**Age:** {student_info.get('age')}")
        st.write(f"**Class:** {student_info.get('class')}")
        st.write(f"**Contact Info:** {student_info.get('contact_info')}")

        # Fetch grades
        st.write("### Grades Overview")
        grades=fetch_latest_grades(firebase_uid)

        if grades:
            # Prepare data for plotting
            subjects = [grade['subject_name'] for grade in grades]
            marks = [grade['grade'] for grade in grades]

            # Create a 3D bar chart using Plotly
            fig = go.Figure(data=[go.Bar(
                x=subjects,
                y=marks,
                marker=dict(color='royalblue', line=dict(color='black', width=2))
            )])

            # Update layout for a better appearance
            fig.update_layout(
                title='Grades Overview',
                scene=dict(
                    xaxis_title='Subjects',
                    yaxis_title='Grades',
                    zaxis_title='Count',
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5)  # Adjust camera for better 3D perspective
                    )
                ),
                margin=dict(l=0, r=0, b=0, t=40),  # Adjust margins
                width=700,
                height=500
            )

            # Render the plot in Streamlit
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No grades available.")

        # Display assignments in text format
        st.write("### Assignment Details")
        assignments = fetch_class_assignments(student_info.get('class'))
        if assignments:
            for i, assignment in enumerate(assignments, start=1):
                st.write(f"Assignment {i}: {assignment}")
        else:
            st.write("No assignments available.")




def fetch_students(class_assigned):
    students_ref = db.collection("students").where("class", "==", class_assigned).stream()
    students = []
    for student in students_ref:
        student_data = student.to_dict()
        student_data['id'] = student.id  # Optionally store the document ID
        students.append(student_data)
    return students



# Fetch assigned subjects for a specific class
def fetch_assigned_subjects(class_assigned):
    teachers_ref = db.collection("teachers").where("class_assigned", "==", class_assigned).stream()
    
    for teacher in teachers_ref:
        teacher_data = teacher.to_dict()
        
        # Use get to safely access 'subject_id'
        subject_id = teacher_data.get('subject_id')
        if subject_id:
            # Fetch the subject document
            subject_doc = db.collection("subjects").document(subject_id).get()
            if subject_doc.exists:
                # Return the subject name directly
                return subject_doc.to_dict().get("subject_name")
    
    # Return None if no subject was found
    return None
    





def create_teacher_entry(name, subject_name, class_assigned, firebase_uid):
    # Check if the subject exists first
    subjects_ref = db.collection("subjects").where("subject_name", "==", subject_name).stream()
    subject_ids = [subject.id for subject in subjects_ref]

    if subject_ids:
        subject_id = subject_ids[0]
        teachers_ref = db.collection("teachers")
        teacher_data = {
            "name": name,
            "subject_id": subject_id,
            "class_assigned": class_assigned,
            "firebase_uid": firebase_uid 
        }
        teachers_ref.add(teacher_data)
        st.success("Teacher entry created successfully.")
    else:
        st.error("Subject does not exist. Teacher entry not created.")
        
def fetch_assigned_subjects_for_teacher(firebase_uid):
    # Assuming you have a collection "teachers" in your database
    teacher_ref = db.collection("teachers").where("firebase_uid", "==", firebase_uid).stream()
    
    subjects = {}  # Initialize an empty dictionary for subjects

    # Iterate through the teacher records to collect registered subjects
    for teacher in teacher_ref:
        teacher_data = teacher.to_dict()
        class_assigned = teacher_data.get('class_assigned')
        subject_id = teacher_data.get('subject_id')
        
        # Ensure both class and subject are present to avoid assigning unintended subjects
        if class_assigned and subject_id:
            subject_ref = db.collection("subjects").document(subject_id).get()
            
            # Check if the subject document exists to avoid missing subjects
            if subject_ref.exists:
                subject_name = subject_ref.to_dict().get('subject_name')
                
                # Initialize the list for this class if it's not already in subjects
                if class_assigned not in subjects:
                    subjects[class_assigned] = []
                
                subjects[class_assigned].append(subject_name)
    
    # Return the collected subjects; if no subjects were found, return an empty dictionary
    return subjects

def fetch_assignments(class_name, subject_name):
    assignments_ref = db.collection("assignments").where("class_assigned", "==", class_name).where("subject_name", "==", subject_name).stream()
    assignments = []
    
    for assignment in assignments_ref:
        assignments.append(assignment.to_dict())
    
    return assignments

def teacher_panel(firebase_uid):
    
    if 'teacher_name' not in st.session_state:
        st.session_state.teacher_name = "Default Teacher Name"

    # Fetch teacher info and set session state
    teacher_info = fetch_teacher_info(firebase_uid)
    if teacher_info:
        st.session_state.teacher_name = teacher_info.get('name')

    # Initialize assigned subjects for each class with empty strings
    classes = ["10-A", "10-B", "10-C"]
    if "assigned_subjects" not in st.session_state:
        st.session_state.assigned_subjects = {class_name: "" for class_name in classes}

    # Fetch the teacher's assigned subjects
    teacher_subjects = fetch_assigned_subjects_for_teacher(firebase_uid)

    # Set assigned subjects based on fetched subjects
    for class_name in classes:
        if teacher_subjects and teacher_subjects.get(class_name):
            st.session_state.assigned_subjects[class_name] = teacher_subjects[class_name][0]  # Set to the first subject found
        else:
            st.session_state.assigned_subjects[class_name] = ""  # No subjects registered

    # Display assigned subjects
    st.subheader("Assigned Subjects")
    for class_name in classes:
        subject = st.session_state.assigned_subjects.get(class_name, "")
        if not subject:
            st.write(f"**Class {class_name}:** No subjects registered.")
        else:
            st.write(f"**Class {class_name}:** {subject}")

    # Section for assigning grades
    st.subheader("Assign Grades")
    selected_class = st.selectbox("Select Class to Assign Grades", classes)

    subject_name = st.session_state.assigned_subjects[selected_class]
    if subject_name:
        st.write(f"**Subject:** {subject_name}")

        # Fetch students for the selected class
        students = fetch_students(selected_class)
        student_count = len(students)

        # Show total student count for the selected class
        st.write(f"**Total Students in {selected_class}:** {student_count}")

        if students:
            student_names = [student['name'] for student in students]
            selected_student = st.selectbox("Select Student", student_names)
            student_uid = next(student['firebase_uid'] for student in students if student['name'] == selected_student)

            # Input for grade
            grade = st.number_input("Grade", min_value=0, max_value=100, step=1)

            # Button to submit grade
            if st.button("Submit Grade"):
                try:
                    submit_grade(student_uid, subject_name, grade)
                    st.success("Grade submitted successfully!")
                except Exception as e:
                    st.error(f"Error submitting grade: {str(e)}")
        else:
            st.write("No students available to assign grades.")
    else:
        st.error("No subject registered for this class to assign grades.")

    # Section for applying to teach a new subject
    st.subheader("Apply to Teach a New Subject")
    class_to_teach = st.selectbox("Select Class to Teach", classes)

    available_subjects = get_subjects()
    assigned_in_class = fetch_assigned_subjects(class_to_teach)
    available_subjects = [subject for subject in available_subjects if subject not in (assigned_in_class or [])]


    if available_subjects:
        selected_subject = st.selectbox("Select a Subject to Teach", available_subjects)

        if st.button("Apply to Teach"):
            existing_teachers = db.collection("teachers").where("class_assigned", "==", class_to_teach).where("subject_id", "==", selected_subject).stream()
            if any(existing_teachers):
                st.error(f"The subject '{selected_subject}' is already assigned in {class_to_teach}.")
            else:
                subjects_ref = db.collection("subjects").where("subject_name", "==", selected_subject).stream()
                subject_id = next((subject.id for subject in subjects_ref), None)

                if subject_id:
                    # Update session state to reflect the new subject assignment
                    st.session_state.assigned_subjects[class_to_teach] = selected_subject  # Replace previous subject
                    create_teacher_entry(st.session_state.teacher_name, selected_subject, class_to_teach, firebase_uid)
                    st.success(f"Assigned to teach {selected_subject} in {class_to_teach}.")
                    st.rerun()  # Refresh the app to show updated subjects
                else:
                    st.error(f"Subject '{selected_subject}' does not exist.")
    else:
        st.write("No available subjects to teach for this class.")

    # Post New Assignment Section
    st.subheader("Post New Assignment")
    class_assigned_for_assignment = st.selectbox("Select Class for Assignment", classes)

    # Check if the teacher is registered for any subject in the selected class
    subject_name = st.session_state.assigned_subjects[class_assigned_for_assignment]
    if subject_name:
        title = st.text_input("Assignment Title")
        description = st.text_area("Assignment Description")
        due_date = st.date_input("Due Date")

        if st.button("Post Assignment"):
            if title and description and due_date:
                try:
                    post_assignment(title, description, due_date, subject_name, class_assigned_for_assignment, st.session_state.teacher_name)
                    st.success("Assignment posted successfully!")

                    # Immediately fetch the assignments after posting
                    assignments = fetch_assignments(class_assigned_for_assignment, subject_name)
                    st.session_state.current_assignments[class_assigned_for_assignment] = assignments
                except Exception as e:
                    st.error(f"Failed to post assignment: {str(e)}")
            else:
                st.error("Please fill in all fields before posting the assignment.")
    else:
        st.error("No subject registered for this class to post an assignment.")



    
def post_assignment(title, description, due_date, subject_name, class_assigned_for_assignment, teacher_name):
    # Create a dictionary to hold the assignment data
    assignment_data = {
        "title": title,
        "description": description,
        "due_date": due_date.isoformat(),  # Store due date in a standard format
        "subject_name": subject_name,
        "class_assigned": class_assigned_for_assignment,
        "teacher_name": teacher_name  # Save the teacher's actual name
    }
    
    # Add the assignment to the database
    db.collection("assignments").add(assignment_data)







def sign_out():
    st.session_state.clear()  # Clear session state
    st.success("You have been signed out.")
    st.rerun()  # This should work if you're on an appropriate version of Streamlit


def get_subjects():
    subjects_ref = db.collection("subjects").stream()
    return [subject.to_dict()["subject_name"] for subject in subjects_ref]
# Main function to run the Streamlit app



def main():
    

# Set the page configuration
    st.set_page_config(page_title="Student Performance Tracker", layout="wide")

# Custom CSS for a 3D gradient theme
    st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #84fab0, #8fd3f4); /* Gradient background */
        color: #2c3e50; /* Dark text color for readability */
        font-family: 'Arial', sans-serif;
        padding: 20px;
        border-radius: 15px; /* Rounded corners */
    }

    /* Adding some 3D effects */
    .card {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Shadow effect */
        transition: transform 0.2s; /* Smooth hover effect */
    }

    .card:hover {
        transform: scale(1.05); /* Scale up on hover */
    }
</style>
""", unsafe_allow_html=True)

# Example of a card element
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("Performance Tracker")
    st.write("Welcome to the performance tracker. Here, you can view and analyze student performance.")
    st.markdown('</div>', unsafe_allow_html=True)

# Your application logic here...


# Your application logic here...


    # Check if user is logged in
    if "firebase_uid" not in st.session_state:
        user_type = st.selectbox("Are you a:", ("Select", "Teacher", "Student"))

        if user_type != "Select":
            action = st.radio("Login or Create an Account", ("Login", "Create Account"))

            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if action == "Create Account" and st.button("Create Account"):
                try:
                    user = auth.create_user_with_email_and_password(email, password)
                    firebase_uid = user['localId']
                    st.session_state["firebase_uid"] = firebase_uid
                    st.session_state["user_type"] = user_type

                    if user_type == "Student":
                        create_student_entry(email, firebase_uid)
                    elif user_type == "Teacher":
                        create_teacher_entry(email.split("@")[0], "ENGLISH", "10-A", firebase_uid)

                    st.success("Account created successfully! Please log in.")

                except Exception as e:
                    st.error(e)

            elif action == "Login" and st.button("Login"):
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    firebase_uid = user['localId']
                    st.session_state["firebase_uid"] = firebase_uid
                    st.session_state["user_type"] = user_type
                    st.success("Logged in successfully!")
                    st.rerun()  # This should work if you're on an appropriate version of Streamlit
  # Re-render after login to show the correct dashboard

                except Exception as e:
                    st.error(e)

    else:  # User is logged in
        if st.session_state["user_type"] == "Teacher":
            teacher_panel(st.session_state["firebase_uid"])
        elif st.session_state["user_type"] == "Student":
            student_dashboard(st.session_state["firebase_uid"])

        if st.button("Sign Out"):
            sign_out()  # Call sign_out to handle logout

if __name__ == "__main__":
    initialize_firestore_data()
    main()

