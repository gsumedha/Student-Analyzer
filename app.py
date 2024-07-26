from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import matplotlib.pyplot as plt
import pandas as pd
import os
import io
import base64
import numpy as np

app = Flask(__name__)
app.secret_key = "secret_key"
app.config['UPLOAD_FOLDER'] = 'uploads'
client = MongoClient('mongodb://localhost:27017')
db = client['Student_data']
collection = db['Students']

@app.route("/", methods=["GET", "POST"])
def index():
    students = list(collection.find())
    return render_template("index.html")

@app.route("/data", methods=["POST"])
def datahandle():
    if request.method == "POST":
        roll_number = request.form["roll_number"]
        existing_student = collection.find_one({"roll_number": roll_number})
        
        if existing_student:
            return "Roll number already exists. Please use a different roll number.", 400
        
        student_data = {
            "name": request.form["name"],
            "class": request.form["class"],
            "roll_number": roll_number,
            "1st_semester": request.form["cgpa1"],
            "2nd_semester": request.form["cgpa2"],
            "3rd_semester": request.form["cgpa3"],
            "4th_semester": request.form["cgpa4"],
            "5th_semester": request.form["cgpa5"],
            "6th_semester": request.form["cgpa6"],
            "7th_semester": request.form["cgpa7"],
            "8th_semester": request.form["cgpa8"]
        }
        collection.insert_one(student_data)
        return "Data submitted successfully!"
    

@app.route('/dash_board', methods=["GET", "POST"])
def dash_board():
    return render_template("dash_board.html")

@app.route("/data_visuals", methods=["GET", "POST"])
def data_vision():
    if request.method == "POST":
        roll_number = request.form["roll_number"]
        class_name = request.form["class"]

        # Retrieve data from MongoDB
        student_data = collection.find_one({"roll_number": roll_number, "class": class_name})
        if student_data:
            # Print the student data to verify keys
            print("Student Data:", student_data)

            # Calculate class averages
            class_averages = calculate_class_averages(class_name)

            # Generate the graph
            img = generate_graph(student_data, class_averages)
            return render_template("result.html", img=img)
        else:
            flash("No data found for the given roll number and class", "error")
            return redirect(url_for('data_vision'))
    return render_template("dash_board.html")

def calculate_class_averages(class_name):
    # Retrieve all students in the specified class
    students = collection.find({"class": class_name})
    
    # Initialize lists to hold scores for each semester
    semesters = ["1st_semester", "2nd_semester", "3rd_semester", "4th_semester", "5th_semester", "6th_semester", "7th_semester", "8th_semester"]
    semester_scores = {semester: [] for semester in semesters}
    
    # Collect all scores
    for student in students:
        for semester in semesters:
            score = student.get(semester)
            if score is not None and score != '':
                semester_scores[semester].append(float(score))
    
    # Calculate average scores
    averages = {semester: np.mean(scores) if scores else np.nan for semester, scores in semester_scores.items()}
    return averages

def generate_graph(student_data, class_averages):
    plt.switch_backend('Agg')
    semesters = ["1st_semester", "2nd_semester", "3rd_semester", "4th_semester", "5th_semester", "6th_semester", "7th_semester", "8th_semester"]
    student_scores = []

    for semester in semesters:
        score = student_data.get(semester)
        if score is None or score == '':
            score = np.nan  # Use numpy's nan value
        else:
            score = float(score)
        student_scores.append(score)
    
    class_avg_scores = [class_averages[semester] for semester in semesters]

    # Create a mask for missing values
    mask = ~np.isnan(student_scores)

    # Plot the scores, using the mask to ignore missing values
    plt.figure(figsize=(10, 5))
    plt.plot(np.array(semesters)[mask], np.array(student_scores)[mask], marker='o', linestyle='-', color='b', label='Student')
    plt.plot(np.array(semesters)[mask], np.array(class_avg_scores)[mask], marker='o', linestyle='-', color='r', label='Class Average')
    plt.title('CGPA Progress')
    plt.xlabel('Semester')
    plt.ylabel('CGPA')
    plt.ylim(0, 10)
    plt.legend()
    plt.grid(True)

    # Save plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    # Encode the image to base64 to send to the template
    img_base64 = base64.b64encode(img.getvalue()).decode()
    return img_base64

@app.route("/view_data", methods=["GET"])
def view_data():
    # Retrieve all records from MongoDB
    all_students = collection.find()
    return render_template("view_data.html", students=all_students)


@app.route("/update", methods=["GET", "POST"])
def update():
    roll_number = request.args.get("roll_number")
    student_data = collection.find_one({"roll_number": roll_number})
    if request.method == "POST":
        updated_data = {
            "name": request.form["name"],
            "class": request.form["class"],
            "1st_semester": request.form["cgpa1"],
            "2nd_semester": request.form["cgpa2"],
            "3rd_semester": request.form["cgpa3"],
            "4th_semester": request.form["cgpa4"],
            "5th_semester": request.form["cgpa5"],
            "6th_semester": request.form["cgpa6"],
            "7th_semester": request.form["cgpa7"],
            "8th_semester": request.form["cgpa8"]
        }
        collection.update_one({"roll_number": roll_number}, {"$set": updated_data})
        flash("Data updated successfully!", "success")
        return redirect(url_for("index"))

    return render_template("update.html", student=student_data)


@app.route('/delete', methods=['POST'])
def delete_student():
    roll_number = request.form.get('roll_number')
    if roll_number:
        result = collection.delete_one({"roll_number": roll_number})
        if result.deleted_count > 0:
            flash('Data deleted successfully!', 'success')
        else:
            flash('Student with Roll Number not found!', 'error')
    else:
        flash('Roll Number is required!', 'error')
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)




