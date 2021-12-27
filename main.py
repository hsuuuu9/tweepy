from flask import Flask, render_template, request, redirect, url_for
import tweepy
import random
import copy
import re
import openpyxl
from flask import Flask, request, Response, abort, render_template,session
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from collections import defaultdict
from sqlalchemy import create_engine
from requests_oauthlib import OAuth1Session
import pandas as pd
import pymysql
import datetime
from urllib.parse import urlparse,parse_qsl

pymysql.install_as_MySQLdb()
db_path = "mysql://shuichi47:V3BtyW&U@172.104.91.29:3306/tweepy"
url_sql = urlparse(db_path)
conn = create_engine('mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(host = url_sql.hostname, port=url_sql.port, user = url_sql.username, password= url_sql.password, database = url_sql.path[1:]))


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, name, password):
        self.id = id
        self.name = name
        self.password = password
users = {}
letter = 'select * from python_mensa'
df = pd.read_sql(letter, conn)
for i in range(len(df)):
    users[i+1] = User(i+1, df['oauth_token'][i], df['oauth_token_secret'][i])

nested_dict = lambda: defaultdict(nested_dict)
user_check = nested_dict()
for i in users.values():
    user_check[i.name]["password"] = i.password
    user_check[i.name]["id"] = i.id

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))



consumer_token = "C59oc8XoWokiS7J8LFKzHLl5q"
consumer_secret = "7aDgLIClOaG88Jp5ppKNr0AKZMfoaf5CiRY9iKsdBA5SENTStr"

oauth = []
name = []
app.config['SECRET_KEY'] = "shuichi"


@app.route("/")
def zero():

    return render_template('zero.html')



@app.route("/twitter")
def twitter():
    try:
        asdf = session['username']
    except:
        session['username'] = 'anonymous'
    myna = session['username']
    login_flag = 'T'
    if myna == 'anonymous':
        login_flag = 'F'
    else:
        letter = 'select * from python_mensa where oauth_token = "'+myna+'" '
        df = pd.read_sql(letter,conn)
        myna = df['screen_name'][0]
    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    redirect_url = auth.get_authorization_url()
    return render_template('main.html',redirect_url = redirect_url,myna = myna,login_flag = login_flag)

@app.route('/twitter/login/', methods=["GET", "POST"])
def login():
    if(request.method == "POST"):
        # ユーザーチェック
        if(request.form["username"] in user_check and request.form["password"] == user_check[request.form["username"]]["password"]):
            # ユーザーが存在した場合はログイン
            login_user(users.get(user_check[request.form["username"]]["id"]))
            session['username'] = request.form["username"]
            return render_template("login_success.html",myname = session['username'])
        else:
            return render_template("login_fail.html")
    else:
        return render_template("login.html")


@app.route('/twitter/logout')
@login_required
def logout():
    logout_user()
    session['username'] = 'anonymous'
    return render_template('logout.html')


@app.route("/twitter/created/")
def created():
    url = request.url
    base_url = 'https://api.twitter.com/'
    access_token_url = base_url + 'oauth/access_token'

    a = url.find('?oauth_token=')
    b = url.find('&oauth_verifier=')

    oauth_token = url[a+13:b]
    oauth_verifier = url[b+16:]

    twitter = OAuth1Session(
            consumer_token,
            consumer_secret,
            oauth_token,
            oauth_verifier,
        )

    response = twitter.post(
            access_token_url,
            params={'oauth_verifier': oauth_verifier}
        )
    access_token = dict(parse_qsl(response.content.decode("utf-8")))
    oauth_token = access_token['oauth_token']
    oauth_token_secret = access_token['oauth_token_secret']
    user_id = access_token['user_id']
    screen_name = access_token['screen_name']

    letter = 'delete from python_mensa where user_id = "'+user_id+'" '
    conn.execute(letter)
    letter = 'insert into python_mensa values("'+oauth_token+'","'+oauth_token_secret+'","'+user_id+'","'+screen_name+'")'
    conn.execute(letter)
    return render_template('created.html',screen_name = screen_name,oauth_token=oauth_token,oauth_token_secret=oauth_token_secret)


@app.route("/twitter/command", methods=["GET"])
def command_get():
    oauth_token = session['username']
    letter = 'select * from python_mensa where oauth_token = "'+oauth_token+'" '
    df = pd.read_sql(letter,conn)
    screen_name = df['screen_name'][0]

    return render_template('command.html',screen_name=screen_name)

@app.route("/twitter/command", methods=["POST"])
def command_post():
    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    oauth_token = session['username']
    letter = 'select * from python_mensa where oauth_token = "'+oauth_token+'" '
    df = pd.read_sql(letter,conn)


    myname = df['screen_name'][0]
    letter_already = 'select * from '+myname
    df_already = pd.read_sql(letter_already,conn)
    already = []
    for i in range(len(df_already)):
        already.append(df_already['user_id'][i])
    oauth_token_secret = df['oauth_token_secret'][0]
    word = request.form.get("word")
    person = request.form.get("person")
    auth.set_access_token(oauth_token,oauth_token_secret)
    api = tweepy.API(auth)
    n = 50
    if not word is None:
        tweets = tweepy.Cursor( api.search, q=word, tweet_mode='extended', result_type="recent", include_entities=True, cursor=-1).items(n)

        users_twitter = []

        for tweet in tweets:

            if tweet.author.friends_count > tweet.author.followers_count:
                tweet_screen_name = tweet.author.screen_name
                users_twitter.append(tweet_screen_name)


    if not person is None:
        users_twitter = []
        followers_ids = tweepy.Cursor(api.followers_ids, id=person, cursor=-1).items(n)
        for follower_id in followers_ids:
            try:
                user = api.get_user(follower_id)
                user_info = user.screen_name
                if user.followers_count < user.friends_count:
                    users_twitter.append(user_info)
            except tweepy.error.TweepError as e:
                print(e.reason)

    users_twitter = list(set(users_twitter))

    for user_twitter in users_twitter:
        if not user_twitter in already:
            conn.execute('insert into '+myname+' values("'+user_twitter+'",0,0,"will follow")')
    return render_template('result.html',users_twitter=users_twitter)

@app.route("/twitter/check")
def check():

    oauth_token = session['username']
    letter = 'select * from python_mensa where oauth_token = "'+oauth_token+'" '
    df = pd.read_sql(letter,conn)
    myname = df['screen_name'][0]
    letter_user = 'select * from '+myname
    df_user = pd.read_sql(letter_user,conn)
    users = []
    for i in range(len(df_user)):
        users.append(df_user['user_id'][i])
    follows = []
    for i in range(len(df_user)):
        follows.append(df_user['follow_unix'][i])
    unfollows = []
    for i in range(len(df_user)):
        unfollows.append(df_user['unfollow_unix'][i])
    status = []
    for i in range(len(df_user)):
        status.append(df_user['status'][i])
    return render_template('check.html',users=users,follows=follows,unfollows=unfollows,status=status,length = len(users))

@app.route("/twitter/argo")
def argo():


    return render_template('argo.html')



if __name__ == '__main__':
    app.run(debug=True)
