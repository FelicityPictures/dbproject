import time

import pymysql.cursors
from flask import Flask, redirect, render_template, request, session, url_for

# Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3308,
                       user='root',
                       password='',
                       db='finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

# Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM person WHERE username = %s AND password = %s'
    cursor.execute(query, (username, password))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    cursor.close()
    if(data):
        # creates a session for the the user
        # session is tied to flask request context
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
    password = request.form['password']

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
        cursor.execute(ins, (username, password, firstName, lastName, email))
        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor()
    # query = """
    #         SELECT * FROM photo
    #         WHERE poster = %s
    #         ORDER BY postingDate DESC
    #         """
    query = """
            SELECT DISTINCT pID, postingDate, filePath, caption, firstName, lastName
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
    return render_template('home.html', username=user, posts=posts, groups=groups, reacts=reacts)

@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor()
    photo = request.form['photo']
    caption = request.form['caption']
    followers = request.form.getlist('followers')
    timeString = time.strftime('%Y-%m-%d %H:%M:%S')
    query = 'INSERT INTO photo (postingDate, filePath, allFollowers, caption, poster) VALUES(%s, %s, %s, %s, %s)'
    if(len(followers) > 0):
        if(followers[0] == "all"):
            # all followers
            cursor.execute(query, (timeString, photo, 1, caption, username))
            conn.commit()
        else:
            cursor.execute(query, (timeString, photo, 0, caption, username))
            conn.commit()
            query = 'SELECT LAST_INSERT_ID()'
            cursor.execute(query)
            pID = cursor.fetchall()
            pID = pID[0].get('LAST_INSERT_ID()')
            print(pID)
            query = 'INSERT INTO sharedwith (pID, groupName, groupCreator) VALUES(%s, %s, %s)'
            for group in followers:
                info = group.split(';')
                cursor.execute(query, (pID, info[0], info[1]))
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
    cursor.execute(query, (username, photo))
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
    # check that user is logged in
    # username = session['username']
    # should throw exception if username not found
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
    #grabs information from the forms
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
    follower = request.form['follower']

    cursor = conn.cursor();

    query = 'DELETE FROM follow WHERE followee = %s AND follower = %s'
    cursor.execute(query, (user, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('connections'))

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor()
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)


@app.route('/groups')
def groups():
    # check that user is logged in
    #username = session['username']
    # should throw exception if username not found

    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM belongto WHERE username = %s'
    cursor.execute(query, (user))
    data = cursor.fetchall()

    query = 'SELECT * FROM person WHERE username != %s'
    cursor.execute(query, (user))
    otherUsersData = cursor.fetchall()

    cursor.close()
    return render_template('groups.html', username=user, availableUsers=otherUsersData, group_list=data)

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

        query = 'SELECT * FROM belongto WHERE username = %s'
        cursor.execute(query, (user))
        data = cursor.fetchall()
        cursor.close()
        return redirect(url_for('connections'))


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
