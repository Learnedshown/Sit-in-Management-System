from db_helper import execute
from werkzeug.security import generate_password_hash, check_password_hash

def register_students(data):
    hashed_pw = generate_password_hash(data["password"])
    query = """ 
        INSERT INTO students(id_number, first_name, middle_name, last_name, course_level, course, password, email, address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
   query = "DELETE FROM students WHERE id_number = ?"
   execute(query, (id_number,), commit=True)

def update_student(data):
   view_students(data["id_number"])

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


def student_session(data):
  
   view_students(data["id_number"])
   
   query = """ UPDATE students set sessions_remaining = sessions_remaining - 1, total_session_used = total_session_used + 1 WHERE id_number = ? AND sessions_remaining > 0 """
   execute(query, (data["id_number"],
                   ),
                   commit=True
          )


def student_verify_password(id_number, password):
   student = view_students(id_number)

   if student is None:
      return False
   return check_password_hash(student["password"], password)


def view_all_students():
    query = "SELECT * FROM students"
    return execute(query, fetchall=True)