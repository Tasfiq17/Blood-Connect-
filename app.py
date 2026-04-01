from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from flask import jsonify


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1749',  # Your MySQL password
    'database': 'blood_connect'
}

# Database Connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Decorator to prevent caching
def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return no_cache_view

# Add this custom filter for date formatting
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d'):
    if value is None:
        return ""
    if isinstance(value, str):
        return value  # Formatted as string
    return value.strftime(format)

# Login required decorator
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped_view

# Home Route
@app.route('/')
def home():
    return render_template('home.html')

# Log In
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['loginEmail']
        password = request.form['loginPassword']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and (user['user_type'] == 'Admin' and password == '1749' or check_password_hash(user['password'], password)):
            session['user_id'] = user['id']
            session['user_type'] = user['user_type']
            if user['user_type'] == 'Admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        
        # If we get here, login failed
        error = 'Invalid email or password'
        return render_template('login.html', error=error)
    
    # For GET requests or if there was a flash message
    return render_template('login.html')

# Registration Route
@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form['registerName']
        email = request.form['registerEmail']
        password = request.form['registerPassword']
        phone = request.form['registerPhone']
        dob = request.form['registerDOB']
        gender = request.form['registerGender']
        blood_group = request.form['registerBloodGroup']
        address = request.form['address']
        user_type = request.form['registerUserType']
    except KeyError as e:
        return render_template('login.html', register_error=f"Missing field: {str(e)}", show_register=True)

    if not all([name, email, password, phone, dob, gender, blood_group, address, user_type]):
        return render_template('login.html', register_error='All fields are required', show_register=True)

    if not email.endswith('@eastdelta.edu.bd'):
        return render_template('login.html', register_error='Only EDU emails allowed', show_register=True)

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO users (name, email, password, phone, dob, gender, blood_group, address, user_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, hashed_password, phone, dob, gender, blood_group, address, user_type))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    except mysql.connector.Error as err:
        return render_template('login.html', register_error=str(err), show_register=True)

# Logout Route
@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'success')
    response = make_response(redirect(url_for('home')))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# User Dashboard
@app.route('/dashboard')
@login_required
@no_cache
def user_dashboard():
    if session.get('user_type') == 'Admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user info
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    # Get user's blood requests
    cursor.execute("SELECT * FROM requests WHERE user_id = %s", (session['user_id'],))
    requests = cursor.fetchall()
    
    # Get user's notifications
    cursor.execute("""
        SELECT n.*, r.blood_group, r.hospital 
        FROM notifications n
        JOIN requests r ON n.request_id = r.id
        WHERE n.user_id = %s
        ORDER BY n.created_at DESC
    """, (session['user_id'],))
    notifications = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('dashboard.html', user=user, requests=requests, notifications=notifications)

# Admin Dashboard
@app.route('/adminDash')
@login_required
@no_cache
def admin_dashboard():
    if session.get('user_type') != 'Admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get stats
    cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE user_type != 'Admin'")
    total_users = cursor.fetchone()['total_users']
    
    cursor.execute("SELECT COUNT(*) as total_requests FROM requests")
    total_requests = cursor.fetchone()['total_requests']
    
    cursor.execute("SELECT COUNT(*) as active_donors FROM users WHERE user_type = 'Donor' AND is_active = TRUE")
    active_donors = cursor.fetchone()['active_donors']
    
    # Get all users
    cursor.execute("SELECT id, name, email, phone, blood_group, user_type, is_active FROM users")
    all_users = cursor.fetchall()
    
    # Get all requests with user names
    cursor.execute("""
        SELECT r.*, u.name as user_name 
        FROM requests r 
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
    """)
    all_requests = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('adminDash.html', 
                         total_users=total_users,
                         total_requests=total_requests,
                         active_donors=active_donors,
                         all_users=all_users,
                         all_requests=all_requests)

# Find Donor Route
@app.route('/findDonor')
@login_required
@no_cache
def find_donor():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, blood_group, address FROM users WHERE user_type = 'Donor' AND is_active = TRUE")
    donors = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('findDonors.html', donors=donors)

# Request List Route
@app.route('/reqList')
@login_required
@no_cache
def request_list():
    if session.get('user_type') != 'Admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT r.*, u.name FROM requests r JOIN users u ON r.user_id = u.id")
    requests = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('reqList.html', requests=requests)

# Settings Route
@app.route('/settings', methods=['GET', 'POST'])
@login_required
@no_cache
def settings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['editName']
        location = request.form['editLocation']
        contact = request.form['editContactNo']
        cursor.execute("""
            UPDATE users SET name = %s, address = %s, phone = %s WHERE id = %s
        """, (name, location, contact, session['user_id']))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()  # Refresh user data after update

    cursor.close()
    conn.close()
    return render_template('setting.html', user=user)

# Guide Route
@app.route('/guide')
def guide():
    return render_template('guide.html')

# Why Blood Connect Route
@app.route('/WhyBC')
def why_bc():
    return render_template('WhyBC.html')

# Contact Us Route
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Request Blood
@app.route('/request_blood', methods=['GET', 'POST'])
@login_required
@no_cache
def request_blood():
    if request.method == 'POST':
        blood_group = request.form['blood-group']
        hospital = request.form['hospital']
        required_date = request.form['date']
        urgency = request.form['urgency']
        notes = request.form.get('notes', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert the request with Approved status
        query = """
            INSERT INTO requests (user_id, blood_group, hospital, required_date, urgency, notes, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Approved')
        """
        cursor.execute(query, (session['user_id'], blood_group, hospital, required_date, urgency, notes))
        request_id = cursor.lastrowid
        
        # Get requester info
        cursor.execute("SELECT name, phone FROM users WHERE id = %s", (session['user_id'],))
        requester = cursor.fetchone()
        requester_name, requester_phone = requester
        
        # Find matching donors
        cursor.execute("""
            SELECT id FROM users 
            WHERE blood_group = %s 
            AND id != %s 
            AND user_type = 'Donor'
            AND is_active = TRUE
        """, (blood_group, session['user_id']))
        
        potential_donors = cursor.fetchall()
        
        # Create notifications
        notification_message = (
            f"URGENT: {requester_name} needs {blood_group} blood at {hospital}. "
            f"Contact: {requester_phone}. Needed by: {required_date}"
        )
        
        for donor in potential_donors:
            donor_id = donor[0]
            cursor.execute("""
                INSERT INTO notifications (user_id, request_id, message)
                VALUES (%s, %s, %s)
            """, (donor_id, request_id, notification_message))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Blood request submitted! Donors with matching blood type have been notified.', 'success')
        return redirect(url_for('user_dashboard'))
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('request_blood.html', today=today)

# Route to mark notifications as read 
@app.route('/mark_notifications_read', methods=['POST'])
@login_required
def mark_notifications_read():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notifications 
        SET is_read = TRUE 
        WHERE user_id = %s AND is_read = FALSE
    """, (session['user_id'],))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

# Route to check for unread notifications 
@app.route('/check_notifications')
@login_required
def check_notifications():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as unread_count 
        FROM notifications 
        WHERE user_id = %s AND is_read = FALSE
    """, (session['user_id'],))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'hasUnread': result[0] > 0})



if __name__ == '__main__':
    app.run(debug=True)

