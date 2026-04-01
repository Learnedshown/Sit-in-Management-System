from db_helper import execute
from datetime import datetime
from models.student_models import (
    view_students,
    update_student,
    delete_students
)

# ---------------------------
# ADMIN LOGIN
# ---------------------------
def admin_verify_password(id_number, password):
    return execute(
        "SELECT * FROM admins WHERE id_number = ? AND password = ?",
        (id_number, password),
        fetchone=True
    )


# ---------------------------
# SEARCH STUDENT (REUSE VIEW)
# ---------------------------
def search_student(keyword):
    return execute(
        """SELECT * FROM students 
           WHERE id_number LIKE ? 
           OR first_name LIKE ? 
           OR last_name LIKE ?""",
        (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"),
        fetchall=True
    )

def reset_all_sessions():
    return execute("""
        UPDATE students
        SET sessions_remaining = 30,
            total_session_used = 0
    """, commit=True)


# ---------------------------
# START SIT-IN
# ---------------------------
def start_sitin(data):
    student = view_students(data["id_number"])  # ✅ reused

    if not student:
        raise Exception("Student not found")
    
    if is_already_sitin(student["id"]):
        raise Exception("Student already has an active session!")
    
    if is_pc_in_use(data.get("pc_number"), data.get("lab_room")):
        raise Exception(f"PC {data.get('pc_number')} in {data.get('lab_room')} is already in use!")

    if student["sessions_remaining"] <= 0:
        raise Exception("No sessions remaining")

    now = datetime.now()

    # ✅ INSERT SESSION HISTORY
    execute("""
        INSERT INTO sessions_history 
        (student_id, login_time, session_date, pc_number, lab_room, purpose)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        student["id"],
        now.strftime("%H:%M:%S"),
        now.strftime("%Y-%m-%d"),
        data.get("pc_number"),
        data.get("lab_room"),
        data.get("purpose")
    ), commit=True)

    # ✅ UPDATE SESSION (REUSE LOGIC STYLE)
    execute("""
        UPDATE students
        SET sessions_remaining = sessions_remaining - 1,
            total_session_used = total_session_used + 1
        WHERE id = ?
    """, (student["id"],), commit=True)


# ---------------------------
# END SIT-IN
# ---------------------------
def end_sitin(session_id):
    now = datetime.now()

    execute("""
        UPDATE sessions_history
        SET logout_time = ?
        WHERE session_id = ?
    """, (now.strftime("%H:%M:%S"), session_id), commit=True)





def view_current_sitin():
    query = """
    SELECT 
        sh.session_id AS sit_id,
        s.id_number,
        s.first_name || ' ' || s.last_name AS name,
        sh.purpose,
        sh.lab_room AS sit_lab,
        sh.pc_number AS session,
        CASE 
            WHEN sh.logout_time IS NULL THEN 'Active'
            ELSE 'Ended'
        END AS status,
        sh.login_time
    FROM sessions_history sh
    JOIN students s ON sh.student_id = s.id
    WHERE sh.logout_time IS NULL
    ORDER BY sh.login_time DESC
    """

    sitins = execute(query, fetchall=True)
    return sitins

# ---------------------------
# VIEW SIT-IN RECORDS
# ---------------------------
def view_sitin_records():
    return execute("""
        SELECT sh.session_id, s.id_number, s.first_name, s.last_name,
               sh.login_time, sh.logout_time,
               sh.session_date, sh.pc_number, sh.lab_room
        FROM sessions_history sh
        JOIN students s ON sh.student_id = s.id
        ORDER BY sh.session_date DESC
    """, fetchall=True)


# ---------------------------
# ADMIN ACTIONS (REUSE)
# ---------------------------
def admin_update_student(data):
    return update_student(data)  # ✅ reused

def admin_delete_student(id_number):
    return delete_students(id_number)  # ✅ reused


#ADMIN ANNOUNCEMENT
def add_announcement(data):
    query = """ INSERT into announcements (content) 
                VALUES (?)
            """
    execute(query, (data["content"],), commit=True )

def get_announcement():
    query = "SELECT * FROM announcements ORDER BY created_at DESC"
    return execute(query, fetchall=True)

def view_all_sitin_purposes():
    return execute("""
        SELECT purpose
        FROM sessions_history
    """, fetchall=True)

def is_already_sitin(student_id):
    return execute("""
        SELECT 1 FROM sessions_history
        WHERE student_id = ?
        AND logout_time IS NULL
    """, (student_id,), fetchone=True)

def is_pc_in_use(pc_number, lab_room):
    return execute("""
        SELECT 1 FROM sessions_history
        WHERE pc_number = ?
        AND lab_room = ?
        AND logout_time IS NULL
    """, (pc_number, lab_room), fetchone=True)

def admin_update_student(data):
    student = view_students(data["id_number"])
    if not student:
        raise Exception("Student not Found")
    
    query = """UPDATE students SET first_name = ?, middle_name = ?, last_name = ?, course_level = ?, course = ?, email = ?, address = ?, sessions_remaining = ? WHERE id_number = ?"""
    execute(query, (data["first_name"],
                    data["middle_name"],
                    data["last_name"],
                    data["course_level"],
                    data["course"],
                    data["email"],
                    data["address"],
                    data["sessions_remaining"],  
                    data["id_number"]  
                   ),
                        commit=True
            )