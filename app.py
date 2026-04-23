import os
from werkzeug.utils import secure_filename
from datetime import datetime
from werkzeug.security import check_password_hash
from flask import Flask, request, jsonify, url_for, render_template, redirect, session, flash, json
from database import setup_database, close_db
from db_helper import execute
from models.student_models import (
    register_students,view_students,
    student_session, 
    get_student_history_with_feedback 
    ,update_student, view_all_students, 
    student_verify_password, 
    change_student_password, 
    delete_students)

from models.admin_models import (
    search_student,
    start_sitin,
    end_sitin,
    view_current_sitin,
    view_sitin_records,
    admin_verify_password,
    add_announcement,
    get_announcement,
    view_all_sitin_purposes,
    is_already_sitin,
    reset_all_sessions,
    admin_update_student,
    add_feedback,
    get_all_feedback,
    add_points,
    deduct_points,
    award_points,
    get_reward_sessions,
    get_leaderboard,
    get_student_reward_score,
    mark_task_completion,
    get_student_stats,
    get_student_rank,
    create_reservation,
    get_available_pcs,
    get_student_reservations,
    cancel_reservation,
    get_all_reservations,
    approve_reservation,
    reject_reservation,
    start_session_from_reservation,
    get_today_reservations
)



app = Flask(__name__)
app.secret_key = "secret123"
setup_database(app)
app.teardown_appcontext(close_db)

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route("/register", methods=["GET", "POST"])
def register_student_route():
    if request.method == "POST":
        id_number = request.form.get("id_number")
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        middle_name = request.form.get("middle_name", "").strip()
        course_level = request.form.get("course_level")
        password_input = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        email = request.form.get("email")
        course = request.form.get("course")
        address = request.form.get("address")

     
        form_data = dict(
            id_number=id_number,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            course_level=course_level,
            email=email,
            course=course,
            address=address
        )

        if not all([id_number, first_name, last_name, course_level, email, course, address, password_input]):
            flash("All fields must be filled!", "danger")
            return render_template("student/register.html", **form_data)

        if password_input != confirm_password:
            flash("Passwords do not match", "warning")
            return render_template("student/register.html", **form_data)

        if len(password_input) < 8:
            flash("Password must be at least 8 characters long", "danger")
            return render_template("student/register.html", **form_data)

        if len(first_name) > 30 or len(last_name) > 30 or (middle_name and len(middle_name) > 30):
            flash("Names cannot exceed 30 characters", "danger")
            return render_template("student/register.html", **form_data)

        if len(id_number) != 8:
            flash("ID number must be 8 digits!", "danger")
            return render_template("student/register.html", **form_data)

        try:
            register_students({
                "id_number": id_number,
                "first_name": first_name,
                "last_name": last_name,
                "middle_name": middle_name,
                "course_level": course_level,
                "password": password_input,
                "email": email,
                "course": course,
                "address": address
            })
        except Exception:
            flash("ID already exists!", "danger")
            return render_template("student/register.html", **form_data)

        return jsonify({"success": True})

    return render_template("student/register.html")

@app.route("/student/add", methods= ["GET", "POST"])
def add_student():

    if request.method == "POST":
        id_number = request.form.get("id_number")
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        middle_name = request.form.get("middle_name", "").strip()
        course_level = request.form.get("course_level")
        password_input = request.form.get("password")
        email = request.form.get("email")
        course = request.form.get("course")
        address = request.form.get("address")

        form_data = dict(
            id_number = id_number,
            first_name = first_name,
            last_name = last_name,
            middle_name = middle_name,
            course_level = course_level,
            password_input = password_input,
            email = email,
            course = course,
            address = address
        )

        if not all([id_number, first_name, last_name, course_level, email, course, address, password_input]):
            flash("All fields must be filled!", "danger")
            return render_template("admin/admin_students.html", **form_data)
        
        if len(password_input) < 8:
            flash("Password must be 8 Characters Long!")
            return render_template("admin/admin_students.html", **form_data)
        
        if len(first_name) > 30 or len(last_name) > 30 or (middle_name and len(middle_name) > 30):
            flash("Names cannot exceed 30 characters", "danger")
            return render_template("admin/admin_students.html", **form_data)

        if len(id_number) != 8:
            flash("ID number must be 8 digits!", "danger")
            return render_template("admin/admin_students.html", **form_data)
        
        try:
            register_students({
                "id_number": id_number,
                "first_name": first_name,
                "last_name": last_name,
                "middle_name": middle_name,
                "course_level": course_level,
                "password": password_input,
                "email": email,
                "course": course,
                "address": address
            })
        except Exception:
            flash("ID already exists!", "danger")
            return render_template("admin/admin_students.html", **form_data)

        return redirect (url_for("add_student"))

    return render_template("admin/admin_students.html")

@app.route("/admin/students/<id_number>/delete", methods=["POST"])
def delete_student_route(id_number):
    delete_students(id_number)
    flash("Student deleted successfully!", "success")
    return redirect(url_for("add_student"))

 
@app.route("/reset-session", methods=["POST"])
def reset_sessions():

    if "user" not in session or session.get("role") != "admin":
        flash("Please log in first", "warning")
        return redirect(url_for("login"))
    
    reset_all_sessions()

    flash("All student sessions have been reset for the new semester.", "success")
    return render_template("admin/admin_students.html")
        


@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        id_number = request.form.get("id_number")
        password = request.form.get("password")
        
        if not id_number or not password:
            return render_template("auth/login.html", error="ID and password is required")
                
        if admin_verify_password(id_number, password):
            session["user"] = id_number
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))

        if student_verify_password(id_number, password):
            session["user"] = id_number
            session["role"] = "student"
            return redirect(url_for("dashboard"))
        
        return render_template("auth/login.html", error="Invalid Credentials")
        
    return render_template("auth/login.html")



@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    student = view_students(session["user"])
    full_name = f"{student['first_name']} {student['last_name']}"
    profile_photo = student.get("profile_photo") or "default.png"
    course = student['course']
    course_level = student['course_level']
    email = student['email']
    address = student['address']
    sessions_remaining = student['sessions_remaining']
    
    announcements = get_announcement()
    
    return render_template("student/dashboard.html", 
    name=full_name,
    course=course,
    year=course_level,
    email = email,
    address=address,
    sessions_remaining = sessions_remaining,
    profile_photo=profile_photo,
    announcements = announcements
    )
# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "user" not in session or session.get("role") != "admin":
        flash("Please log in first", "warning")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            add_announcement({"content": content})
            flash("Announcement posted!", "success")
        return redirect(url_for("admin_dashboard"))

    # Get all students
    students = view_all_students()
    total_students = len(students)

    current_sitin = view_current_sitin()
    current_count = len(current_sitin)

    total_sitin = sum(s.get("total_session_used", 0) for s in students)

    # Count sit-ins per purpose
    # Assuming you have a function view_all_sitin() returning sit-in records with "purpose" keys
    sitins = view_all_sitin_purposes()  # You need to implement this or get sit-ins data

    # List all purposes shown on chart
    purposes = ['C#', 'C', 'Java', 'Python', 'PHP']

    purpose_counts = {p: 0 for p in purposes}

    for sitin in sitins:
        purpose = sitin.get("purpose")
        if purpose in purpose_counts:
            purpose_counts[purpose] += 1
        else:
            # Optionally count unknown/other purposes or ignore
            pass

    chart_labels = list(purpose_counts.keys())
    chart_values = list(purpose_counts.values())

    announcements = get_announcement()

    return render_template(
        "admin/admin_dashboard.html",
        total_students=total_students,
        current_count=current_count,
        total_sitin=total_sitin,
        chart_labels=json.dumps(chart_labels),
        chart_values=json.dumps(chart_values),
        announcements=announcements
    )


#------------------------------------
#EDIT STUDENT PROFILE (ADMIN)       |
#------------------------------------
@app.route("/admin/students/<id_number>/edit", methods=["POST"])
def admin_edit_student(id_number):
   
    if "user" not in session or session.get("role") != "admin":
        flash("Please log in as admin!", "warning")
        return redirect(url_for("login"))

    # ✅ Check if student exists
    student = view_students(id_number)
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for("admin_students"))

    # ✅ Gather form data
    data = {
        "id_number": id_number,
        "first_name": request.form.get("first_name", "").strip(),
        "middle_name": request.form.get("middle_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "course_level": int(request.form.get("course_level", student["course_level"])),
        "course": request.form.get("course", student["course"]),
        "email": request.form.get("email", student["email"]),
        "address": request.form.get("address", student["address"]),
        "sessions_remaining": min(
            max(int(request.form.get("sessions_remaining", student["sessions_remaining"])), 0), 30
        ),
    }

    
    try:
        admin_update_student(data)
        flash("Student updated successfully!", "success")
    except Exception as e:
        flash(f"Update failed: {str(e)}", "danger")
        return redirect(url_for("admin_edit_student", id_number=id_number))

    return redirect(url_for("admin_students"))

#------------------------------------
#EDIT PROFILE (STUDENT)             |
#------------------------------------
@app.route("/editprofile", methods=["GET", "POST"])
def edit_profile():
    if "user" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))

    student = view_students(session["user"])  # Fetch current student info

    if request.method == "POST":
        # --- Form fields ---
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        middle_name = request.form.get("middle_name", "").strip()
        course_level = request.form.get("course_level")
        email = request.form.get("email")
        course = request.form.get("course")
        address = request.form.get("address")
        current_password = request.form.get("current_password")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # --- Validation ---
        if not first_name or not last_name or not email:
            flash("First name, last name, and email are required!", "danger")
            return redirect(url_for("edit_profile"))

        if len(first_name) > 30 or len(last_name) > 30 or (middle_name and len(middle_name) > 30):
            flash("Names cannot exceed 30 characters", "danger")
            return redirect(url_for("edit_profile"))
        
        if password:
            if len(password) < 8:
                flash("Password must be 8 characters long", "warning")
                return redirect(url_for("edit_profile"))
            
            if not current_password:
                flash("Please enter your current password", "danger")
                return redirect(url_for("edit_profile"))
            
            if not check_password_hash(student["password"], current_password):
                flash("Current password is incorrect", "danger")
                return redirect(url_for("edit_profile"))

            if password != confirm_password:
                flash("Password do not Match!", "danger")
                return redirect(url_for("edit_profile"))
            
            
            change_student_password({
                "id_number": session["user"],
                "password": password
            })

        # --- Profile photo upload ---
        file = request.files.get("profile_photo")
        profile_filename = student.get("profile_photo") or "default.png"  # fallback to default if null

        if file and allowed_file(file.filename):
            filename = secure_filename(f"{session['user']}_{file.filename}")
            upload_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            file.save(upload_path)
            profile_filename = filename  # update to new filename

        # --- Update student record ---
        try:
            update_student({
                "id_number": session["user"],
                "first_name": first_name,
                "last_name": last_name,
                "middle_name": middle_name,
                "course_level": int(course_level) if course_level else None,
                "email": email,
                "course": course,
                "address": address,
                "profile_photo": profile_filename
            })
            flash("Profile updated successfully!", "success")
        except Exception as e:
            flash(f"Update failed: {str(e)}", "danger")
            return redirect(url_for("edit_profile"))

        return redirect(url_for("edit_profile"))

    # GET request → render form with current data
    return render_template(
        "student/editprofile.html",
        first_name=student.get("first_name", ""),
        last_name=student.get("last_name", ""),
        middle_name=student.get("middle_name", ""),
        course_level=student.get("course_level"),
        email=student.get("email", ""),
        course=student.get("course"),
        address=student.get("address", ""),
        profile_photo=student.get("profile_photo") or "default.png"  # ensures template always has a photo
    )


#VIEW STUDENT PAGE
@app.route("/admin/students")
def admin_students():
    try:
        students = view_all_students()
        return render_template("admin/admin_students.html")
    except Exception as e:
        return f"Error: {e}", 400
    
@app.route("/admin/students_data")
def admin_students_data():
    try:
        students = view_all_students()  # fetch all students from DB
        return {"students": students}   # return JSON
    except Exception as e:
        return {"error": str(e)}, 400


@app.route("/view_student/<id_number>", methods=["GET"])
def view_student_route(id_number):
    try:
        student = view_students(id_number)
        return jsonify(student)  # Return student data as JSON
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/admin/current_sitin")
def admin_current_sitin():
    if "user" not in session or session.get("role") != "admin":
        flash("Please log in first!", "warning")
        return redirect(url_for("login"))

    try:
        current = view_current_sitin()  # Fetch all active sit-ins
        return render_template(
            "admin/admin_current_sitin.html",
            current=current
        )
    except Exception as e:
        flash(f"Error fetching current sit-ins: {str(e)}", "danger")
        return render_template("admin/admin_current_sitin.html", current=[])


# ---------------------------
# START SIT-IN (POST) & VIEW SIT-IN PAGE (GET)
# ---------------------------
@app.route("/admin/sitin", methods=["POST"])
def admin_sitin_page():
    try:
        start_sitin(request.form)
        return jsonify({"success": True, "message": "Sit-in started successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
  


# ---------------------------
# END SIT-IN (POST)
# ---------------------------
@app.route("/admin/sitin/end/<int:session_id>", methods=["POST"])
def admin_end_sitin(session_id):
    try:
        end_sitin(session_id)
        flash("Sit-in ended successfully", "success")
        return redirect(url_for("admin_current_sitin"))
    except Exception as e:
        return f"Error: {e}", 400


# ---------------------------
# VIEW ALL SIT-IN RECORDS PAGE
# ---------------------------
@app.route("/admin/sitin/records")
def admin_sitin_records():
    try:
        records = view_sitin_records()
        return render_template("admin/admin_sitin_records.html", records=records)
    except Exception as e:
        return f"Error: {e}", 400



@app.route("/student/history")
def student_history():
    if "user" not in session:
        return redirect(url_for("login"))

    student = view_students(session["user"])
    history = get_student_history_with_feedback(student["id"])

    return render_template("student/history.html", history=history)

@app.route("/student/submit_feedback/<int:session_id>", methods=["POST"])
def submit_feedback_session(session_id):
    if "user" not in session:
        return redirect(url_for("login"))

    student = view_students(session["user"])

    message = request.form.get("message")
    rating = request.form.get("rating")

    if not message or not rating:
        flash("All fields required!", "danger")
        return redirect(url_for("student_history"))

    add_feedback(
        student["id"],     # ✅ FIXED (NOT id_number)
        session_id,
        message,
        int(rating)
    )

    flash("Feedback submitted!", "success")
    return redirect(url_for("student_history"))

@app.route("/admin/feedback")
def admin_feedback():
    if "user" not in session or session.get("role") != "admin":
        flash("Please log in as admin!", "warning")
        return redirect(url_for("login"))

    feedback = get_all_feedback()

    return render_template("admin/admin_feedback.html", feedback=feedback)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

"""@app.route("/student/rewards")
def student_rewards():
    if "user" not in session:
        return redirect(url_for("login"))

    student = view_students(session["user"])
    points = student["points"]

    return render_template("student/rewards.html", points=points)"""


# ---------------------------
# REWARDS PAGE (VIEW)
# ---------------------------
@app.route("/admin/rewards")
def admin_rewards():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    # Get all sessions that haven't been rewarded yet
    records = execute("""
        SELECT 
            s.session_id,
            s.student_id,
            s.purpose,
            s.session_date,
            s.status,
            s.points_awarded,
            s.is_rewarded,
            st.id_number,
            st.first_name,
            st.last_name
        FROM sessions_history s
        JOIN students st ON s.student_id = st.id
        WHERE s.is_deleted = 0
        ORDER BY s.session_date DESC
    """, fetchall=True)
    
    return render_template("admin/admin_rewards.html", records=records)


# ---------------------------
# AWARD POINT ACTION (1 point only)
# ---------------------------
@app.route("/admin/reward_session/<int:session_id>", methods=["POST"])
def reward_session(session_id):
    """Award 1 point to student for this session"""
    
    # Get session details
    session_data = execute("""
        SELECT student_id FROM sessions_history
        WHERE session_id = ? AND is_deleted = 0
    """, (session_id,), fetchone=True)
    
    if not session_data:
        flash("Session not found", "error")
        return redirect(url_for("admin_rewards"))
    
    # Award 1 point (status is not used for points anymore)
    result = award_points(session_id, session_data["student_id"], award=True)
    
    if result["success"]:
        flash(f"Successfully awarded 1 point", "success")
    else:
        flash(result["message"], "error")
    
    return redirect(url_for("admin_rewards"))


# ---------------------------
# MARK TASK COMPLETION (Separate from points)
# ---------------------------
@app.route("/admin/mark_task/<int:session_id>", methods=["POST"])
def mark_task(session_id):
    """Mark task as Complete or Incomplete (doesn't affect points)"""
    
    status = request.form.get("status")  # 'Complete' or 'Incomplete'
    
    if status not in ['Complete', 'Incomplete']:
        flash("Invalid status", "error")
        return redirect(url_for("admin_rewards"))
    
    result = mark_task_completion(session_id, status)
    
    if result["success"]:
        flash(f"Task marked as {status}", "success")
    else:
        flash(result["message"], "error")
    
    return redirect(url_for("admin_rewards"))


# ---------------------------
# LEADERBOARD (Based on points only, tasks separate)
# ---------------------------
@app.route("/leaderboard")
def leaderboard():
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Get all students with their stats
    students = execute("""
        SELECT 
            st.id,
            st.id_number,
            st.first_name,
            st.last_name,
            st.points,
            COUNT(s.session_id) as total_sessions,
            SUM(CASE WHEN s.status = 'Complete' THEN 1 ELSE 0 END) as completed_tasks,
            SUM(CASE WHEN s.status = 'Incomplete' THEN 1 ELSE 0 END) as incomplete_tasks,
            SUM(s.hours_rendered) as total_hours
        FROM students st
        LEFT JOIN sessions_history s ON st.id = s.student_id AND s.is_deleted = 0
        GROUP BY st.id
        ORDER BY st.points DESC
    """, fetchall=True)
    
    # Calculate scores
    for student in students:
        # Points score (max 100 points = 100%)
        points_score = min((student["points"] / 100) * 100, 100)
        
        # Task score (separate from points)
        total_tasks = student["total_sessions"] or 0
        completed = student["completed_tasks"] or 0
        task_score = (completed / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Hours score
        hours_score = min((student["total_hours"] or 0) / 50 * 100, 100)
        
        # Final combined score (60% points, 20% tasks, 20% hours)
        student["final_score"] = (
            (points_score * 0.6) +
            (task_score * 0.2) +
            (hours_score * 0.2)
        )
        student["points_score"] = round(points_score, 2)
        student["task_score"] = round(task_score, 2)
        student["hours_score"] = round(hours_score, 2)
        student["total_hours"] = round(student["total_hours"] or 0, 2)
    
    # Sort by final score
    students = sorted(students, key=lambda x: x["final_score"], reverse=True)
    
    # Add rank
    for i, student in enumerate(students, start=1):
        student["rank"] = i
    
    return render_template("admin/admin_leaderboard.html", data=students)


# ---------------------------
# STUDENT REWARDS PAGE
# ---------------------------
@app.route("/student/rewards")
def student_rewards():
    if "user" not in session:
        return redirect(url_for("login"))
    
    # Get student info
    student = execute("""
        SELECT id, id_number, first_name, last_name, points
        FROM students
        WHERE id_number = ?
    """, (session["user"],), fetchone=True)
    
    if not student:
        return redirect(url_for("logout"))
    
    # Get student stats (separate systems)
    stats = get_student_stats(student["id"])
    
    # Get rank based on points only
    rank_data = get_student_rank(student["id"])
    
    return render_template(
        "student/rewards.html",
        student=student,
        points=stats["points_earned"],
        total_possible_points=stats["total_possible_points"],
        points_rate=stats["points_rate"],
        tasks_completed=stats["tasks_completed"],
        tasks_incomplete=stats["tasks_incomplete"],
        completion_rate=stats["completion_rate"],
        total_hours=stats["total_hours"],
        rank=rank_data["rank"]
    )

# ---------------------------
# STUDENT RESERVATION ROUTES
# ---------------------------

@app.route("/student/reservation/make", methods=["GET", "POST"])
def student_make_reservation():
    if "user" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
    
    student = execute("SELECT id FROM students WHERE id_number = ?", (session["user"],), fetchone=True)
    
    if request.method == "POST":
        try:
            data = {
                "purpose": request.form.get("purpose"),
                "reservation_date": request.form.get("reservation_date"),
                "time_slot": request.form.get("time_slot"),
                "lab_room": request.form.get("lab_room"),
                "pc_number": request.form.get("pc_number")
            }
            
            result = create_reservation(student["id"], data)
            flash(result["message"], "success")
            return redirect(url_for("student_my_reservations"))
        except Exception as e:
            flash(str(e), "error")
    
    # Get available time slots
    time_slots = ["8:00 AM - 10:00 AM", "10:00 AM - 12:00 PM", "1:00 PM - 3:00 PM", "3:00 PM - 5:00 PM"]
    lab_rooms = ["530", "544", "524", "526"]
    purposes = [
    {"purpose": "Programming (C#)"},
    {"purpose": "Programming (Java)"},
    {"purpose": "Programming (Python)"},
    {"purpose": "Programming (PHP)"},
    {"purpose": "Programming (C)"},
    {"purpose": "Programming (Other)"},   
]   
    
    return render_template("student/make_reservation.html", 
                         time_slots=time_slots, 
                         lab_rooms=lab_rooms,
                         purposes=purposes)


@app.route("/student/reservations")
def student_my_reservations():
    if "user" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
    
    student = execute("SELECT id FROM students WHERE id_number = ?", (session["user"],), fetchone=True)
    reservations = get_student_reservations(student["id"])
    
    return render_template("student/my_reservations.html", reservations=reservations)


@app.route("/student/reservation/cancel/<int:reservation_id>", methods=["POST"])
def student_cancel_reservation(reservation_id):
    if "user" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
    
    student = execute("SELECT id FROM students WHERE id_number = ?", (session["user"],), fetchone=True)
    
    try:
        result = cancel_reservation(reservation_id, student["id"], "student")
        flash(result["message"], "success")
    except Exception as e:
        flash(str(e), "error")
    
    return redirect(url_for("student_my_reservations"))


@app.route("/student/start_reserved_session/<int:reservation_id>", methods=["POST"])
def start_reserved_session(reservation_id):
    if "user" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
    
    student = execute("SELECT id FROM students WHERE id_number = ?", (session["user"],), fetchone=True)
    
    try:
        result = start_session_from_reservation(reservation_id, student["id"])
        flash(result["message"], "success")
        return redirect(url_for("student_my_reservations"))
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("student_my_reservations"))


@app.route("/student/get_available_pcs")
def get_available_pcs_route():
    """AJAX endpoint to get available PCs for selected time slot"""
    lab_room = request.args.get("lab_room")
    reservation_date = request.args.get("reservation_date")
    time_slot = request.args.get("time_slot")
    
    if not all([lab_room, reservation_date, time_slot]):
        return jsonify({"error": "Missing parameters"}), 400
    
    result = get_available_pcs(lab_room, reservation_date, time_slot)
    return jsonify(result)


# ---------------------------
# ADMIN RESERVATION ROUTES
# ---------------------------

@app.route("/admin/reservations")
def admin_reservations():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    status_filter = request.args.get("status", "all")
    date_filter = request.args.get("date", "")
    search = request.args.get("search", "")
    
    filters = {}
    if status_filter != "all":
        filters["status"] = status_filter
    if date_filter:
        filters["date"] = date_filter
    if search:
        filters["search"] = search
    
    reservations = get_all_reservations(filters if filters else None)
    
    return render_template("admin/admin_reservations.html", 
                         reservations=reservations,
                         current_status=status_filter,
                         current_date=date_filter,
                         current_search=search)


@app.route("/admin/reservation/<int:reservation_id>/approve", methods=["POST"])
def admin_approve_reservation(reservation_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    admin = execute("SELECT id FROM admins WHERE id_number = ?", (session["user"],), fetchone=True)
    remarks = request.form.get("remarks", "")
    
    try:
        result = approve_reservation(reservation_id, admin["id"], remarks)
        flash(result["message"], "success")
    except Exception as e:
        flash(str(e), "error")
    
    return redirect(url_for("admin_reservations"))


@app.route("/admin/reservation/<int:reservation_id>/reject", methods=["POST"])
def admin_reject_reservation(reservation_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    admin = execute("SELECT id FROM admins WHERE id_number = ?", (session["user"],), fetchone=True)
    remarks = request.form.get("remarks", "")
    
    try:
        result = reject_reservation(reservation_id, admin["id"], remarks)
        flash(result["message"], "success")
    except Exception as e:
        flash(str(e), "error")
    
    return redirect(url_for("admin_reservations"))


@app.route("/admin/reservation/<int:reservation_id>/cancel", methods=["POST"])
def admin_cancel_reservation(reservation_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    student = execute("SELECT student_id FROM reservations WHERE id = ?", (reservation_id,), fetchone=True)
    
    try:
        result = cancel_reservation(reservation_id, student["student_id"], "admin")
        flash(result["message"], "success")
    except Exception as e:
        flash(str(e), "error")
    
    return redirect(url_for("admin_reservations"))


@app.route("/admin/mark_and_reward/<int:session_id>", methods=["POST"])
def mark_and_reward(session_id):
    """Mark task and optionally award points"""
    
    status = request.form.get("status")
    award_point = request.form.get("award_point")
    
    if status not in ['Complete', 'Incomplete']:
        flash("Invalid status", "error")
        return redirect(url_for("admin_rewards"))
    
    # Get session details
    session_data = execute("""
        SELECT student_id, is_rewarded FROM sessions_history
        WHERE session_id = ? AND is_deleted = 0
    """, (session_id,), fetchone=True)
    
    if not session_data:
        flash("Session not found", "error")
        return redirect(url_for("admin_rewards"))
    
    if session_data["is_rewarded"] == 1:
        flash("Points already awarded for this session", "error")
        return redirect(url_for("admin_rewards"))
    
    # Mark the task
    execute("""
        UPDATE sessions_history
        SET status = ?
        WHERE session_id = ?
    """, (status, session_id), commit=True)
    
    # Award point if requested AND task is Complete
    if award_point == "yes" and status == "Complete":
        result = award_points(session_id, session_data["student_id"], award=True)
        if result["success"]:
            flash(f"✅ Task marked as {status} and 1 point awarded!", "success")
        else:
            flash(f"⚠️ Task marked as {status} but point award failed", "warning")
    elif status == "Complete" and award_point == "no":
        flash(f"📋 Task marked as {status} (no points awarded)", "info")
    elif status == "Incomplete":
        flash(f"📋 Task marked as {status} (points cannot be awarded)", "info")
    
    return redirect(url_for("admin_rewards"))


@app.route("/")
def root():
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)