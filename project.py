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
	if 'error' in session:
		error = session['error']
		session['error'] = None
	else:
		error = None

	if error == None:
		return render_template('login.html')
	else:
		return render_template('login.html', error=error)

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']
	print "CCCCCC"
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
		session['error'] = error
		return redirect(url_for('login'))
		#return render_template('login.html', error=error)

@app.route('/register')
def register():
	if 'error' in session:
		error = session['error']
		session['error'] = None
	else:
		error = None
	if error == None:
		return render_template('register.html')
	else:
		return render_template('register.html', error=error)

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
		session['error'] = error
		return redirect(url_for('register'))
	else:
		ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
		cursor.execute(ins, (username, hash_password.hexdigest(), first_name, last_name))
		conn.commit()
		cursor.close()
		return redirect(url_for('welcome'))

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
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, username)
	info = cursor.fetchall()

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

	print info
	cursor.close()
	if error == None:
		return render_template('home.html', info=info, posts=data, group_list=group_list)
	else:
		return render_template('home.html', info=info, posts=data, error=error, group_list=group_list)

@app.route('/logout')
def logout():
	session.pop('username')
	session.pop('error')
	return redirect('/')

@app.route('/post', methods=['GET','POST'])
def post():
	item = request.form['blog']
	visibility = request.form['visibility']
	username = session['username']
	path = request.form['file']
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	cursor = conn.cursor()

	
	if visibility == "True":
		visibility = True
	else:
		visibility = False
		query = 'SELECT group_name FROM Member WHERE username = %s'
		cursor.execute(query, username)
		data = cursor.fetchall()

		temp = []
		group_list = []

	if not visibility:
		try:
			group = request.form['group']
		except:
			return redirect(url_for('home'))
		creator = ''
		pos = group.rfind('@')
		if pos != -1:
			creator = group[pos+1:]
			group = group[0:pos-1]

		#for item in data:
		#	temp.append(item.values())
		#for i in range(len(temp)):
		#	group_list.append(temp[i][0])
		#	print group_list[i]

	#false -> private, has a friendgroup associated with it
	#true -> public to all friends

	#print group
	#print creator
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
	try:
		percent = (((float)(num_pub))/(nump))*100
	except:
		percent = 0
	percent = '%.2f'%(percent)

	query = 'SELECT count(DISTINCT username) AS num_f FROM Member WHERE username_creator = %s AND username != %s'
	cursor.execute(query, (user, user))
	num_friends = cursor.fetchall()

	query = 'SELECT * FROM content WHERE username = %s AND public = %s ORDER BY timest DESC'
	cursor.execute(query, (user, True))
	public_post = cursor.fetchall()

	cursor.close()
	return render_template('user.html', user=user, countp=countp, f_post=f_post, l_post=l_post, countg=countg, percent=percent, num_friends=num_friends, public=public_post)

@app.route('/post/content_id=<id>', methods=['GET', 'POST'])
def view_post(id):
	session['id'] = id
	username = session['username']
	error = session['error']
	session['error'] = None

	cursor = conn.cursor()
	query = 'SELECT * FROM Content LEFT JOIN Share ON content.id = share.id WHERE content.id = %s'#NATURAL LEFT JOIN Share WHERE username = %s AND id = %s ORDER BY timest DESC'
	cursor.execute(query, id)
	data = cursor.fetchall()
	#print data[0]['public']
	cursor.close()

	cursor = conn.cursor()
	query = 'SELECT * FROM Tag JOIN Person ON username_taggee = person.username WHERE id = %s AND status = %s'
	cursor.execute(query, (id, True))
	tag = cursor.fetchall()
	print tag
	cursor.close()

	cursor = conn.cursor()
	query = 'SELECT username, comment_text, timest FROM Comment WHERE id = %s ORDER BY timest DESC'
	cursor.execute(query, (id))
	data2 = cursor.fetchall()
	
	query = 'SELECT * FROM person'
	cursor.execute(query)
	data3 = cursor.fetchall()
	cursor.close()
	if error == None:
		return render_template('comments.html', people=tag, post=data, comments=data2, person=data3)
	else:
		return render_template('comments.html', people=tag, post=data, comments=data2, person=data3, error=error)

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

@app.route('/tag', methods=['GET', 'POST'])
def tagging():
	id = session['id']
	tagger = session['username']
	tagged = request.form['friend']
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	status = False

	cursor = conn.cursor()
	query = 'SELECT * FROM content WHERE id = %s'
	cursor.execute(query, id)
	content = cursor.fetchall()

	if content[0]['public'] == 0:
		query = 'SELECT group_name FROM share WHERE id = %s'
		cursor.execute(query, id)
		data = cursor.fetchall()

		query = 'SELECT username FROM member WHERE group_name = %s'
		cursor.execute(query, data[0]['group_name'])
		data = cursor.fetchall()

		member_list = []
		for i in range(len(data)):
			member_list.append(data[i]['username'])

		if tagged not in member_list:
			session['error'] = tagged + " is not part of this friend group."
			return redirect(url_for('view_post', id=id))

	query = 'SELECT * FROM Tag WHERE id = %s AND username_taggee = %s'
	cursor.execute(query, (id, tagged))
	check = cursor.fetchall()

	if check:
		if check[0]['status'] == True:
			session['error'] = tagged + " is already tagged."
			return redirect(url_for('view_post', id=id))
		else:
			cursor.close()
			return redirect(url_for('view_post', id=id))

	if tagger == tagged:
		status = True

	ins = 'INSERT INTO Tag VALUES (%s, %s, %s, %s, %s)'
	cursor.execute(ins, (id, tagger, tagged, timestamp, status))
	data2 = cursor.fetchall()
	conn.commit()
	cursor.close()

	return redirect(url_for('view_post', id=id))

@app.route('/tag-log', methods=['GET', 'POST'])
def tag_log():
	username = session['username']

	status = False
	cursor = conn.cursor()
	query = 'SELECT * FROM tag JOIN content ON tag.id = content.id WHERE username_taggee = %s AND status = %s ORDER BY tag.timest DESC'
	cursor.execute(query, (username, status))
	data = cursor.fetchall()

	query = 'SELECT * FROM tag JOIN content ON tag.id = content.id WHERE username_taggee = %s AND status = %s ORDER BY content.timest DESC'
	cursor.execute(query, (username, not status))
	data2 = cursor.fetchall()
	cursor.close()

	return render_template('tag-log.html', tagging=data, approved=data2)

@app.route('/edit_tag', methods=['GET', 'POST'])
def edit_tag():
	try:
		id = request.form['post_id']
	except:
		return redirect(url_for('tag_log'))
	username = session['username']
	choice = request.form['action']
	cursor = conn.cursor()


	if choice == 'Accept':
		print choice
		add = True
	if choice == 'Deny':
		add = False

	if add:
		query = 'UPDATE tag SET status = %s WHERE id = %s AND username_taggee = %s'
		cursor.execute(query, (True, id, username))
		conn.commit()
		cursor.close()
	else:
		query = 'DELETE FROM tag WHERE id = %s AND username_taggee = %s'
		cursor.execute(query, (id, username))
		conn.commit()
		cursor.close()

	return redirect(url_for('tag_log'))


@app.route('/friendgroup')
def friendgroups():
	username = session['username']
	cursor = conn.cursor()
	query = 'SELECT group_name, username_creator FROM member WHERE username = %s'
	cursor.execute(query, username)
	data = cursor.fetchall()

	query = 'SELECT * FROM member'
	cursor.execute(query)
	data2 = cursor.fetchall()
	cursor.close()

	return render_template('friendgroup.html', group_list=data, member_list=data2)

@app.route('/add_to_fg', methods=['GET', 'POST'])
def add_to_fg():
	username = session['username']
	error = session['error']
	session['error'] = None
	if 'success' in session:
		success = session['success']
		session['success'] = None
	else:
		success = None
	cursor = conn.cursor()
	
	query = 'SELECT first_name, last_name, username FROM Person WHERE username!=%s'
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
		friend_list.append(temp[i][1] + ' ' + temp[i][2] + ' (' + temp[i][0] + ')')
		print friend_list[i]
	temp[:] = []
	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		group_list.append(temp[i][0])

	if error == None and success == None:
		return render_template('edit_fg.html', friend_list=friend_list, group_list=group_list)
	elif error != None and success == None:
		return render_template('edit_fg.html', friend_list=friend_list, group_list=group_list, error=error)
	elif error == None and success != None:
		return render_template('edit_fg.html', friend_list=friend_list, group_list=group_list, success=success)
	else:
		return render_template('edit_fg.html', friend_list=friend_list, group_list=group_list, error=error, success=success)


@app.route('/insert_fg', methods=['GET', 'POST'])
def insert_fg():
	username = session['username']
	try:
		group = request.form['group']
	except:
		session['error'] = 'You Do Not Own Any Friend Groups'
		return redirect(url_for('add_to_fg'))
	friend = request.form['friend']
	index = friend.rfind('(')
	friend = friend[index+1:-1]

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
		session['error'] = err
		cursor.close()
		return redirect(url_for('add_to_fg'))
		#return render_template('edit_fg.html', friend_list=total_fl, group_list=group_list, error=err)

	ins = 'INSERT INTO Member (username, group_name, username_creator) VALUES (%s,%s,%s)'
	cursor.execute(ins, (friend, group, username))
	conn.commit()
	cursor.close()

	success = friend + ' was added to ' + group + '!'
	session['success'] = success

	return redirect(url_for('add_to_fg'))
	#return render_template('edit_fg.html', friend_list=total_fl, group_list=group_list, success=success)

@app.route('/create_fg', methods=['GET', 'POST'])
def create_fg():
	username = session['username']
	error = session['error']
	session['error'] = None
	cursor = conn.cursor();
	query = 'SELECT first_name, last_name, username FROM Person WHERE username!=%s'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()

	temp = []
	first_name_list = []
	last_name_list = []
	username_list = []
	friend_list = []

	for item in data:
		temp.append(item.values())
	for i in range(len(temp)):
		username_list.append(temp[i][0])
		#print username_list[i]
	for i in range(len(temp)):
		first_name_list.append(temp[i][1])
		#print first_name_list[i]
	for i in range(len(temp)):
		last_name_list.append(temp[i][2])
		#print last_name_list

	for i in range(len(temp)):
		friend_list.append(first_name_list[i] + ' ' + last_name_list[i] + ' (' + username_list[i] + ')')
		#print friend_list[i]

	if error == None:
		return render_template('create_fg.html', friend_list=friend_list)
	else:
		return render_template('create_fg.html', friend_list=friend_list, error=error)

@app.route('/new_fg', methods=['GET', 'POST'])
def new_fg():
	username = session['username']
	group = request.form['newgroup']
	friend_1 = request.form['friend1']
	#print friend_1
	#friend_2 = request.form['friend2']
	#print friend_2
	description = request.form['description']
	cursor = conn.cursor()

	index = friend_1.rfind('(')
	friend_1_username = friend_1[index+1:-1]

	#index = friend_2.rfind('(')
	#friend_2_username = friend_2[index+1:-1]

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
		#print group_list[i]
	temp[:] = []
	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		friend_list.append(temp[i][0])
		#print friend_list[i]

	if group in group_list:
		err = 'This FriendGroup already exists.'
		session['error'] = err
		cursor.close()
		return redirect(url_for('create_fg'))
		#return render_template('create_fg.html', friend_list=friend_list, error=err)
	#if friend_1 == friend_2:
	#	err = 'Duplicate friends selected'
	#	session['error'] = err
	#	cursor.close()
	#	return redirect(url_for('create_fg'))
		#return render_template('create_fg.html', friend_list=friend_list, error=err)

	ins = 'INSERT INTO FriendGroup (group_name, username, description) VALUES (%s,%s,%s)'
	cursor.execute(ins, (group, username, description))
	conn.commit()
	ins = 'INSERT INTO Member (username, group_name, username_creator) VALUES (%s,%s,%s)'
	cursor.execute(ins, (friend_1_username, group, username))
	conn.commit()
	#cursor.execute(ins, (friend_2_username, group, username))
	#conn.commit()
	cursor.execute(ins, (username, group, username))
	#cursor.execute(ins, (username, group, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))

@app.route('/remove_friend')
def remove_friend():
	username = session['username']
	try:
		success = session['success']
		session['success'] = None
	except:
		success = None
	try:
		error = session['error']
		session['error'] = None
	except:
		error = None

	cursor = conn.cursor();
	query = 'SELECT first_name, last_name, username FROM Person WHERE username!=%s'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()

	temp = []
	friend_list = []

	for item in data:
		temp.append(item.values())
	for i in range(len(temp)):
		friend_list.append(temp[i][1] + ' ' + temp[i][2] + ' (' + temp[i][0] + ')')
		#print friend_list[i]

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

	if error == None and success == None:
		return render_template('remove_friend.html', group_list=group_list, friend_list=friend_list)
	elif error != None and success == None:
		return render_template('remove_friend.html', group_list=group_list, friend_list=friend_list, error=error)
	elif error == None and success != None:
		return render_template('remove_friend.html', group_list=group_list, friend_list=friend_list, success=success)
	else:
		return render_template('remove_friend.html', group_list=group_list, friend_list=friend_list, error=error, success=success)


@app.route('/remove', methods=['GET', 'POST'])
def remove():
	username = session['username']
	try:
		group = request.form['group']
	except:
		session['error'] = 'You do not own any Friend Groups'
		return redirect(url_for('remove_friend'))
	friend = request.form['friend']
	index = friend.rfind('(')
	friend = friend[index+1:-1]
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
		session['error'] = err
		cursor.close()
		return redirect(url_for('remove_friend'))
		#return render_template('remove_friend.html', group_list=group_list, friend_list=total_fl, error=err)
	if len(friend_list) == 2:
		err = group + " only has two members! Can't remove."
		session['error'] = err
		cursor.close()
		return redirect(url_for('remove_friend'))
		#return render_template('remove_friend.html', group_list=group_list, friend_list=total_fl, error=err)

	rm = 'DELETE FROM Member WHERE username = %s'
	cursor.execute(rm, (friend))
	conn.commit()
	cursor.close()

	success = friend + ' was removed from ' + group + '!'
	session['success'] = success

	return redirect(url_for('remove_friend'))
	#return render_template('remove_friend.html', group_list=group_list, friend_list=total_fl, success=success)

@app.route('/edit_profile', methods=['GET','POST'])
def edit_profile():
	error = session['error']
	session['error'] = None

	cursor = conn.cursor()
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, session['username'])
	info = cursor.fetchall()
	cursor.close()

	if error == None:
		return render_template('edit-profile.html', name=info)
	else:
		return render_template('edit-profile.html', name=info, error=error)

@app.route('/change_name', methods=['GET', 'POST'])
def change_name():
	first_name = request.form['first_name']
	last_name = request.form['last_name']

	cursor = conn.cursor()
	query = 'UPDATE person SET first_name = %s, last_name = %s WHERE username = %s'
	cursor.execute(query, (first_name, last_name, session['username']))
	conn.commit()
	cursor.close()

	return redirect(url_for('edit_profile'))

@app.route('/change_pass', methods=['GET', 'POST'])
def change_pass():
	old_pass = request.form['old']
	old_pass = hashlib.sha1(old_pass).hexdigest()
	new_pass = request.form['new']
	new_pass = hashlib.sha1(new_pass).hexdigest()

	cursor = conn.cursor()
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, session['username'])
	info = cursor.fetchall()

	if info[0]['password'] != old_pass:
		session['error'] = "Cannot complete. Password was incorrect."
		return redirect(url_for('edit_profile'))

	if old_pass == new_pass:
		return redirect(url_for('edit_profile'))

	query = 'UPDATE person SET password = %s WHERE username = %s'
	cursor.execute(query, (new_pass, session['username']))
	conn.commit()
	cursor.close()

	return redirect(url_for('edit_profile'))

@app.route('/user', methods=['GET', 'POST'])
def user_list():
	cursor = conn.cursor()
	query = 'SELECT * FROM person'
	cursor.execute(query)
	data = cursor.fetchall()
	cursor.close()
	return render_template('user_list.html', user_list=data)


app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)