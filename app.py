from flask import Flask, render_template, request, redirect, session, Response
from flask_session import Session
import mysql.connector
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.neighbors import KNeighborsRegressor
import pandas as pd
from sqlalchemy import create_engine
import datetime
import speech_recognition as sr
import pyttsx3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from io import BytesIO
import threading

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Dev$1234',
    'database': 'attendance',
    'auth_plugin': 'caching_sha2_password'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Global variables
spi = 0
res = ""
student = []
student2 = []
a_list = []
b_list = []
c_list = []
d_list = []
e_list = []
f_list = []
g_list = []
h_list = []
b1 = b2 = b3 = b4 = c1 = c2 = c3 = c4 = 0
err = ""
formt = ""
plt1 = []
plt2 = []
load = ""
dr = ""
admitted = ""
enrolled = ""
diff = ""
br = ""
show = []
area = ""
subs = []
clg_time = ""
ot_time = ""
sl_hr = ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/t_login', methods=['GET', 'POST'])
def t_login():
    st = "n"
    if request.method == 'POST':
        p = request.form['pswd']
        if p == 'abc':
            return redirect('/t_homepage')
        st = "The password is wrong..."
    return render_template('t_login.html', st=st)

@app.route('/a_login', methods=['GET', 'POST'])
def a_login():
    st = "n"
    if request.method == 'POST':
        p = request.form['pswd']
        if p == 'pqr':
            return redirect('/a_homepage')
        st = "The password is wrong..."
    return render_template('a_login.html', st=st)

@app.route('/s_homepage')
def s_homepage():
    return render_template('s_homepage.html')

@app.route('/t_homepage')
def t_homepage():
    return render_template('t_homepage.html')

@app.route('/a_homepage')
def a_homepage():
    return render_template('a_homepage.html')

@app.route('/a_upload_data', methods=['GET', 'POST'])
def a_upload_data():
    ms = ""
    if request.method == 'POST':
        try:
            mysql_url = 'mysql+mysqlconnector://root:Dev$1234@localhost:3306/attendance'
            engine = create_engine(mysql_url)

            sem = str(request.form['sem'])
            uploaded_file = request.files['file1']
            theory = int(request.form['theory'])
            practical = int(request.form['practical'])
            subjects = [request.form[f's{i}'].lower() for i in range(1, 5)]

            if uploaded_file and uploaded_file.filename.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
                required_cols = ["eno", "name", "gender"]
                
                if all(col in df.columns for col in required_cols):
                    sub = pd.read_excel('static/subjects.xlsx')
                    sub[sem] = subjects
                    sub.to_excel('static/subjects.xlsx', index=False)
                    
                    n = len(df)
                    splits = [(0, theory), (theory, theory * 2), (theory * 2, n)]
                    dfs = [pd.DataFrame(df[start:end]) for start, end in splits]

                    # Create table names and upload data
                    for i, subject in enumerate(subjects):
                        for j, df_split in enumerate(dfs):
                            table_name = f"{sem}_{chr(97+j)}_{subject}"
                            df_split.to_sql(table_name, con=engine, index=False, if_exists='replace')

                    # Handle practical groups
                    p = int(n / practical)
                    r1, r2 = 0, practical
                    for t in range(1, p + 1):
                        tbname = f"{sem}_p{t}"
                        d = pd.DataFrame(df[r1:r2])
                        d.to_sql(tbname, con=engine, index=False, if_exists='replace')
                        r1, r2 = r2, r2 + practical
                    
                    if r1 < n:
                        tbname = f"{sem}_p{p + 1}"
                        d = pd.DataFrame(df[r1:n])
                        d.to_sql(tbname, con=engine, index=False, if_exists='replace')

                    ms = "You registered the attendance sheet successfully..."
                else:
                    ms = "Not all required columns present. Please check the format."
            else:
                ms = "Invalid file format. Please upload an .xlsx file."
        except Exception as e:
            ms = f"Some Error Occurred: {str(e)}"

    return render_template('a_upload_data.html', ms=ms)

@app.route('/s_predict', methods=['GET', 'POST'])
def s_predict():
    global spi, res
    if request.method == 'POST':
        try:
            mid_marks1 = float(request.form['m1'])
            mid_marks2 = float(request.form['m2'])
            
            data = pd.read_csv("static/Training.csv")
            
            # Result prediction
            X = data[['Mid1', 'Mid2']]
            y = data['Result']
            m1 = LogisticRegression()
            m1.fit(X, y)
            res = m1.predict([[mid_marks1, mid_marks2]])[0]
            
            # SPI prediction
            y_spi = data['SPI']
            m2 = KNeighborsRegressor(n_neighbors=5)
            m2.fit(X, y_spi)
            spi = m2.predict([[mid_marks1, mid_marks2]])[0]
        except Exception as e:
            print(f"Prediction error: {str(e)}")
    return render_template('s_predict.html', spi=spi, res=res)

@app.route('/t_take_attendance', methods=['GET', 'POST'])
def t_take_attendance():
    msg = ""
    li = []
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()

        if 'students' not in session:
            session['students'] = []

        form_type = request.form.get('form_type')

        if request.method == 'POST':
            if form_type == 'f1':
                sem = request.form['sem2']
                div = request.form['div2']
                mycursor.execute('SHOW TABLES')
                for (table_name,) in mycursor:
                    parts = table_name.split('_')
                    if parts[0] == sem and parts[1] == div:
                        li.append(table_name)

        selected_table = request.form.get('selected_table', session.get("table"))
        session["table"] = selected_table

        if selected_table and form_type == 'f2':
            today = datetime.datetime.now().strftime('%d_%m_%Y')
            
            try:
                mycursor.execute(f"DESCRIBE {selected_table}")
                existing_columns = [col[0] for col in mycursor]
                if today not in existing_columns:
                    mycursor.execute(f"ALTER TABLE {selected_table} ADD {today} VARCHAR(2)")
                    mydb.commit()
            except mysql.connector.Error as e:
                msg = f"Database error: {e}"

            mycursor.execute(f"SELECT eno FROM {selected_table}")
            enos = [str(eno[0])[-3:] for eno in mycursor]

            def process_student(p):
                try:
                    eno = enos[p]
                    engine = pyttsx3.init()
                    engine.setProperty('voice', engine.getProperty('voices')[0].id)
                    engine.say(f"Student {eno}, please respond with present or absent")
                    engine.runAndWait()

                    recognizer = sr.Recognizer()
                    with sr.Microphone() as source:
                        recognizer.adjust_for_ambient_noise(source)
                        audio = recognizer.listen(source, timeout=5)

                    text = recognizer.recognize_google(audio).lower()
                    status = 'P' if 'present' in text or 'yes' in text else 'A'
                    
                    mycursor.execute(f"UPDATE {selected_table} SET {today} = %s WHERE eno = %s", 
                                    (status, int(enos[p])))
                    mydb.commit()
                except Exception as e:
                    print(f"Error processing student {p}: {str(e)}")
                    mycursor.execute(f"UPDATE {selected_table} SET {today} = 'A' WHERE eno = %s", 
                                    (int(enos[p]),))
                    mydb.commit()

            threads = []
            for p in range(len(enos)):
                thread = threading.Thread(target=process_student, args=(p,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            msg = "Attendance successfully taken"

        elif selected_table and form_type == 'f3':
            mycursor.execute(f"SELECT eno FROM {selected_table}")
            session['students'] = [str(eno[0]) for eno in mycursor]
            return render_template('t_take_attendance.html', msg=msg, student=session['students'], li=li)

        elif form_type == 'f4':
            today = datetime.datetime.now().strftime('%d_%m_%Y')
            mycursor.execute(f"ALTER TABLE {selected_table} ADD {today} VARCHAR(2)")
            mydb.commit()
            
            for eno in session.get('students', []):
                status = request.form.get(eno, 'A')
                mycursor.execute(f"UPDATE {selected_table} SET {today} = %s WHERE eno = %s", 
                               (status, eno))
                mydb.commit()
            msg = "Attendance successfully taken"

    except Exception as e:
        msg = f"Error: {str(e)}"
    finally:
        mycursor.close()
        mydb.close()

    return render_template('t_take_attendance.html', li=li, msg=msg, student=session.get('students', []))

@app.route('/t_analyze_attendance', methods=['GET', 'POST'])
def analyze_attendance():
    p = a = avg = tot_avg = male = female = choose = rang = 0
    below_stu = []
    li = []
    
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()

        form_type = request.form.get('form_type')

        if request.method == 'POST' and form_type == 'f1':
            sem = request.form['sem3']
            mycursor.execute('SHOW TABLES')
            li = [table[0] for table in mycursor if table[0].startswith(sem)]

        selected_table = request.form.get('selected_table')
        
        if selected_table:
            if form_type == 'f2':
                choose = 1
                mycursor.execute(f"SELECT * FROM {selected_table}")
                records = mycursor.fetchall()
                
                averages = []
                male_avg = []
                female_avg = []
                
                for record in records:
                    p = sum(1 for val in record[3:] if val == 'P')
                    a = len(record[3:]) - p
                    avg = (100 * p) / (p + a) if (p + a) > 0 else 0
                    averages.append(avg)
                    
                    if record[2] == 'male':
                        male_avg.append(avg)
                    else:
                        female_avg.append(avg)
                
                tot_avg = sum(averages) / len(averages) if averages else 0
                male = sum(male_avg) / len(male_avg) if male_avg else 0
                female = sum(female_avg) / len(female_avg) if female_avg else 0
                
                plt.bar(['Male', 'Female'], [male, female], color=['#668cff', '#ff99cc'], width=0.5)
                plt.xlabel("Gender of Student")
                plt.ylabel("Average Attendance in percentage")
                plt.savefig('static/graph_analyse.png')
                plt.close()

            elif form_type == 'f3':
                choose = 2
                en = request.form['enrollment_number']
                mycursor.execute(f"SELECT * FROM {selected_table} WHERE eno = %s", (en,))
                record = mycursor.fetchone()
                
                if record:
                    p = sum(1 for val in record[3:] if val == 'P')
                    a = len(record[3:]) - p
                    avg = (100 * p) / (p + a) if (p + a) > 0 else 0
                    
                    plt.pie([a, p], labels=['Absent', 'Present'], colors=['red', '#3399ff'], 
                           autopct='%1.1f%%', startangle=90)
                    plt.savefig('static/graph_analyse.png')
                    plt.close()

            elif form_type == "f4":
                choose = 3
                rang = int(request.form['percentage'])
                mycursor.execute(f"SELECT * FROM {selected_table}")
                records = mycursor.fetchall()
                
                below = 0
                for record in records:
                    p = sum(1 for val in record[3:] if val == 'P')
                    a = len(record[3:]) - p
                    avg = (100 * p) / (p + a) if (p + a) > 0 else 0
                    
                    if avg < rang:
                        below += 1
                        below_stu.append(record[0])
                
                above = len(records) - below
                plt.pie([below, above], labels=['Below range', 'Above range'], 
                       colors=['#d9b38c', '#996633'], autopct='%1.1f%%', startangle=90)
                plt.savefig('static/graph_analyse.png')
                plt.close()

    except Exception as e:
        print(f"Analysis error: {str(e)}")
    finally:
        mycursor.close()
        mydb.close()

    return render_template('t_analyze_attendance.html', li=li, avg=avg, tot_avg=tot_avg, 
                         male=male, female=female, choose=choose, below_stu=below_stu, rang=rang)

@app.route('/s_analyze_attendance', methods=['GET', 'POST'])
def analyze_attendance2():
    p = a = avg = tot_avg = male = female = choose = rang = 0
    below_stu = []
    li = []
    
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()

        form_type = request.form.get('form_type')

        if request.method == 'POST' and form_type == 'f1':
            sem = request.form['sem3']
            mycursor.execute('SHOW TABLES')
            li = [table[0] for table in mycursor if table[0].startswith(sem)]

        selected_table = request.form.get('selected_table')
        
        if selected_table:
            if form_type == 'f2':
                choose = 1
                mycursor.execute(f"SELECT * FROM {selected_table}")
                records = mycursor.fetchall()
                
                averages = []
                male_avg = []
                female_avg = []
                
                for record in records:
                    p = sum(1 for val in record[3:] if val == 'P')
                    a = len(record[3:]) - p
                    avg = (100 * p) / (p + a) if (p + a) > 0 else 0
                    averages.append(avg)
                    
                    if record[2] == 'male':
                        male_avg.append(avg)
                    else:
                        female_avg.append(avg)
                
                tot_avg = sum(averages) / len(averages) if averages else 0
                male = sum(male_avg) / len(male_avg) if male_avg else 0
                female = sum(female_avg) / len(female_avg) if female_avg else 0
                
                plt.bar(['Male', 'Female'], [male, female], color=['#668cff', '#ff99cc'], width=0.5)
                plt.xlabel("Gender of Student")
                plt.ylabel("Average Attendance in percentage")
                plt.savefig('static/graph_analyse.png')
                plt.close()

            elif form_type == 'f3':
                choose = 2
                en = request.form['enrollment_number']
                mycursor.execute(f"SELECT * FROM {selected_table} WHERE eno = %s", (en,))
                record = mycursor.fetchone()
                
                if record:
                    p = sum(1 for val in record[3:] if val == 'P')
                    a = len(record[3:]) - p
                    avg = (100 * p) / (p + a) if (p + a) > 0 else 0
                    
                    plt.pie([a, p], labels=['Absent', 'Present'], colors=['red', '#3399ff'], 
                           autopct='%1.1f%%', startangle=90)
                    plt.savefig('static/graph_analyse.png')
                    plt.close()

            elif form_type == "f4":
                choose = 3
                rang = int(request.form['percentage'])
                mycursor.execute(f"SELECT * FROM {selected_table}")
                records = mycursor.fetchall()
                
                below = 0
                for record in records:
                    p = sum(1 for val in record[3:] if val == 'P')
                    a = len(record[3:]) - p
                    avg = (100 * p) / (p + a) if (p + a) > 0 else 0
                    
                    if avg < rang:
                        below += 1
                        below_stu.append(record[0])
                
                above = len(records) - below
                plt.pie([below, above], labels=['Below range', 'Above range'], 
                       colors=['#d9b38c', '#996633'], autopct='%1.1f%%', startangle=90)
                plt.savefig('static/graph_analyse.png')
                plt.close()

    except Exception as e:
        print(f"Analysis error: {str(e)}")
    finally:
        mycursor.close()
        mydb.close()

    return render_template('s_analyze_attendance.html', li=li, avg=avg, tot_avg=tot_avg, 
                         male=male, female=female, choose=choose, below_stu=below_stu, rang=rang)



@app.route('/t_dwn_attendance', methods=['GET', 'POST'])
def t_dwn_attendance():
    tables = []
    if request.method == 'POST' and request.form.get('form_type') == 'f1':
        try:
            semester = request.form['sem2']
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SHOW TABLES')
                    tables = [table[0] for table in cursor if table[0].startswith(str(semester))]
        except Exception as e:
            print(f"Error fetching tables: {str(e)}")
    return render_template("t_dwn_attendance.html", li=tables)

@app.route('/a_drop_attendance', methods=['GET', 'POST'])
def a_drop_attendance():
    message = ""
    if request.method == 'POST':
        semester = request.form.get('sem2')
        if semester:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute('SHOW TABLES')
                        tables = [table[0] for table in cursor if table[0].startswith(str(semester))]
                        
                        for table in tables:
                            try:
                                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                                conn.commit()
                            except Exception as e:
                                message = f"Error dropping table {table}: {str(e)}"
                                break
                        
                        if not message:
                            message = "Attendance Sheets deleted successfully"
            except mysql.connector.Error as err:
                message = f"MySQL Error: {str(err)}"
            except Exception as e:
                message = f"Error: {str(e)}"
    return render_template("a_drop_attendance.html", msg=message)

@app.route('/t_dwn_attendance2', methods=['GET', 'POST'])
def t_dwn_attendance2():
    if request.method == 'POST' and request.form.get('form_type') == 'f2':
        selected_table = request.form.get('selected_table')
        if selected_table:
            try:
                with get_db_connection() as conn:
                    df = pd.read_sql(f"SELECT * FROM {selected_table}", conn)
                    
                    output = BytesIO()
                    df.to_excel(output, index=False)
                    output.seek(0)
                    
                    return Response(
                        output,
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f"attachment;filename={selected_table}.xlsx"}
                    )
            except Exception as e:
                print(f"Error downloading attendance: {str(e)}")
    return redirect('/t_dwn_attendance')

class StudentGrouper:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.a_list = []
        self.b_list = []
        self.c_list = []
        self.d_list = []
        self.e_list = []
        self.f_list = []
        self.g_list = []
        self.h_list = []
        self.b_counts = [0, 0, 0, 0]
        self.c_counts = [0, 0, 0, 0]
        self.error = ""
        self.load = ""
        self.plot_flags = [False, False]
    
    def process_file(self, file):
        try:
            self.reset()
            
            if file.filename.endswith('.xlsx'):
                data = pd.read_excel(file)
            elif file.filename.endswith('.csv'):
                data = pd.read_csv(file)
            else:
                self.error = "Invalid file format. Please upload .xlsx or .csv"
                return
            
            if all(col in data.columns for col in ['eno', 'percentage']):
                self._process_percentage_data(data)
            elif all(col in data.columns for col in ['eno', 'spi']):
                self._process_spi_data(data)
            else:
                self.error = "File must contain either 'eno' and 'percentage' or 'eno' and 'spi' columns"
                
        except Exception as e:
            self.error = f"Error processing file: {str(e)}"
    
    def _process_percentage_data(self, data):
        data['percentage'] = pd.to_numeric(data['percentage'], errors='coerce')
        data = data.dropna(subset=['percentage'])
        
        for _, row in data.iterrows():
            perc = row['percentage']
            entry = f"Enrollment number: {row['eno']}, Percentage: {perc}"
            
            if 80 <= perc <= 100:
                self.a_list.append(entry)
            elif 60 <= perc < 80:
                self.b_list.append(entry)
            elif 40 <= perc < 60:
                self.c_list.append(entry)
            elif 35 <= perc < 40:
                self.d_list.append(entry)
        
        self.b_counts = [len(self.a_list), len(self.b_list), len(self.c_list), len(self.d_list)]
        self._create_plot(
            ["100-80", "80-60", "60-40", "below 40"],
            self.b_counts,
            '#219F94',
            "Percentage range",
            "Number of students"
        )
        self.load = "yes"
        self.plot_flags = [True, False]
    
    def _process_spi_data(self, data):
        data['spi'] = pd.to_numeric(data['spi'], errors='coerce')
        data = data.dropna(subset=['spi'])
        
        for _, row in data.iterrows():
            spi_val = row['spi']
            entry = f"Enrollment number: {row['eno']}, SPI: {spi_val}"
            
            if 8 <= spi_val <= 10:
                self.e_list.append(entry)
            elif 6 <= spi_val < 8:
                self.f_list.append(entry)
            elif 4 <= spi_val < 6:
                self.g_list.append(entry)
            elif spi_val < 4:
                self.h_list.append(entry)
        
        self.c_counts = [len(self.e_list), len(self.f_list), len(self.g_list), len(self.h_list)]
        self._create_plot(
            ["10-8", "8-6", "6-4", "below 4"],
            self.c_counts,
            '#EB455F',
            "SPI range",
            "Number of students"
        )
        self.load = "yes"
        self.plot_flags = [False, True]
    
    def _create_plot(self, bins, values, color, xlabel, ylabel):
        plt.figure()
        plt.bar(bins, values, color=color)
        plt.xlabel(xlabel, fontdict={'color': color, 'size': 15})
        plt.ylabel(ylabel, fontdict={'color': color, 'size': 15})
        plt.savefig('static/graph_analyse.png')
        plt.close()

student_grouper = StudentGrouper()

@app.route('/t_group_students', methods=['GET', 'POST'])
def t_group_students():
    if request.method == 'POST':
        file = request.files.get('file1')
        if file and file.filename:
            student_grouper.process_file(file)
    
    return render_template(
        't_group_students.html',
        a_list=student_grouper.a_list,
        b_list=student_grouper.b_list,
        c_list=student_grouper.c_list,
        d_list=student_grouper.d_list,
        e_list=student_grouper.e_list,
        f_list=student_grouper.f_list,
        g_list=student_grouper.g_list,
        h_list=student_grouper.h_list,
        b1=student_grouper.b_counts[0],
        b2=student_grouper.b_counts[1],
        b3=student_grouper.b_counts[2],
        b4=student_grouper.b_counts[3],
        c1=student_grouper.c_counts[0],
        c2=student_grouper.c_counts[1],
        c3=student_grouper.c_counts[2],
        c4=student_grouper.c_counts[3],
        load=student_grouper.load,
        plt1=student_grouper.plot_flags[0],
        plt2=student_grouper.plot_flags[1],
        err=student_grouper.error
    )

class DropoutPredictor:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.dr = ""
        self.admitted = ""
        self.enrolled = ""
        self.diff = ""
        self.branch = ""
        self.show_result = False
        self.error = ""
        self.area = ""
    
    def predict(self, branch, year, area):
        try:
            self.reset()
            self.branch = branch
            self.area = area
            
            file_name = "static/Dropout_c2d.csv" if area == 'C2D' else "static/Dropout_regular.csv"
            data = pd.read_csv(file_name)
            
            if branch == 'All':
                X = data[['year']]
                a = data['total admitted']
                e = data['total enrolled']
            else:
                branch_col = {
                    'IT': 'IT',
                    'Automobile': 'Automobile',
                    'CACDDM': 'CACDDM',
                    'Chemical': 'Chemical',
                    'Civil': 'Civil',
                    'EC': 'EC',
                    'Electrical': 'Electrical',
                    'Fabrication': 'Fabrication',
                    'Mechanical': 'Mechnical',
                    'Textile': 'Textile',
                    'Mech in CAD-CAM': 'MC'
                }.get(branch, 'IT')
                
                X = data[['year']]
                a = data[f'{branch_col} admitted']
                e = data[f'{branch_col} enrolled']
            
            # Predict admissions
            model_admit = LinearRegression()
            model_admit.fit(X, a)
            self.admitted = max(0, int(model_admit.predict([[year]])[0]))
            
            # Predict enrollments
            model_enroll = LinearRegression()
            model_enroll.fit(X, e)
            self.enrolled = max(0, int(model_enroll.predict([[year]])[0]))
            
            # Apply maximum admission constraints for regular area
            if area == 'Regular':
                max_data = pd.read_csv('static/Max_admissions.csv')
                max_admit = {
                    'IT': max_data.loc[0, 'branch_max'],
                    'Automobile': max_data.loc[1, 'branch_max'],
                    'CACDDM': max_data.loc[2, 'branch_max'],
                    'Chemical': max_data.loc[3, 'branch_max'],
                    'Civil': max_data.loc[4, 'branch_max'],
                    'EC': max_data.loc[5, 'branch_max'],
                    'Electrical': max_data.loc[6, 'branch_max'],
                    'Fabrication': max_data.loc[7, 'branch_max'],
                    'Mechanical': max_data.loc[8, 'branch_max'],
                    'Textile': max_data.loc[9, 'branch_max'],
                    'Mech in CAD-CAM': max_data.loc[10, 'branch_max'],
                    'All': max_data.loc[11, 'branch_max']
                }.get(branch, 0)
                
                self.admitted = min(self.admitted, max_admit)
            
            # Calculate final values
            self.enrolled = min(self.enrolled, self.admitted)
            self.diff = self.admitted - self.enrolled
            self.dr = int((self.diff * 100) / self.admitted) if self.admitted > 0 else 0
            self.show_result = True
            
        except Exception as e:
            self.error = f"Error in prediction: {str(e)}"
            print(self.error)

dropout_predictor = DropoutPredictor()

@app.route('/t_dropout', methods=['GET', 'POST'])
def t_dropout():
    if request.method == 'POST':
        branch = request.form.get('branch', '')
        try:
            year = int(request.form.get('year', 0))
        except ValueError:
            year = 0
        area = request.form.get('Select area', '')
        
        dropout_predictor.predict(branch, year, area)
    
    return render_template(
        't_dropout.html',
        dr=dropout_predictor.dr,
        admitted=dropout_predictor.admitted,
        enrolled=dropout_predictor.enrolled,
        diff=dropout_predictor.diff,
        br=dropout_predictor.branch,
        show=dropout_predictor.show_result,
        area=dropout_predictor.area,
        err=dropout_predictor.error
    )

class StudyPlanner:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.subjects = []
        self.clg_time = ""
        self.ot_time = ""
        self.sl_hr = ""
        self.show_plan = False
        self.message = ""
        self.subject_order = ["", "", "", ""]
    
    def load_subjects(self, semester):
        try:
            self.reset()
            sub = pd.read_excel('static/subjects.xlsx')
            if semester in sub.columns:
                session['subs2'] = sub[semester].tolist()
        except Exception as e:
            self.message = f"Error loading subjects: {str(e)}"
    
    def create_plan(self, form_data):
        try:
            self.subjects = session.get('subs2', [])
            if len(self.subjects) >= 4:
                self.subject_order = [
                    form_data.get(self.subjects[0], '1'),
                    form_data.get(self.subjects[1], '2'),
                    form_data.get(self.subjects[2], '3'),
                    form_data.get(self.subjects[3], '4')
                ]
                self.clg_time = form_data.get('time', '')
                self.ot_time = form_data.get('ot_time', '')
                self.sl_hr = form_data.get('sleep_hours', '')
                self.show_plan = True
                session['subs2'] = []
        except Exception as e:
            self.message = "Please enter difficulty level properly"

study_planner = StudyPlanner()

@app.route('/s_studyplanner', methods=['GET', 'POST'])
def s_studyplanner():
    if request.method == 'POST':
        form_type = request.form.get('f_type')
        if form_type == 'f1':
            semester = request.form.get('semester')
            study_planner.load_subjects(semester)
        elif form_type == 'f2':
            study_planner.create_plan(request.form)
    
    return render_template(
        's_studyplanner.html',
        subs=session.get('subs2', []),
        count=len(session.get('subs2', [])),
        show=study_planner.show_plan,
        clg_time=study_planner.clg_time,
        ot_time=study_planner.ot_time,
        sl_hr=study_planner.sl_hr,
        s1=study_planner.subject_order[0],
        s2=study_planner.subject_order[1],
        s3=study_planner.subject_order[2],
        s4=study_planner.subject_order[3],
        ms=study_planner.message
    )

@app.route('/a_maximum_admissions', methods=['GET', 'POST'])
def a_maximum_admissions():
    if request.method == 'POST':
        branches = [
            'IT', 'Automobile', 'CACDDM', 'Chemical', 'Civil',
            'EC', 'Electrical', 'Fabrication', 'Mechanical',
            'Textile', 'Mech in CAD-CAM', 'All'
        ]
        values = [int(request.form.get(f'b_{branch}', 0)) for branch in branches]
        
        try:
            df = pd.DataFrame({'branch': branches, 'branch_max': values})
            df.to_csv('static/Max_admissions.csv', index=False)
        except Exception as e:
            print(f"Error saving max admissions: {str(e)}")
    
    return render_template('a_maximum_admissions.html')

if __name__ == "__main__":
    app.run(debug=True)