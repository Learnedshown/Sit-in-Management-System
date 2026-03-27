import os
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, url_for, render_template, redirect, session, flash, json
from models.student_models import register_students, view_students, student_session, update_student, view_all_students, student_verify_password
from database import setup_database, close_db
from models.admin_models import (
    search_student,
    start_sitin,
    end_sitin,
    view_current_sitin,
    view_sitin_records,
    admin_verify_password
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

        return redirect(url_for("login"))

    return render_template("student/register.html")



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
   
    
    return render_template("student/dashboard.html", 
    name=full_name,
    course=course,
    year=course_level,
    email = email,
    address=address,
    sessions_remaining = sessions_remaining,
    profile_photo=profile_photo
    )

# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user" not in session or session.get("role") != "admin":
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    # Get all students
    students = view_all_students()
    total_students = len(students)

    
    current_sitin = view_current_sitin()
    current_count = len(current_sitin)

    
    total_sitin = sum(s.get("total_session_used", 0) for s in students)

  
    course_counts = {}
    for s in students:
        course = s.get("course", "Unknown")
        course_counts[course] = course_counts.get(course, 0) + 1

    
    chart_labels = list(course_counts.keys())
    chart_values = list(course_counts.values())

    return render_template(
        "admin/admin_dashboard.html",
        total_students=total_students,
        current_count=current_count,
        total_sitin=total_sitin,
        chart_labels=json.dumps(chart_labels),
        chart_values=json.dumps(chart_values)
    )

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

        # --- Validation ---
        if not first_name or not last_name or not email:
            flash("First name, last name, and email are required!", "danger")
            return redirect(url_for("edit_profile"))

        if len(first_name) > 30 or len(last_name) > 30 or (middle_name and len(middle_name) > 30):
            flash("Names cannot exceed 30 characters", "danger")
            return redirect(url_for("edit_profile"))

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

        return redirect(url_for("dashboard"))

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

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


"""

@app.route("/students/<id_number>", methods=["POST"])
def update_student_route(id_number):

    if "user" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("login"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    middle_name = request.form.get("middle_name", "").strip()
    course_level = request.form.get("course_level")
    email = request.form.get("email")
    course = request.form.get("course")
    address = request.form.get("address")

    if not first_name or not last_name or not email:
        flash("First name, last name, and email are required!", "danger")
        return redirect(url_for("dashboard"))

    if len(first_name) > 30 or len(last_name) > 30 or (middle_name and len(middle_name) > 30):
        flash("Names cannot exceed 30 characters", "danger")
        return redirect(url_for("dashboard"))

    file = request.files.get("profile_photo")
    profile_filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{session['user']}_{file.filename}")
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        profile_filename = filename
        
    try:
        update_student({
            "id_number": session.get("user"),
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": middle_name,
            "course_level": int(course_level) if course_level else None,
            "email": email,
            "course": course,
            "address": address
        })
    except Exception as e:
        flash(f"Update failed: {str(e)}", "danger")
        return redirect(url_for("dashboard"))

    flash("Profile updated successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/")
def root():
    return redirect(url_for("login"))


@app.route("/editprofile")
def edit_profile():
    return render_template("editprofile.html")



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

# ---------------------------
# START SIT-IN (POST) & VIEW SIT-IN PAGE (GET)
# ---------------------------
@app.route("/admin/sitin", methods=["GET", "POST"])
def admin_sitin_page():
    if request.method == "POST":
        try:
            start_sitin(request.form)
            flash("Sit-in started successfully", "success")
            return redirect(url_for("admin_sitin_page"))
        except Exception as e:
            return f"Error: {e}", 400

    try:
        current = view_current_sitin()
        return render_template("admin_sitin.html", current=current)
    except Exception as e:
        return f"Error: {e}", 400


# ---------------------------
# END SIT-IN (POST)
# ---------------------------
@app.route("/admin/sitin/end/<int:session_id>", methods=["POST"])
def admin_end_sitin(session_id):
    try:
        end_sitin(session_id)
        flash("Sit-in ended successfully", "success")
        return redirect(url_for(""))
    except Exception as e:
        return f"Error: {e}", 400


# ---------------------------
# VIEW ALL SIT-IN RECORDS PAGE
# ---------------------------
@app.route("/admin/sitin/records")
def admin_sitin_records():
    try:
        records = view_sitin_records()
        return render_template("sitin_records.html", records=records)
    except Exception as e:
        return f"Error: {e}", 400

@app.route("/admin/students_data")
def admin_students_data():
    try:
        students = view_all_students()  # fetch all students from DB
        return {"students": students}   # return JSON
    except Exception as e:
        return {"error": str(e)}, 400

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
    app.run(debug=True)