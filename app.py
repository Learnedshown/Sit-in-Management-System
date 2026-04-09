import os
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from flask import Flask, request, jsonify, url_for, render_template, redirect, session, flash, json
from models.student_models import register_students, view_students, student_session, update_student, view_all_students, student_verify_password, change_student_password, delete_students
from database import setup_database, close_db
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
    admin_update_student
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




@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/")
def root():
    return redirect(url_for("login"))




"""

#FOR ADMIN- EDIT PROFILE FOR STUDENT

@app.route("/admin/students/<id_number>/edit", methods=["POST"])
def admin_edit_student(id_number):
    if "user" not in session or session.get("role") != "admin":
        flash("Please log in as admin!", "warning")
        return redirect(url_for("login"))

    student = view_students(id_number)
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for("admin_students"))

    if request.method == "POST":
        # Gather form data
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
            update_student(data)
            flash("Student updated successfully!", "success")
        except Exception as e:
            flash(f"Update failed: {str(e)}", "danger")
            return redirect(url_for("admin_edit_student", id_number=id_number))

        return redirect(url_for("admin_students"))

    return render_template("admin/admin_students.html", student=student)



# ---------------------------
# SEARCH STUDENT PAGE (GET) & SEARCH (POST)
# ---------------------------
@app.route("/admin/search", methods=["GET", "POST"])
def admin_search_student():
    if request.method == "POST":
        keyword = request.form.get("keyword", "")
        try:
            students = search_student(keyword)
            return render_template("admin_search.html", students=students, keyword=keyword)
        except Exception as e:
            return f"Error: {e}", 400
    
    return render_template("admin_search.html")


# ---------------------------
# VIEW STUDENTS PAGE
# ---------------------------
@app.route("/admin/students")
def admin_students():
    try:
        students = view_all_students()
        return render_template("admin_students.html", students=students)
    except Exception as e:
        return f"Error: {e}", 400

# JSONIFY
@app.route("/view_student/<id_number>", methods=["GET"])
def view_student_route(id_number):
    try:
        student = view_students(id_number)
        return jsonify(student)  # Return student data as JSON
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route("/student_session", methods=["POST"])
def student_session_route():
    data = request.get_json()
    if "id_number" not in data:
        return jsonify({"error": "id_number is required"}), 400

    try:
        # Before & after printing is already inside student_session()
        student_session(data)

        # Return the updated student info
        updated_student = view_students(data["id_number"])
        return jsonify({
            "message": "Session deducted successfully!",
            "student": updated_student
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)