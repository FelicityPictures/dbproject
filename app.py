import time
import os
import pymysql.cursors
import hashlib
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory
from werkzeug.utils import secure_filename

# upload folder
UPLOAD_FOLDER = ".\\uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
SALT = 'Felicity_Ng_CS-UY_3083'
# Initialize the app from Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3308,
                       user='root',
                       password='',
                       db='finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

def hello():
    return render_template('index.html')

@app.route('/')
@app.route('/home')
def home():
    if not session.get('logged_in'):
        return render_template('index.html')
    user = session['username']
    cursor = conn.cursor()
    query = """
            SELECT DISTINCT pID, postingDate, filePath, caption, firstName, lastName, username
            FROM photo JOIN person ON(photo.poster=person.username)
            WHERE pID in
                (SELECT pID
                FROM sharedwith NATURAL JOIN belongto
                WHERE username = %s
                UNION
                SELECT pID
                FROM Photo JOIN Follow ON(poster=followee)
                WHERE allFollowers=true AND followStatus=true AND follower = %s
                UNION
                SELECT pID
                FROM photo
                WHERE poster = %s)
            ORDER BY postingDate DESC
            """
    cursor.execute(query, (user, user, user))
    posts = cursor.fetchall()

    query = """
            SELECT pID, username, firstName, lastName
            FROM tag NATURAL JOIN person
            WHERE tagStatus=1 AND pID in
                (SELECT pID
                FROM sharedwith NATURAL JOIN belongto
                WHERE username = %s
                UNION
                SELECT pID
                FROM Photo JOIN Follow ON(poster=followee)
                WHERE allFollowers=true AND followStatus=true AND follower = %s
                UNION
                SELECT pID
                FROM photo
                WHERE poster = %s)
            """
    cursor.execute(query, (user, user, user))
    tags = cursor.fetchall()

    query = 'SELECT groupName, groupCreator FROM belongto WHERE username = %s'
    cursor.execute(query, (user))
    groups = cursor.fetchall()

    query = """
            SELECT *
            FROM reactto
            WHERE pID IN
                (SELECT pID
                FROM sharedwith NATURAL JOIN belongto
                WHERE username = %s
                UNION
                SELECT pID
                FROM Photo JOIN Follow ON(poster=followee)
                WHERE allFollowers=true AND followStatus=true AND follower = %s
                UNION
                SELECT pID
                FROM photo
                WHERE poster = %s)
            """
    cursor.execute(query, (user, user, user))
    reacts = cursor.fetchall()

    cursor.close()
    return render_template('home.html', username=user, posts=posts, tags=tags, groups=groups, reacts=reacts)

@app.route('/register')
def register():
    return render_template('register.html')

# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']+SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM person WHERE username = %s AND password = %s'
    cursor.execute(query, (username, hashed_password))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    cursor.close()
    if(data):
        # creates a session for the the user
        # session is tied to flask request context
        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('home'))
    else:
        # returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('index.html', loginError=error)

# Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']+SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    if(data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', registerError=error)
    else:
        ins = 'INSERT INTO person (username, password, firstName, lastName, email) VALUES (%s, %s, %s, %s, %s)'
        # cursor.execute(ins, (firstName, lastName, email, username, password))
        cursor.execute(ins, (username, hashed_password, firstName, lastName, email))
        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        username = session['username']
        cursor = conn.cursor()
        # check if the post request has the file part
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['photo']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            caption = request.form['caption']
            followers = request.form.getlist('followers')
            timeString = time.strftime('%Y-%m-%d %H:%M:%S')
            query = 'INSERT INTO photo (postingDate, filePath, allFollowers, caption, poster) VALUES(%s, %s, %s, %s, %s)'
            # WHAT HAPPENS IF NOTHING CHOSEN???
            if(len(followers) > 0 and followers[0] == "all"):
                # all followers
                cursor.execute(query, (timeString, filename, 1, caption, username))
                conn.commit()
            else:
                cursor.execute(query, (timeString, filename, 0, caption, username))
                conn.commit()
            query = 'SELECT LAST_INSERT_ID()'
            cursor.execute(query)
            pID = cursor.fetchall()
            pID = pID[0].get('LAST_INSERT_ID()')
            if(len(followers) > 0 and followers[0] != "all"):
                query = 'INSERT INTO sharedwith (pID, groupName, groupCreator) VALUES(%s, %s, %s)'
                for group in followers:
                    info = group.split(';')
                    cursor.execute(query, (pID, info[0], info[1]))
                    conn.commit()
            filename = str(pID) + "_" + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            query = 'UPDATE photo SET filePath = %s WHERE pID = %s'
            cursor.execute(query, (filename, pID))
            conn.commit()
        cursor.close()
    return redirect(url_for('home'))

@app.route('/react', methods=['GET', 'POST'])
def react():
    username = session['username']
    cursor = conn.cursor()
    photo = request.form['pID']
    react = request.form['react']
    comment = request.form['comment']

    query = 'SELECT * FROM reactto WHERE pID = %s AND username = %s'
    cursor.execute(query, (photo, username))
    data = cursor.fetchone()
    if(not data):
        query = 'INSERT INTO reactto (username, pID, reactionTime, comment, emoji) VALUES(%s, %s, %s, %s, %s)'
        timeString = time.strftime('%Y-%m-%d %H:%M:%S')
        #  pID, postingDate, filePath, allFollowers, caption, poster
        cursor.execute(query, (username, photo, timeString, comment, react))
        conn.commit()
    else:
        # change existing reaction?
        pass
    cursor.close()
    return redirect(url_for('home'))

@app.route('/connections')
def connections():
    if not session.get('logged_in'):
        return render_template('index.html')
    user = session['username']

    cursor = conn.cursor();
    query = 'SELECT * FROM follow WHERE followee = %s'
    cursor.execute(query, (user))
    connectionsData = cursor.fetchall()

    query = """
            SELECT * FROM person
            WHERE username != %s AND username NOT IN(
                SELECT followee
                FROM follow
                WHERE follower = %s
            )
            """
    cursor.execute(query, (user, user))
    otherUsersData = cursor.fetchall()

    query = 'SELECT * FROM follow WHERE follower = %s'
    cursor.execute(query, (user))
    followingData = cursor.fetchall()

    cursor.close()
    return render_template('connections.html', username=user, connections=connectionsData, otherUsers=otherUsersData, following=followingData)

@app.route('/follow', methods=['GET', 'POST'])
def follow():
    user = session['username']
    followee = request.form['followee']

    cursor = conn.cursor();

    query = 'SELECT * FROM follow WHERE follower = %s AND followee = %s'
    cursor.execute(query, (user, followee))
    data = cursor.fetchone()
    if(not data):
        ins = 'INSERT INTO follow (follower, followee, followStatus) VALUES(%s, %s, %s)'
        cursor.execute(ins, (user, followee, 0))
        conn.commit()
    cursor.close()
    return redirect(url_for('connections'))

@app.route('/approvefollow', methods=['GET', 'POST'])
def approvefollow():
    user = session['username']
    #grabs information from the forms
    follower = request.form['follower']

    cursor = conn.cursor();

    query = 'UPDATE follow SET followStatus = %s WHERE followee = %s AND follower = %s'
    cursor.execute(query, (1, user, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('connections'))

@app.route('/rejectfollow', methods=['GET', 'POST'])
def rejectfollow():
    user = session['username']
    #grabs information from the forms
    followee = request.form['followee']
    follower = request.form['follower']

    cursor = conn.cursor();

    query = 'DELETE FROM follow WHERE followee = %s AND follower = %s'
    cursor.execute(query, (followee, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('connections'))

@app.route('/groups')
def groups():
    if not session.get('logged_in'):
        return render_template('index.html')
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT groupName, description, groupCreator FROM belongto NATURAL JOIN friendgroup WHERE username = %s'
    cursor.execute(query, (user))
    userGroups = cursor.fetchall()

    query = 'SELECT * FROM belongto WHERE (groupName, groupCreator) IN (SELECT groupName, groupCreator FROM belongto WHERE username = %s)'
    cursor.execute(query, (user))
    membersOfGroup = cursor.fetchall()

    query = 'SELECT * FROM person WHERE username != %s'
    cursor.execute(query, (user))
    listOfOtherUsers = cursor.fetchall()

    cursor.close()
    return render_template('groups.html', username=user, availableUsers=listOfOtherUsers, group_list=userGroups, memberList=membersOfGroup)

# Create new group
@app.route('/newgroup', methods=['GET', 'POST'])
def newgroup():
    user = session['username']
    # grabs information from the forms
    groupName = request.form['groupName']
    description = request.form['description']
    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM friendgroup WHERE groupName = %s AND groupCreator = %s'
    cursor.execute(query, (groupName, user))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    if(data):
        # If the previous query returns data, then group exists
        error = "You already have a group with this name."
        query = 'SELECT * FROM belongto WHERE username = %s'
        cursor.execute(query, (user))
        data = cursor.fetchall()

        user = session['username']
        cursor = conn.cursor()
        query = 'SELECT * FROM belongto WHERE username = %s'
        cursor.execute(query, (user))
        data = cursor.fetchall()

        query = 'SELECT * FROM person WHERE username != %s'
        cursor.execute(query, (user))
        otherUsersData = cursor.fetchall()

        cursor.close()
        return render_template('groups.html', error=error, username=user, availableUsers=otherUsersData, group_list=data)
    else:
        ins = 'INSERT INTO friendgroup (groupName, groupCreator, description) VALUES(%s, %s, %s)'
        cursor.execute(ins, (groupName, user, description))
        conn.commit()
        ins = 'INSERT INTO belongto (username, groupName, groupCreator) VALUES(%s, %s, %s)'
        cursor.execute(ins, (user, groupName, user))
        conn.commit()
        memberList = request.form.getlist('members')
        for member in memberList:
            ins = 'INSERT INTO belongto (username, groupName, groupCreator) VALUES(%s, %s, %s)'
            cursor.execute(ins, (member, groupName, user))
            conn.commit()
        return redirect(url_for('groups'))

@app.route('/logout')
def logout():
    session['logged_in'] = False
    session.pop('username')
    return redirect('/')

@app.route('/uploads/<path:filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
