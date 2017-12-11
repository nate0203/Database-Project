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

# welcome page for PriCoSha
@app.route('/')
def welcome():
	return render_template('welcome.html')

# login page for PriCoSha
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

# check if user information for login is valid
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	username = request.form['username']
	password = request.form['password']
	session['error'] = None
	hash_password = hashlib.md5(password)

	# query for correct username and password
	cursor = conn.cursor()
	query = 'SELECT * FROM person WHERE username = %s and password = %s'
	cursor.execute(query, (username, hash_password.hexdigest()))
	data = cursor.fetchone()
	cursor.close()
	error = None
	if(data):
		# valid login
		session['username'] = data['username']
		return redirect(url_for('home'))
	else:
		# invalid login
		error = 'Invalid username or password'
		session['error'] = error
		return redirect(url_for('login'))

# registration for account
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

# check if registration information is allowed
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	username = request.form['username']
	password = request.form['password']
	first_name = request.form['first_name']
	last_name = request.form['last_name']
	hash_password = hashlib.sha1(password)

	# query for people with same username
	cursor = conn.cursor()
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, (username))
	data = cursor.fetchone()
	error = None
	if(data):
		# invalid username
		error = "Username already exists"
		session['error'] = error
		return redirect(url_for('register'))
	else:
		# valid username, account created
		ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
		cursor.execute(ins, (username, hash_password.hexdigest(), first_name, last_name))
		conn.commit()
		cursor.close()
		return redirect(url_for('welcome'))

# home page after logging in
@app.route('/home')
def home():
	username = session['username']
	error = session['error']
	session['error'] = None
	cursor = conn.cursor();

	# query for information on current user
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, username)
	info = cursor.fetchall()

	# query for content relevant to current user (posts in group and personal public posts)
	query = 'SELECT * FROM Content LEFT JOIN Share ON content.id = share.id WHERE content.username = %s OR (share.username, share.group_name) IN (SELECT member.username_creator, member.group_name FROM member RIGHT JOIN share on (member.group_name = share.group_name AND member.username_creator = share.username) WHERE member.username = %s or member.username_creator = %s) ORDER BY timest DESC'
	cursor.execute(query, (username, username, username))
	data = cursor.fetchall()

	# query for friend groups the current user owns
	query = 'SELECT group_name FROM FriendGroup WHERE username = %s'
	cursor.execute(query, username)
	data2 = cursor.fetchall()
	temp = []
	group_list = []

	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		group_list.append(temp[i][0])

	# query for friend groups the current user is a member of
	query = 'SELECT group_name, username_creator FROM Member WHERE username = %s AND username_creator != %s'
	cursor.execute(query, (username, username))
	data3 = cursor.fetchall()

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
		return render_template('home.html', info=info, posts=data, group_list=group_list)
	else:
		return render_template('home.html', info=info, posts=data, error=error, group_list=group_list)

# log out 
@app.route('/logout')
def logout():
	session.pop('username')
	session.pop('error')
	return redirect('/')

# posting attempt
@app.route('/post', methods=['GET','POST'])
def post():
	item = request.form['blog']
	visibility = request.form['visibility']
	username = session['username']
	path = request.form['file']
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	cursor = conn.cursor()

	# public or private post
	if visibility == "True":
		visibility = True
	else:
		visibility = False
		query = 'SELECT group_name FROM Member WHERE username = %s'
		cursor.execute(query, username)
		data = cursor.fetchall()

		temp = []
		group_list = []

	# private post
	if not visibility:
		# get official group name
		try:
			group = request.form['group']
		except:
			return redirect(url_for('home'))
		creator = ''
		pos = group.rfind('@')
		if pos != -1:
			creator = group[pos+1:]
			group = group[0:pos-1]

	# query to insert content item
	ins = 'INSERT INTO Content (username, timest, file_path, content_name, public) VALUES (%s, %s, %s, %s, %s)'
	cursor.execute(ins, (username, timestamp, path, item, visibility))
	conn.commit();

	# query to insert information about content information shared with group
	if not visibility:
		query = 'SELECT id FROM Content WHERE timest = %s AND username = %s'
		cursor.execute(query, (timestamp, username))
		content_ID = cursor.fetchall()
		ins = 'INSERT INTO Share VALUES (%s, %s, %s)'
		if creator == '':
			cursor.execute(ins, (content_ID[0].get('id'), group, username))
		else:
			cursor.execute(ins, (content_ID[0].get('id'), group, creator))
		conn.commit()

	query = 'SELECT content_name FROM Content WHERE username = %s'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()
	return redirect(url_for('home'))

# query to look at user's information
# information includes number of friends,
# number of friend groups, % of public posts and more
@app.route('/user/userid=<user>', methods=['GET', 'POST'])
def view_user(user):
	cursor = conn.cursor()
	query = 'SELECT count(*) AS num_posts FROM Content WHERE username = %s'
	cursor.execute(query, (user))
	countp = cursor.fetchall()
	nump = countp[0]['num_posts']

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

	if user == session['username']:
		return render_template('user.html', user=user, countp=countp, f_post=f_post, l_post=l_post, countg=countg, percent=percent, num_friends=num_friends, public=public_post)
	else:
		return render_template('user.html', user=user, countp=countp, f_post=f_post, l_post=l_post, countg=countg, percent=percent, num_friends=num_friends, public=public_post, other=True)

# view content item
@app.route('/post/content_id=<id>', methods=['GET', 'POST'])
def view_post(id):
	session['id'] = id
	username = session['username']
	error = session['error']
	session['error'] = None

	cursor = conn.cursor()
	query = 'SELECT * FROM Content LEFT JOIN Share ON content.id = share.id WHERE content.id = %s'
	cursor.execute(query, id)
	data = cursor.fetchall()
	print data[0]['Share.username']
	print session['username']
	cursor.close()

	# check if content item can be viewed by current user (post is part of friend group user is in or public)
	if data[0]['public'] == False and data[0]['Share.username'] != username:
		cursor = conn.cursor()
		query = 'SELECT * FROM member WHERE username = %s and username_creator = %s and group_name = %s'
		cursor.execute(query, (username, data[0]['Share.username'], data[0]['group_name']))
		check = cursor.fetchall()
		print check
		if not check:
			return redirect(url_for('home'))

	cursor = conn.cursor()
	query = 'SELECT * FROM Tag JOIN Person ON username_taggee = person.username WHERE id = %s AND status = %s'
	cursor.execute(query, (id, True))
	tag = cursor.fetchall()
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

# add comment to post
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

# tag person by username
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
		query = 'SELECT group_name, username FROM share WHERE id = %s'
		cursor.execute(query, id)
		data_g = cursor.fetchall()

		query = 'SELECT username FROM member WHERE group_name = %s and username_creator = %s'
		cursor.execute(query, (data_g[0]['group_name'], data_g[0]['username']))
		data = cursor.fetchall()
		print data

		member_list = []
		for i in range(len(data)):
			member_list.append(data[i]['username'])

		#query = 'SELECT username FROM friendgroup WHERE group_name = %s'
		#cursor.execute(query, data_g[0]['group_name'])
		#data = cursor.fetchall()
		#print data

		#if data:
		member_list.append(data_g[0]['username'])

		# check if person is part of friend group if the post is private
		if tagged not in member_list:
			session['error'] = tagged + " is not part of this friend group."
			return redirect(url_for('view_post', id=id))

	query = 'SELECT * FROM Tag WHERE id = %s AND username_taggee = %s'
	cursor.execute(query, (id, tagged))
	check = cursor.fetchall()

	# check if person is tagged yet
	if check:
		if check[0]['status'] == True:
			session['error'] = tagged + " is already tagged."
			return redirect(url_for('view_post', id=id))
		else:
			cursor.close()
			return redirect(url_for('view_post', id=id))

	# self tagging
	if tagger == tagged:
		status = True

	ins = 'INSERT INTO Tag VALUES (%s, %s, %s, %s, %s)'
	cursor.execute(ins, (id, tagger, tagged, timestamp, status))
	data2 = cursor.fetchall()
	conn.commit()
	cursor.close()

	return redirect(url_for('view_post', id=id))

# log for all tags
# see current or pending tags and allows pending tags to be accepted or denied
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

# accept or deny tag chosen in tag log
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

# view information about current friend groups and options on own friend groups
@app.route('/friendgroup')
def friendgroups():
	username = session['username']
	cursor = conn.cursor()
	query = 'SELECT DISTINCT group_name, username_creator FROM member WHERE username = %s or username_creator=%s'
	cursor.execute(query, (username, username))
	data = cursor.fetchall()

	query = 'SELECT * FROM member JOIN person on member.username = person.username'
	cursor.execute(query)
	data2 = cursor.fetchall()

	query = 'SELECT * FROM friendgroup JOIN person on friendgroup.username = person.username'
	cursor.execute(query)
	owner = cursor.fetchall()

	cursor.close()

	return render_template('friendgroup.html', group_list=data, member_list=data2, owner=owner)

# page to add a person to a friend group you own
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

# add a person to a friend group that exists and that you own
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

	ins = 'INSERT INTO Member (username, group_name, username_creator) VALUES (%s,%s,%s)'
	cursor.execute(ins, (friend, group, username))
	conn.commit()
	cursor.close()

	success = friend + ' was added to ' + group + '!'
	session['success'] = success

	return redirect(url_for('add_to_fg'))

# page to create a friend group that you will own
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
	for i in range(len(temp)):
		first_name_list.append(temp[i][1])
	for i in range(len(temp)):
		last_name_list.append(temp[i][2])

	for i in range(len(temp)):
		friend_list.append(first_name_list[i] + ' ' + last_name_list[i] + ' (' + username_list[i] + ')')

	if error == None:
		return render_template('create_fg.html', friend_list=friend_list)
	else:
		return render_template('create_fg.html', friend_list=friend_list, error=error)

# create the actual friend group
@app.route('/new_fg', methods=['GET', 'POST'])
def new_fg():
	username = session['username']
	group = request.form['newgroup']
	friend_1 = request.form['friend1']
	description = request.form['description']
	cursor = conn.cursor()

	index = friend_1.rfind('(')
	friend_1_username = friend_1[index+1:-1]

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
	temp[:] = []
	for item in data2:
		temp.append(item.values())
	for i in range(len(temp)):
		friend_list.append(temp[i][0])

	if group in group_list:
		err = 'This FriendGroup already exists.'
		session['error'] = err
		cursor.close()
		return redirect(url_for('create_fg'))

	ins = 'INSERT INTO FriendGroup (group_name, username, description) VALUES (%s,%s,%s)'
	cursor.execute(ins, (group, username, description))
	conn.commit()
	ins = 'INSERT INTO Member (username, group_name, username_creator) VALUES (%s,%s,%s)'
	cursor.execute(ins, (friend_1_username, group, username))
	conn.commit()
	#cursor.execute(ins, (username, group, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))

# page to remove a friend from a friend group you own
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

	cursor.close()

	if error == None and success == None:
		return render_template('remove_friend.html', group_list=group_list, friend_list=friend_list)
	elif error != None and success == None:
		return render_template('remove_friend.html', group_list=group_list, friend_list=friend_list, error=error)
	elif error == None and success != None:
		return render_template('remove_friend.html', group_list=group_list, friend_list=friend_list, success=success)
	else:
		return render_template('remove_friend.html', group_list=group_list, friend_list=friend_list, error=error, success=success)

# remove the chosen person from a friend group
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
	if len(friend_list) == 1:
		err = group + " only has two members! Can't remove."
		session['error'] = err
		cursor.close()
		return redirect(url_for('remove_friend'))

	rm = 'DELETE FROM Member WHERE username = %s and friendgroup = %s'
	cursor.execute(rm, (friend, group))
	conn.commit()
	cursor.close()

	success = friend + ' was removed from ' + group + '!'
	session['success'] = success

	return redirect(url_for('remove_friend'))

# view profile information that can be changed (password and first/last name)
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

# set first and last name to new entry
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

# set password to something else
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

# view list of users, allows to view profiles/get correct usernames for tagging or friending
@app.route('/user', methods=['GET', 'POST'])
def user_list():
	cursor = conn.cursor()
	query = 'SELECT * FROM person'
	cursor.execute(query)
	data = cursor.fetchall()
	cursor.close()
	return render_template('user_list.html', user_list=data)

app.secret_key = 'some super secret key'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)