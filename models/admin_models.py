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

    # get login time
    session = execute("""
        SELECT login_time, session_date
        FROM sessions_history
        WHERE session_id = ?
    """, (session_id,), fetchone=True)

    start = datetime.strptime(
        f"{session['session_date']} {session['login_time']}",
        "%Y-%m-%d %H:%M:%S"
    )

    end = now

    hours = (end - start).total_seconds() / 3600

    execute("""
        UPDATE sessions_history
        SET logout_time = ?, hours_rendered = ?
        WHERE session_id = ?
    """, (now.strftime("%H:%M:%S"), hours, session_id), commit=True)





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
    

# ---------------------------
# ANALYTICS
# ---------------------------
def get_total_students():
    return execute("SELECT COUNT(*) as total FROM students", fetchone=True)

def get_total_sitin_sessions():
    return execute("SELECT COUNT(*) as total FROM sessions_history", fetchone=True)

def get_daily_sitin_counts():
    return execute("""
        SELECT session_date, COUNT(*) as count
        FROM sessions_history
        GROUP BY session_date
        ORDER BY session_date ASC
    """, fetchall=True)

def get_top_students(limit=5):
    return execute("""
        SELECT first_name, last_name, total_session_used
        FROM students
        ORDER BY total_session_used DESC
        LIMIT ?
    """, (limit,), fetchall=True)


# ---------------------------
# REWARDS / POINTS SYSTEM
# ---------------------------
def add_points(id_number, points):
    return execute("""
        UPDATE students
        SET points = points + ?
        WHERE id_number = ?
    """, (points, id_number), commit=True)


def deduct_points(id_number, points):
    return execute("""
        UPDATE students
        SET points = MAX(points - ?, 0)
        WHERE id_number = ?
    """, (points, id_number), commit=True)
from db_helper import execute


# ---------------------------
# GET ALL SESSIONS FOR REWARD PAGE
# ---------------------------
def get_reward_sessions():
    return execute("""
        SELECT 
            sh.session_id,
            s.id_number,
            s.first_name,
            s.last_name,
            sh.session_date,
            sh.purpose,
            sh.status,
            sh.points_awarded,
            sh.is_rewarded
        FROM sessions_history sh
        JOIN students s ON sh.student_id = s.id
        WHERE sh.is_deleted = 0
        AND sh.logout_time IS NOT NULL
        ORDER BY sh.session_date DESC
    """, fetchall=True)

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

    # get login time
    session = execute("""
        SELECT login_time, session_date
        FROM sessions_history
        WHERE session_id = ?
    """, (session_id,), fetchone=True)

    start = datetime.strptime(
        f"{session['session_date']} {session['login_time']}",
        "%Y-%m-%d %H:%M:%S"
    )

    end = now

    hours = (end - start).total_seconds() / 3600

    execute("""
        UPDATE sessions_history
        SET logout_time = ?, hours_rendered = ?
        WHERE session_id = ?
    """, (now.strftime("%H:%M:%S"), hours, session_id), commit=True)





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
    

# ---------------------------
# ANALYTICS
# ---------------------------
def get_total_students():
    return execute("SELECT COUNT(*) as total FROM students", fetchone=True)

def get_total_sitin_sessions():
    return execute("SELECT COUNT(*) as total FROM sessions_history", fetchone=True)

def get_daily_sitin_counts():
    return execute("""
        SELECT session_date, COUNT(*) as count
        FROM sessions_history
        GROUP BY session_date
        ORDER BY session_date ASC
    """, fetchall=True)

def get_top_students(limit=5):
    return execute("""
        SELECT first_name, last_name, total_session_used
        FROM students
        ORDER BY total_session_used DESC
        LIMIT ?
    """, (limit,), fetchall=True)


# ---------------------------
# REWARDS / POINTS SYSTEM
# ---------------------------
def add_points(id_number, points):
    return execute("""
        UPDATE students
        SET points = points + ?
        WHERE id_number = ?
    """, (points, id_number), commit=True)


def deduct_points(id_number, points):
    return execute("""
        UPDATE students
        SET points = MAX(points - ?, 0)
        WHERE id_number = ?
    """, (points, id_number), commit=True)
from db_helper import execute


# ---------------------------
# GET ALL SESSIONS FOR REWARD PAGE
# ---------------------------
def get_reward_sessions():
    return execute("""
        SELECT 
            sh.session_id,
            s.id_number,
            s.first_name,
            s.last_name,
            sh.session_date,
            sh.purpose,
            sh.status,
            sh.points_awarded,
            sh.is_rewarded
        FROM sessions_history sh
        JOIN students s ON sh.student_id = s.id
        ORDER BY sh.session_date DESC
    """, fetchall=True)

# ---------------------------
# AWARD POINTS (Updated - 1 point only)
# ---------------------------
def award_points(session_id, student_id, award=True):
    # check if already rewarded
    session = execute("""
        SELECT is_rewarded FROM sessions_history
        WHERE session_id = ? AND is_deleted = 0
    """, (session_id,), fetchone=True)

    if not session:
        raise Exception("Session not found")

    if session["is_rewarded"] == 1:
        raise Exception("Already rewarded")

    # Award 1 point if award=True
    points_to_award = 1 if award else 0

    # update session
    execute("""
        UPDATE sessions_history
        SET points_awarded = ?, is_rewarded = 1
        WHERE session_id = ?
    """, (points_to_award, session_id), commit=True)

    # update student points (only if awarded)
    if award:
        execute("""
            UPDATE students
            SET points = points + 1
            WHERE id = ?
        """, (student_id,), commit=True)
    
    return {"success": True, "points_awarded": points_to_award}
    
def get_student_reward_score(student_id):
    # 1. Total Points
    student = execute("""
        SELECT points FROM students WHERE id = ?
    """, (student_id,), fetchone=True)

    points = student["points"] if student else 0

    # 🔥 Normalize points (IMPORTANT)
    MAX_POINTS = 100
    points_score = min((points / MAX_POINTS) * 100, 100)

    # 2. Tasks Completed
    tasks = execute("""
        SELECT 
            SUM(CASE WHEN status = 'Complete' THEN 1 ELSE 0 END) as complete,
            COUNT(*) as total
        FROM sessions_history
        WHERE student_id = ? AND is_rewarded = 1
    """, (student_id,), fetchone=True)

    complete = tasks["complete"] or 0
    total_tasks = tasks["total"] or 0

    task_score = (complete / total_tasks) * 100 if total_tasks > 0 else 0

    # 3. Hours (use stored value ✅)
    result = execute("""
        SELECT SUM(hours_rendered) as total_hours
        FROM sessions_history
        WHERE student_id = ? AND hours_rendered IS NOT NULL
    """, (student_id,), fetchone=True)

    total_hours = result["total_hours"] or 0

    # Normalize hours (50 hrs = 100%)
    hours_score = min((total_hours / 50) * 100, 100)

    # 4. Final Weighted Score (FIXED ✅)
    final_score = (
        (points_score * 0.6) +
        (task_score * 0.2) +
        (hours_score * 0.2)
    )

    # 5. Rank system (NEW 🔥)
    if final_score >= 80:
        rank = "Gold"
    elif final_score >= 60:
        rank = "Silver"
    else:
        rank = "Bronze"

    return {
        "points": points,
        "points_score": round(points_score, 2),  # 🔥 added
        "task_score": round(task_score, 2),
        "hours_score": round(hours_score, 2),
        "total_hours": round(total_hours, 2),
        "final_score": round(final_score, 2),
        "rank": rank  # 🔥 added
    }

# ---------------------------
# MARK TASK COMPLETION (Cannot mark if points already awarded)
# ---------------------------
def mark_task_completion(session_id, status):
    """
    Mark task as Complete or Incomplete
    Cannot mark if points were already awarded
    """
    # Check if session exists
    session = execute("""
        SELECT is_rewarded FROM sessions_history
        WHERE session_id = ? AND is_deleted = 0
    """, (session_id,), fetchone=True)

    if not session:
        raise Exception("Session not found")
    
    # Check if points were already awarded
    if session["is_rewarded"] == 1:
        raise Exception("Cannot mark task - Points already awarded for this session")

    # Update only task status (no points involved)
    execute("""
        UPDATE sessions_history
        SET status = ?
        WHERE session_id = ?
    """, (status, session_id), commit=True)
    
    return {"success": True, "message": f"Task marked as '{status}' for session {session_id}"}


# ---------------------------
# GET STUDENT STATS (Shows both systems separately)
# ---------------------------
def get_student_stats(student_id):
    # 1. POINT SYSTEM
    student = execute("""
        SELECT points FROM students WHERE id = ?
    """, (student_id,), fetchone=True)
    
    points = student["points"] if student else 0
    
    # Get total possible points
    total_sessions = execute("""
        SELECT COUNT(*) as total
        FROM sessions_history
        WHERE student_id = ? AND is_deleted = 0
    """, (student_id,), fetchone=True)
    
    total_possible_points = total_sessions["total"] or 0
    
    # 2. TASK COMPLETION SYSTEM
    tasks = execute("""
        SELECT 
            SUM(CASE WHEN status = 'Complete' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'Incomplete' THEN 1 ELSE 0 END) as incomplete,
            COUNT(*) as total
        FROM sessions_history
        WHERE student_id = ? AND is_deleted = 0 AND status IS NOT NULL
    """, (student_id,), fetchone=True)
    
    completed = tasks["completed"] or 0
    incomplete = tasks["incomplete"] or 0
    total_tasks = tasks["total"] or 0
    
    # 3. HOURS TRACKING
    result = execute("""
        SELECT SUM(hours_rendered) as total_hours
        FROM sessions_history
        WHERE student_id = ? AND is_deleted = 0 AND hours_rendered IS NOT NULL
    """, (student_id,), fetchone=True)
    
    total_hours = result["total_hours"] or 0
    
    return {
        "points_earned": points,
        "total_possible_points": total_possible_points,
        "points_rate": round((points / total_possible_points) * 100, 2) if total_possible_points > 0 else 0,
        "tasks_completed": completed,
        "tasks_incomplete": incomplete,
        "tasks_total": total_tasks,
        "completion_rate": round((completed / total_tasks) * 100, 2) if total_tasks > 0 else 0,
        "total_hours": round(total_hours, 2),
    }


# ---------------------------
# GET STUDENT RANK (based on points only)
# ---------------------------
def get_student_rank(student_id):
    stats = get_student_stats(student_id)
    points = stats["points_earned"]
    
    if points >= 80:
        rank = "Gold"
    elif points >= 60:
        rank = "Silver"
    elif points >= 40:
        rank = "Bronze"
    else:
        rank = "No Rank"
    
    return {
        "student_id": student_id,
        "points": points,
        "rank": rank
    }

# ---------------------------
# FEEDBACK SYSTEM
# ---------------------------
def add_feedback(student_id, session_id, message, rating):
    return execute("""
        INSERT INTO feedback (student_id, session_id, message, rating)
        VALUES (?, ?, ?, ?)
    """, (student_id, session_id, message, rating), commit=True)

def get_all_feedback():
    return execute("""
        SELECT message, rating, created_at
        FROM feedback
        ORDER BY created_at DESC
    """, fetchall=True)


def delete_feedback(feedback_id):
    return execute("""
        DELETE FROM feedback WHERE id = ?
    """, (feedback_id,), commit=True)



def get_leaderboard():
    return execute("""
        SELECT 
            s.id,
            s.first_name,
            s.last_name,
            s.points,

            COALESCE(SUM(sh.hours_rendered), 0) as total_hours,

            SUM(CASE WHEN sh.status = 'Complete' THEN 1 ELSE 0 END) as completed_tasks,
            COUNT(sh.session_id) as total_tasks

        FROM students s
        LEFT JOIN sessions_history sh ON s.id = sh.student_id
        GROUP BY s.id
    """, fetchall=True)


def get_top_hours():
    return execute("""
        SELECT s.first_name, s.last_name,
               SUM(sh.hours_rendered) as total_hours
        FROM sessions_history sh
        JOIN students s ON sh.student_id = s.id
        GROUP BY sh.student_id
        ORDER BY total_hours DESC
        LIMIT 10
    """, fetchall=True)

# ---------------------------
# FEEDBACK SYSTEM
# ---------------------------
def add_feedback(student_id, session_id, message, rating):
    return execute("""
        INSERT INTO feedback (student_id, session_id, message, rating)
        VALUES (?, ?, ?, ?)
    """, (student_id, session_id, message, rating), commit=True)

def get_all_feedback():
    return execute("""
        SELECT message, rating, created_at
        FROM feedback
        ORDER BY created_at DESC
    """, fetchall=True)


def delete_feedback(feedback_id):
    return execute("""
        DELETE FROM feedback WHERE id = ?
    """, (feedback_id,), commit=True)



def get_leaderboard():
    return execute("""
        SELECT 
            s.id,
            s.first_name,
            s.last_name,
            s.points,

            COALESCE(SUM(sh.hours_rendered), 0) as total_hours,

            SUM(CASE WHEN sh.status = 'Complete' THEN 1 ELSE 0 END) as completed_tasks,
            COUNT(sh.session_id) as total_tasks

        FROM students s
        LEFT JOIN sessions_history sh ON s.id = sh.student_id
        GROUP BY s.id
    """, fetchall=True)


def get_top_hours():
    return execute("""
        SELECT s.first_name, s.last_name,
               SUM(sh.hours_rendered) as total_hours
        FROM sessions_history sh
        JOIN students s ON sh.student_id = s.id
        GROUP BY sh.student_id
        ORDER BY total_hours DESC
        LIMIT 10
    """, fetchall=True)


# ---------------------------
# RESERVATION SYSTEM
# ---------------------------

def create_reservation(student_id, data):
    """Student creates a new reservation"""
    
    # Check if student already has a pending/approved reservation for same time slot
    existing = execute("""
        SELECT id FROM reservations
        WHERE student_id = ?
        AND reservation_date = ?
        AND time_slot = ?
        AND status IN ('Pending', 'Approved')
    """, (student_id, data['reservation_date'], data['time_slot']), fetchone=True)
    
    if existing:
        raise Exception("You already have a pending or approved reservation for this time slot")
    
    # Check if PC is available
    pc_taken = execute("""
        SELECT id FROM reservations
        WHERE pc_number = ?
        AND lab_room = ?
        AND reservation_date = ?
        AND time_slot = ?
        AND status IN ('Pending', 'Approved')
    """, (data['pc_number'], data['lab_room'], data['reservation_date'], data['time_slot']), fetchone=True)
    
    if pc_taken:
        raise Exception(f"PC {data['pc_number']} is already reserved for this time slot")
    
    # Check if PC is currently in use (active sit-in)
    pc_in_use = execute("""
        SELECT session_id FROM sessions_history
        WHERE pc_number = ?
        AND lab_room = ?
        AND session_date = ?
        AND logout_time IS NULL
    """, (data['pc_number'], data['lab_room'], data['reservation_date']), fetchone=True)
    
    if pc_in_use:
        raise Exception(f"PC {data['pc_number']} is currently in use")
    
    # Create reservation
    execute("""
        INSERT INTO reservations 
        (student_id, purpose, reservation_date, time_slot, lab_room, pc_number, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    """, (student_id, data['purpose'], data['reservation_date'], data['time_slot'], 
          data['lab_room'], data['pc_number']), commit=True)
    
    return {"success": True, "message": "Reservation submitted successfully"}


def get_available_pcs(lab_room, reservation_date, time_slot):
    """Get all available PCs for a specific time slot"""
    
    # Get all reserved PCs for this time slot
    reserved = execute("""
        SELECT pc_number FROM reservations
        WHERE lab_room = ?
        AND reservation_date = ?
        AND time_slot = ?
        AND status IN ('Pending', 'Approved')
    """, (lab_room, reservation_date, time_slot), fetchall=True)
    
    reserved_pcs = [r['pc_number'] for r in reserved]
    
    # Get PCs currently in use
    in_use = execute("""
        SELECT pc_number FROM sessions_history
        WHERE lab_room = ?
        AND session_date = ?
        AND logout_time IS NULL
    """, (lab_room, reservation_date), fetchall=True)
    
    in_use_pcs = [r['pc_number'] for r in in_use]
    
    # Generate list of all PCs (1-48 per lab)
    all_pcs = [f"PC{i}" for i in range(1, 49)]
    
    available = []
    for pc in all_pcs:
        if pc not in reserved_pcs and pc not in in_use_pcs:
            available.append(pc)
    
    return {
        "available": available,
        "reserved": reserved_pcs,
        "in_use": in_use_pcs
    }


def get_student_reservations(student_id):
    """Get all reservations for a student"""
    return execute("""
        SELECT r.*, 
               CASE 
                   WHEN r.status = 'Pending' THEN 'pending'
                   WHEN r.status = 'Approved' THEN 'approved'
                   WHEN r.status = 'Rejected' THEN 'rejected'
                   WHEN r.status = 'Cancelled' THEN 'cancelled'
                   WHEN r.status = 'Completed' THEN 'completed'
               END as status_class
        FROM reservations r
        WHERE r.student_id = ?
        ORDER BY 
            CASE r.status
                WHEN 'Pending' THEN 1
                WHEN 'Approved' THEN 2
                ELSE 3
            END,
            r.reservation_date ASC
    """, (student_id,), fetchall=True)


def cancel_reservation(reservation_id, student_id, cancelled_by='student'):
    """Cancel a reservation (student or admin)"""
    
    reservation = execute("""
        SELECT id, status FROM reservations
        WHERE id = ? AND student_id = ?
    """, (reservation_id, student_id), fetchone=True)
    
    if not reservation:
        raise Exception("Reservation not found")
    
    if reservation['status'] not in ['Pending', 'Approved']:
        raise Exception(f"Cannot cancel reservation with status: {reservation['status']}")
    
    execute("""
        UPDATE reservations
        SET status = 'Cancelled',
            cancelled_by = ?,
            cancelled_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (cancelled_by, reservation_id), commit=True)
    
    return {"success": True, "message": "Reservation cancelled successfully"}


def get_all_reservations(filters=None):
    """Get all reservations for admin panel"""
    
    query = """
        SELECT r.*, 
               s.id_number, 
               s.first_name, 
               s.last_name,
               s.email,
               a.id_number as admin_id_number
        FROM reservations r
        JOIN students s ON r.student_id = s.id
        LEFT JOIN admins a ON r.approved_by = a.id
        WHERE 1=1
    """
    params = []
    
    if filters:
        if filters.get('status'):
            query += " AND r.status = ?"
            params.append(filters['status'])
        
        if filters.get('date'):
            query += " AND r.reservation_date = ?"
            params.append(filters['date'])
        
        if filters.get('search'):
            query += " AND (s.id_number LIKE ? OR s.first_name LIKE ? OR s.last_name LIKE ?)"
            search = f"%{filters['search']}%"
            params.extend([search, search, search])
    
    query += " ORDER BY r.created_at DESC"
    
    return execute(query, params, fetchall=True)


def approve_reservation(reservation_id, admin_id, remarks=None):
    """Admin approves a reservation"""
    
    reservation = execute("""
        SELECT id, status FROM reservations
        WHERE id = ?
    """, (reservation_id,), fetchone=True)
    
    if not reservation:
        raise Exception("Reservation not found")
    
    if reservation['status'] != 'Pending':
        raise Exception(f"Cannot approve reservation with status: {reservation['status']}")
    
    execute("""
        UPDATE reservations
        SET status = 'Approved',
            approved_by = ?,
            approved_at = CURRENT_TIMESTAMP,
            admin_remarks = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (admin_id, remarks, reservation_id), commit=True)
    
    return {"success": True, "message": "Reservation approved successfully"}


def reject_reservation(reservation_id, admin_id, remarks=None):
    """Admin rejects a reservation"""
    
    reservation = execute("""
        SELECT id, status FROM reservations
        WHERE id = ?
    """, (reservation_id,), fetchone=True)
    
    if not reservation:
        raise Exception("Reservation not found")
    
    if reservation['status'] != 'Pending':
        raise Exception(f"Cannot reject reservation with status: {reservation['status']}")
    
    execute("""
        UPDATE reservations
        SET status = 'Rejected',
            approved_by = ?,
            approved_at = CURRENT_TIMESTAMP,
            admin_remarks = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (admin_id, remarks, reservation_id), commit=True)
    
    return {"success": True, "message": "Reservation rejected"}


def start_session_from_reservation(reservation_id, student_id):
    """Start a sit-in session from an approved reservation"""
    
    reservation = execute("""
        SELECT r.*, s.sessions_remaining 
        FROM reservations r
        JOIN students s ON r.student_id = s.id
        WHERE r.id = ? AND r.student_id = ?
    """, (reservation_id, student_id), fetchone=True)
    
    if not reservation:
        raise Exception("Reservation not found")
    
    if reservation['status'] != 'Approved':
        raise Exception(f"Cannot start session. Reservation status: {reservation['status']}")
    
    if reservation['reservation_date'] != datetime.now().strftime("%Y-%m-%d"):
        raise Exception("This reservation is for a different date")
    
    if reservation['sessions_remaining'] <= 0:
        raise Exception("No sessions remaining")
    
    # Check if already have an active session
    active = execute("""
        SELECT session_id FROM sessions_history
        WHERE student_id = ? AND logout_time IS NULL
    """, (student_id,), fetchone=True)
    
    if active:
        raise Exception("You already have an active session")
    
    now = datetime.now()
    
    # Create sit-in session
    session_id = execute("""
        INSERT INTO sessions_history 
        (student_id, reservation_id, login_time, session_date, purpose, pc_number, lab_room, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (student_id, reservation_id, now.strftime("%H:%M:%S"), 
          reservation['reservation_date'], reservation['purpose'], 
          reservation['pc_number'], reservation['lab_room'], None), commit=True)
    
    # Update student sessions
    execute("""
        UPDATE students
        SET sessions_remaining = sessions_remaining - 1,
            total_session_used = total_session_used + 1
        WHERE id = ?
    """, (student_id,), commit=True)
    
    # Update reservation
    execute("""
        UPDATE reservations
        SET status = 'Completed',
            session_id = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (session_id, reservation_id), commit=True)
    
    return {"success": True, "message": "Session started successfully", "session_id": session_id}


def get_today_reservations():
    """Get today's approved reservations for admin dashboard"""
    today = datetime.now().strftime("%Y-%m-%d")
    return execute("""
        SELECT r.*, s.first_name, s.last_name, s.id_number
        FROM reservations r
        JOIN students s ON r.student_id = s.id
        WHERE r.reservation_date = ? AND r.status = 'Approved'
        ORDER BY r.time_slot ASC
    """, (today,), fetchall=True)