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
            return render_template("register.html", **form_data)

        if password_input != confirm_password:
            flash("Passwords do not match", "warning")
            return render_template("register.html", **form_data)

        if len(password_input) < 8:
            flash("Password must be at least 8 characters long", "danger")
            return render_template("register.html", **form_data)

        if len(first_name) > 30 or len(last_name) > 30 or (middle_name and len(middle_name) > 30):
            flash("Names cannot exceed 30 characters", "danger")
            return render_template("register.html", **form_data)

        if len(id_number) != 8:
            flash("ID number must be 8 digits!", "danger")
            return render_template("register.html", **form_data)

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
            return render_template("register.html", **form_data)

        return redirect(url_for("login"))

    return render_template("register.html")

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


@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        id_number = request.form.get("id_number")
        password = request.form.get("password")
        
        if not id_number or not password:
            return render_template("login.html", error="ID and password is required")
        
        if student_verify_password(id_number, password):
            session["user"] = id_number
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    student = view_students(session["user"])
    full_name = f"{student['first_name']} {student['last_name']}"
    course = student['course']
    course_level = student['course_level']
    email = student['email']
    address = student['address']
    sessions_remaining = student['sessions_remaining']
    
    return render_template("dashboard.html", 
    name=full_name,
    course=course,
    year=course_level,
    email = email,
    address=address,
    sessions_remaining = sessions_remaining
    )

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/editprofile")
def edit_profile():
    return render_template("editprofile.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        id_number = request.form.get("id_number")
        password = request.form.get("password")

        admin = admin_verify_password(id_number, password)
        if admin:
          
            session["admin_id"] = admin["id_number"]
            session["admin_name"] = admin.get("name", "Admin")  # optional
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid ID number or password", "danger")
            return redirect(url_for("admin_login"))

  
    return render_template("admin_login.html")
# ---------------------------
# ADMIN DASHBOARD
# ---------------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("admin_login"))

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
        "admin_dashboard.html",
        total_students=total_students,
        current_count=current_count,
        total_sitin=total_sitin,
        chart_labels=json.dumps(chart_labels),
        chart_values=json.dumps(chart_values)
    )
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


if __name__ == "__main__":
    app.run(debug=True)