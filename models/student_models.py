from db_helper import execute
from werkzeug.security import generate_password_hash, check_password_hash

def register_students(data):
    hashed_pw = generate_password_hash(data["password"])
    query = """ 
        INSERT INTO students(
            id_number, first_name, middle_name, last_name,
            course_level, course, password, email, address, points
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """ 

    execute(query, (data["id_number"],
                    data["first_name"],
                    data["middle_name"],
                    data["last_name"],
                    data["course_level"],
                    data["course"],
                    hashed_pw,
                    data["email"],
                    data["address"],   
                  ), 
                    commit=True
           )

 
def view_students(id_number):
    query = "SELECT * FROM students WHERE id_number = ?" 
    return execute(query, (id_number,), fetchone=True)
def delete_students(id_number):
  
    student = execute(
        "SELECT id FROM students WHERE id_number = ?",
        (id_number,),
        fetchone=True
    )

    if not student:
        raise Exception("Student not found")

    student_id = student["id"]
    execute("DELETE FROM sessions_history WHERE student_id = ?", (student_id,))

    execute("DELETE FROM students WHERE id_number = ?", (id_number,), commit=True)


""" DELETE STUDENT (SOFT)
def delete_students(id_number):

    student = execute(
        "SELECT id FROM students WHERE id_number = ? AND is_deleted = 0",
        (id_number,),
        fetchone=True
    )

    if not student:
        raise Exception("Student not found")

    student_id = student["id"]

    execute(
        "UPDATE sessions_history SET is_deleted = 1 WHERE student_id = ?",
        (student_id,)
    )

    execute(
        "UPDATE students SET is_deleted = 1 WHERE id_number = ?",
        (id_number,),
        commit=True
    )

def delete_session(session_id, student_id):
   execute(
      "UPDATE sessions_history SET is_deleted = 1 WHERE id = ? AND student_id ?",
      (session_id, student_id),
      commit=True
   )

def delete_student_account(student_id):
   execute(
      "UPDATE students SET is_deleted = 1 WHERE id = ?",
      (student_id,),
      commit=True
   )
"""

def update_student(data):
   student = view_students(data["id_number"])
   if not student:
    raise Exception("Student not found")

   query = """UPDATE students set first_name = ?, middle_name = ?, last_name = ?, course_level = ?, course = ?, email = ?, address = ?, profile_photo = ? WHERE id_number = ?"""
   execute(query, ( data["first_name"],
                    data["middle_name"],
                    data["last_name"],
                    data["course_level"],
                    data["course"],
                    data["email"],
                    data["address"],
                    data["profile_photo"],  
                    data["id_number"] 
                  ),
                      commit=True
            )
   
def change_student_password(data):
    student = view_students(data["id_number"])

    if not student:
        raise Exception("Student not found")

    hash_pw = generate_password_hash(data["password"])

    query = """ UPDATE students SET password = ? WHERE id_number = ? """
    execute(query, (hash_pw, data["id_number"]), commit=True)

def student_session(data):
    student = view_students(data["id_number"])

    if not student:
        raise Exception("Student not found")

    if student["sessions_remaining"] <= 0:
        raise Exception("No sessions remaining")

    query = """
        UPDATE students 
        SET sessions_remaining = sessions_remaining - 1,
            total_session_used = total_session_used + 1,
            points = points + 1
        WHERE id_number = ?
    """

    execute(query, (data["id_number"],), commit=True)


def student_verify_password(id_number, password):
   student = view_students(id_number)

   if student is None:
      return False
   return check_password_hash(student["password"], password)


def view_all_students():
    query = "SELECT * FROM students"
    return execute(query, fetchall=True)

# ---------------------------
# STUDENT FEEDBACK
# ---------------------------
def save_feedback(session_id, message, rating):
    return execute("""
        INSERT INTO feedback (session_id, message, rating)
        VALUES (?, ?, ?)
    """, (session_id, message, rating), commit=True)

def get_student_feedback(student_id):
    return execute("""
        SELECT message, rating, created_at
        FROM feedback
        WHERE student_id = ?
        ORDER BY created_at DESC
    """, (student_id,), fetchall=True)

def get_student_points(id_number):
    return execute("""
        SELECT points FROM students WHERE id_number = ?
    """, (id_number,), fetchone=True)


def get_student_sitin_history(student_id):
    return execute("""
        SELECT * FROM sessions_history
        WHERE student_id = ? AND is_deleted = 0
        ORDER BY session_date DESC
    """, (student_id,), fetchall=True)

def get_student_history_with_feedback(student_id):
    return execute("""
        SELECT 
            sh.session_id,
            sh.session_date,
            sh.login_time,
            sh.logout_time,
            sh.purpose,
            sh.pc_number,
            sh.lab_room,
            f.message,
            f.rating
        FROM sessions_history sh
        LEFT JOIN feedback f 
            ON sh.session_id = f.session_id
        WHERE sh.student_id = ?
        ORDER BY sh.session_date DESC
    """, (student_id,), fetchall=True)