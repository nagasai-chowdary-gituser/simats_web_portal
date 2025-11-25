from flask import Flask, request, render_template

app = Flask(__name__)

# Convert empty input to 0 safely
def to_int(value):
    if value is None:
        return 0
    value = value.strip()
    return int(value) if value.isdigit() else 0


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/attendance', methods=['GET', 'POST'])
def attendance_calc():
    if request.method == 'POST':
        total_class = float(request.form.get('total_classes'))
        no_of_class_attended = float(request.form.get('no_of_classes_attended'))

        result = (no_of_class_attended / total_class) * 100

        return render_template('attendance.html', results=round(result, 2))

    return render_template('attendance.html')


@app.route('/cgpa', methods=['GET','POST'])
def cgpa_calc():
    if request.method == 'POST':

        def safe(v):
            try:
                if v is None:
                    return 0
                v = v.strip()
                return int(v) if v != "" else 0
            except:
                return 0

        s_grades = safe(request.form.get('s_grades'))
        a_grades = safe(request.form.get('a_grades'))
        b_grades = safe(request.form.get('b_grades'))
        c_grades = safe(request.form.get('c_grades'))
        d_grades = safe(request.form.get('d_grades'))
        e_grades = safe(request.form.get('e_grades'))

        cgpa_total = (
            s_grades * 10 +
            a_grades * 9 +
            b_grades * 8 +
            c_grades * 7 +
            d_grades * 6 +
            e_grades * 5
        )

        total_subs = s_grades + a_grades + b_grades + c_grades + d_grades + e_grades

        if total_subs == 0:
            return render_template('cgpa.html', results="0.00", words="Enter at least one subject")

        cgpa_per = round(cgpa_total / total_subs, 2)

        # performance text
        if cgpa_per > 9:
            words = "Excellent ⭐"
        elif cgpa_per >= 8:
            words = "Very Good 👍"
        elif cgpa_per >= 7:
            words = "Good 🙂"
        elif cgpa_per >= 6:
            words = "Average 😐"
        else:
            words = "Needs Improvement ⚠️"

        return render_template('cgpa.html', results=cgpa_per, words=words)

    return render_template('cgpa.html', results="", words="")



if __name__ == "__main__":
    app.run(debug=True, port=5050)
