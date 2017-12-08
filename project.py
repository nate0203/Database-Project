from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import datetime

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='pcs',
                       charset='utf8',
                       cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def welcome():
	return render_template('welcome.html')

@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']
	session['error'] = None
	hash_password = hashlib.sha1(password)

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM person WHERE username = %s and password = %s'
	cursor.execute(query, (username, hash_password.hexdigest()))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	cursor.close()
	error = None
	if(data):
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		return redirect(url_for('home'))
	else:
		#returns an error message to the html page
		error = 'Invalid username or password'
		return render_template('login.html', error=error)

@app.route('/register')
def register():
	return render_template('register.html')

@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']
	first_name = request.form['first_name']
	last_name = request.form['last_name']
	hash_password = hashlib.sha1(password)

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, (username))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	if(data):
		#If the previous query returns data, then user exists
		error = "Username already exists"
		return render_template('register.html', error = error)
	else:
		ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
		cursor.execute(ins, (username, hash_password.hexdigest(), first_name, last_name))
		conn.commit()
		cursor.close()
		return render_template('welcome.html')

@app.route('/home')
def home():
	username = session['username']
	error = session['error']
	session['error'] = None
	cursor = conn.cursor();

	#post column gets cut off for long text
	#query = 'SELECT * FROM Content NATURAL LEFT JOIN Share WHERE username = %s ORDER BY timest DESC'
#SELECT * 
#FROM content LEFT JOIN share ON content.id = share.id
#WHERE content.username = 'qwerty' OR 
#(share.username, share.group_name) IN (SELECT member.username_creator, member.group_name
#FROM member RIGHT JOIN share on (member.group_name = share.group_name AND member.username_creator = share.username)
#WHERE member.username = 'qwerty')
	query = 'SELECT * FROM Content LEFT JOIN Share ON content.id = share.id WHERE content.username = %s OR (share.username, share.group_name) IN (SELECT member.username_creator, member.group_name FROM member RIGHT JOIN share on (member.group_name = share.group_name AND member.username_creator = share.username) WHERE member.username = %s) ORDER BY timest DESC'
	cursor.execute(query, (username, username))
	data = cursor.fetchall()

	query = 'SELECT group_name FROM FriendGroup WHERE username = %s'
	cursor.execute(query, username)
	data2 = cursor.fetchall()
	temp = []
	group_list = []

	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		group_list.append(temp[i][0])
		#print group_list[i]

	'''
	temp[:] = []
	query = 'SELECT group_name FROM Member WHERE username = %s'
	cursor.execute(query, username)
	data3 = cursor.fetchall()
	print data3
	member_list = []

	query = 'SELECT username_creator FROM Member WHERE username = %s'
	cursor.execute(query, username)
	data4 = cursor.fetchall()
	print data4
	creator_list = []

	for item in data3:
		temp.append(item.values())
	for i in range(len(temp)):
		member_list.append(temp[i][0])
		print member_list[i]

	temp[:] = []

	for item in data4:
		temp.append(item.values())
	for i in range(len(temp)):
		creator_list.append(temp[i][0])

	for i in range(len(creator_list)):
		member_list[i] = member_list[i] + ' @' + creator_list[i]

	for i in range(len(member_list)):
		group_list.append(member_list[i])
	'''

	query = 'SELECT group_name, username_creator FROM Member WHERE username = %s AND username_creator != %s'
	cursor.execute(query, (username, username))
	data3 = cursor.fetchall()
	print data3

	tmp2 = []
	creator_list = []
	member_list = []
	for item in data3:
		tmp2.append(item.values())

	for i in range(len(tmp2)):
		member_list.append(tmp2[i][1])
	for i in range(len(tmp2)):
		creator_list.append(tmp2[i][0])

	for i in range(len(creator_list)):
		member_list[i] = member_list[i] + ' @' + creator_list[i]
	for i in range(len(member_list)):
		group_list.append(member_list[i])		

	cursor.close()
	if error == None:
		return render_template('home.html', username=username, posts=data, group_list=group_list)
	else:
		return render_template('home.html', username=username, posts=data, error=error, group_list=group_list)

@app.route('/logout')
def logout():
	session.pop('username')
	session.pop('error')
	return redirect('/')

@app.route('/post', methods=['GET','POST'])
def post():
	item = request.form['blog']
	group = request.form['group']
	visibility = request.form['visibility']
	username = session['username']
	path = request.form['file']
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	cursor = conn.cursor()

	creator = ''
	pos = group.rfind('@')
	if pos != -1:
		creator = group[pos+1:]
		group = group[0:pos-1]

	if visibility == "True":
		visibility = True
	else:
		visibility = False
		query = 'SELECT group_name FROM Member WHERE username = %s'
		cursor.execute(query, username)
		data = cursor.fetchall()

		temp = []
		group_list = []

		#for item in data:
		#	temp.append(item.values())
		#for i in range(len(temp)):
		#	group_list.append(temp[i][0])
		#	print group_list[i]

	#false -> private, has a friendgroup associated with it
	#true -> public to all friends

	print group
	print creator
	ins = 'INSERT INTO Content (username, timest, file_path, content_name, public) VALUES (%s, %s, %s, %s, %s)'
	cursor.execute(ins, (username, timestamp, path, item, visibility))
	conn.commit();

	if not visibility:
		query = 'SELECT id FROM Content WHERE timest = %s AND username = %s'
		cursor.execute(query, (timestamp, username))
		content_ID = cursor.fetchall()
		print timestamp
		print username
		print content_ID[0].get('id')
		ins = 'INSERT INTO Share VALUES (%s, %s, %s)'
		if creator == '':
			cursor.execute(ins, (content_ID[0].get('id'), group, username))
		else:
			cursor.execute(ins, (content_ID[0].get('id'), group, creator))
		conn.commit()

	#selects any content that the user has posted, obviously needs changing
	query = 'SELECT content_name FROM Content WHERE username = %s'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()
	return redirect(url_for('home'))

@app.route('/user/userid=<user>', methods=['GET', 'POST'])
def view_user(user):
	cursor = conn.cursor()
	query = 'SELECT count(*) AS num_posts FROM Content WHERE username = %s'
	cursor.execute(query, (user))
	countp = cursor.fetchall()
	nump = countp[0]['num_posts']
	print nump

	query = 'SELECT min(timest) AS first_post FROM Content WHERE username = %s'
	cursor.execute(query, (user))
	f_post = cursor.fetchall()

	query = 'SELECT max(timest) AS last_post FROM Content WHERE username = %s'
	cursor.execute(query, (user))
	l_post = cursor.fetchall()

	query = 'SELECT count(*) AS num_groups FROM FriendGroup WHERE username = %s'
	cursor.execute(query, (user))
	countg = cursor.fetchall()

	query = 'SELECT count(*) AS num_pub FROM Content WHERE username = %s AND public=true'
	cursor.execute(query, (user))
	countpriv = cursor.fetchall()
	num_pub = countpriv[0]['num_pub']
	print num_pub
	percent = (((float)(num_pub))/(nump))*100
	percent = '%.2f'%(percent)

	query = 'SELECT count(DISTINCT username) AS num_f FROM Member WHERE username_creator = %s'
	cursor.execute(query, (user))
	num_friends = cursor.fetchall()

	cursor.close()
	return render_template('user.html', user=user, countp=countp, f_post=f_post, l_post=l_post, countg=countg, percent=percent, num_friends=num_friends)

@app.route('/post/content_id=<id>', methods=['GET', 'POST'])
def view_post(id):
	session['id'] = id
	username = session['username']
	cursor = conn.cursor()
	query = 'SELECT * FROM Content WHERE id = %s'#NATURAL LEFT JOIN Share WHERE username = %s AND id = %s ORDER BY timest DESC'
	cursor.execute(query, id)
	data = cursor.fetchall()
	cursor.close()

	cursor = conn.cursor()
	query = 'SELECT username, comment_text, timest FROM Comment WHERE id = %s ORDER BY timest DESC'
	cursor.execute(query, (id))
	data2 = cursor.fetchall()
	cursor.close()

	return render_template('comments.html', post=data, comments=data2)

@app.route('/comment', methods=['GET', 'POST'])
def comment():
	id = session['id']
	username = session['username']
	text = request.form['Comment']
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	cursor = conn.cursor()
	ins = 'INSERT INTO Comment (id, username, timest, comment_text) VALUES (%s,%s,%s,%s)'
	cursor.execute(ins, (id, username, timestamp, text))
	conn.commit()
	cursor.close()
	return redirect(url_for('view_post', id=id))

@app.route('/friendgroup')
def friendgroups():
	return render_template('friendgroup.html')

@app.route('/add_to_fg', methods=['GET', 'POST'])
def add_to_fg():
	username = session['username']
	cursor = conn.cursor();
	
	query = 'SELECT username FROM Person WHERE username!=%s'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	query = 'SELECT group_name FROM FriendGroup WHERE username = %s'
	cursor.execute(query, (username))
	data2 = cursor.fetchall()
	cursor.close()

	temp = []
	friend_list = []
	group_list = []

	for item in data:
		temp.append(item.values())
	for i in range(len(temp)):
		friend_list.append(temp[i][0])
		print friend_list[i]
	temp[:] = []
	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		group_list.append(temp[i][0])

	return render_template('edit_fg.html', friend_list=friend_list, group_list=group_list)

@app.route('/insert_fg', methods=['GET', 'POST'])
def insert_fg():
	username = session['username']
	group = request.form['group']
	friend = request.form['friend']
	cursor = conn.cursor()

	query = 'SELECT username FROM Member WHERE group_name = %s AND username_creator = %s'
	cursor.execute(query, (group, username))
	data = cursor.fetchall()
	query = 'SELECT group_name FROM FriendGroup WHERE username = %s'
	cursor.execute(query, (username))
	data2 = cursor.fetchall()
	query = 'SELECT username FROM Person WHERE username!=%s'
	cursor.execute(query, (username))
	data3 = cursor.fetchall()

	cursor.close()

	cursor = conn.cursor()

	temp = []
	friend_list = []
	group_list = []
	total_fl = []

	for item in data:
		temp.append(item.values())
	for i in range(len(temp)):
		friend_list.append(temp[i][0])
		print friend_list[i]
	temp[:] = []
	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		group_list.append(temp[i][0])
	temp[:] = []
	for item in data3:
		temp.append(item.values())
	for i in range(len(temp)):
		total_fl.append(temp[i][0])

	if friend in friend_list:
		err = friend + ' is already in ' + group
		session['err'] = err
		cursor.close()
		return render_template('edit_fg.html', friend_list=total_fl, group_list=group_list, error=err)

	ins = 'INSERT INTO Member (username, group_name, username_creator) VALUES (%s,%s,%s)'
	cursor.execute(ins, (friend, group, username))
	conn.commit()
	cursor.close()

	success = friend + ' was added to ' + group + '!'
	session['success'] = success

	return render_template('edit_fg.html', friend_list=total_fl, group_list=group_list, success=success)

@app.route('/create_fg', methods=['GET', 'POST'])
def create_fg():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT username FROM Person WHERE username!=%s'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()

	temp = []
	friend_list = []

	for item in data:
		temp.append(item.values())
	for i in range(len(temp)):
		friend_list.append(temp[i][0])
		print friend_list[i]

	return render_template('create_fg.html', friend_list=friend_list)

@app.route('/new_fg', methods=['GET', 'POST'])
def new_fg():
	username = session['username']
	group = request.form['newgroup']
	friend_1 = request.form['friend1']
	friend_2 = request.form['friend2']
	description = request.form['description']
	cursor = conn.cursor()

	temp = []
	group_list = []
	friend_list = []

	query = 'SELECT group_name FROM FriendGroup WHERE username = %s'
	cursor.execute(query, username)
	data = cursor.fetchall()

	query = 'SELECT username FROM Person WHERE username!=%s'
	cursor.execute(query, (username))
	data2 = cursor.fetchall()

	for item in data:
		temp.append(item.values())
	for i in range(len(temp)):
		group_list.append(temp[i][0])
		print group_list[i]
	temp[:] = []
	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		friend_list.append(temp[i][0])
		print friend_list[i]

	if group in group_list:
		err = 'This FriendGroup already exists.'
		session['err'] = err
		cursor.close()
		return render_template('create_fg.html', friend_list=friend_list, error=err)
	if friend_1 == friend_2:
		err = 'Duplicate friends selected'
		session['err'] = err
		cursor.close()
		return render_template('create_fg.html', friend_list=friend_list, error=err)

	ins = 'INSERT INTO FriendGroup (group_name, username, description) VALUES (%s,%s,%s)'
	cursor.execute(ins, (group, username, description))
	conn.commit()
	ins = 'INSERT INTO Member (username, group_name, username_creator) VALUES (%s,%s,%s)'
	cursor.execute(ins, (friend_1, group, username))
	conn.commit()
	cursor.execute(ins, (friend_2, group, username))
	conn.commit()
	cursor.execute(ins, (username, group, username))
	#cursor.execute(ins, (username, group, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))

@app.route('/remove_friend')
def remove_friend():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT username FROM Person WHERE username!=%s'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()

	temp = []
	friend_list = []

	for item in data:
		temp.append(item.values())
	for i in range(len(temp)):
		friend_list.append(temp[i][0])
		print friend_list[i]

	cursor = conn.cursor()
	query = 'SELECT group_name FROM FriendGroup WHERE username = %s'
	cursor.execute(query, username)
	data2 = cursor.fetchall()
	temp = []
	group_list = []

	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		group_list.append(temp[i][0])
		print group_list[i]

	cursor.close()
	return render_template('remove_friend.html', group_list=group_list, friend_list=friend_list)

@app.route('/remove', methods=['GET', 'POST'])
def remove():
	username = session['username']
	group = request.form['group']
	friend = request.form['friend']
	cursor = conn.cursor()

	query = 'SELECT username FROM Member WHERE group_name = %s AND username_creator = %s'
	cursor.execute(query, (group, username))
	data = cursor.fetchall()
	query = 'SELECT group_name FROM FriendGroup WHERE username = %s'
	cursor.execute(query, (username))
	data2 = cursor.fetchall()
	query = 'SELECT username FROM Person WHERE username!=%s'
	cursor.execute(query, (username))
	data3 = cursor.fetchall()

	cursor.close()

	cursor = conn.cursor()

	temp = []
	friend_list = []
	group_list = []
	total_fl = []

	for item in data:
		temp.append(item.values())
	for i in range(len(temp)):
		friend_list.append(temp[i][0])
		print friend_list[i]
	temp[:] = []
	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		group_list.append(temp[i][0])
	temp[:] = []
	for item in data3:
		temp.append(item.values())
	for i in range(len(temp)):
		total_fl.append(temp[i][0])

	if friend not in friend_list:
		err = friend + ' is not in ' + group
		session['err'] = err
		cursor.close()
		return render_template('remove_friend.html', group_list=group_list, friend_list=total_fl, error=err)
	if len(friend_list) == 2:
		err = group + " only has two members! Can't remove."
		session['err'] = err
		cursor.close()
		return render_template('remove_friend.html', group_list=group_list, friend_list=total_fl, error=err)

	rm = 'DELETE FROM Member WHERE username = %s'
	cursor.execute(rm, (friend))
	conn.commit()
	cursor.close()

	success = friend + ' was removed from ' + group + '!'
	session['success'] = success

	return render_template('remove_friend.html', group_list=group_list, friend_list=total_fl, success=success)

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)