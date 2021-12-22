from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)
import tweepy
import random
import copy
import re
import openpyxl
from flask import Flask, request, Response, abort, render_template,session
from collections import defaultdict
from sqlalchemy import create_engine
from requests_oauthlib import OAuth1Session

import MySQLdb
import datetime
from urllib.parse import urlparse,parse_qsl
consumer_token = "UYrOite8T3N3p1KNKV5Kmkk6A"
consumer_secret = "uYbPLnzJWDcXGHYS8dJt5TQZnfYwfKLKHKjdKJALYjfhsyrH7s"

db_path = "mysql://shuichi47:V3BtyW&U@172.104.91.29:3306/tweepy"
url_sql = urlparse(db_path)
conn = create_engine('mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(host = url_sql.hostname, port=url_sql.port, user = url_sql.username, password= url_sql.password, database = url_sql.path[1:]))

oauth = []
name = []

@app.route("/")
def index():
    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    redirect_url = auth.get_authorization_url()
    return render_template('main.html',redirect_url = redirect_url)



@app.route("/success/", methods=["GET", "POST"])
def success():
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
    oauth.append(oauth_token)
    oauth.append(oauth_token_secret)
    name.append(screen_name)
    return render_template('success.html',screen_name = screen_name)

@app.route("/execute")
def execute():
    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    auth.set_access_token(oauth[-2],oauth[-1])
    api = tweepy.API(auth)
    api.update_status("TEST")
    n = name[-1]
    u = 'https://twitter.com/' + n
    return render_template('execute.html',u=u)





if __name__ == '__main__':
    app.run(debug=True)
