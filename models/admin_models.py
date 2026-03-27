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


# ---------------------------
# START SIT-IN
# ---------------------------
def start_sitin(data):
    student = view_students(data["id_number"])  # ✅ reused

    if not student:
        raise Exception("Student not found")

    if student["sessions_remaining"] <= 0:
        raise Exception("No sessions remaining")

    now = datetime.now()

    # ✅ INSERT SESSION HISTORY
    execute("""
        INSERT INTO sessions_history 
        (student_id, login_time, session_date, pc_number, lab_room)
        VALUES (?, ?, ?, ?, ?)
    """, (
        student["id"],
        now.strftime("%H:%M:%S"),
        now.strftime("%Y-%m-%d"),
        data.get("pc_number"),
        data.get("lab_room")
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


# ---------------------------
# VIEW CURRENT SIT-IN
# ---------------------------
def view_current_sitin():
    return execute("""
        SELECT sh.session_id, s.id_number, s.first_name, s.last_name,
               sh.login_time, sh.pc_number, sh.lab_room
        FROM sessions_history sh
        JOIN students s ON sh.student_id = s.id
        WHERE sh.logout_time IS NULL
    """, fetchall=True)


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