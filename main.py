
from flask import Flask, render_template, request,session,redirect
from flask_sqlalchemy import SQLAlchemy   # ha module aplyla database la connect karnysathi madat karto
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
from datetime import datetime
import os
import math


with open('config.json', 'r') as c:    #file read karun atomatic close hote
    params = json.load(c)["params"]     # syntex for acsess the file that is json file

local_server = True    #server navacha variable baanvala
app = Flask(__name__)
app.secret_key = 'super-secret-key'

# app.config['UPLOAD_FOLDER']=params['upload_location']
""" gmail la connect karnysathis tych default configure ahe jeve apan hya code la chalvato teva aplyla 1k error  yeto
that is called as smtp error manje google apyla permission nahi det"""
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',   #gmail; cha defalt paramerter ahe
    MAIL_USE_SSL = True,  # kya ham ssl use karyacha ahe ka
    MAIL_USERNAME = params['gmail-user'],  # ham parms se sername access karge
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)    
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    # [0:params['no_of_posts']]  # this is because of our post no is depends upon me manje kiti post have te
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    #pagination logic

    page=request.args.get('page')
    if (not str(page).isnumeric()):
        page=1
    page=int(page)

    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]

    if (page==1):
        prev="#"
        next="/?page="+ str(page+1)

    elif (page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)





    return render_template('index.html', params=params,posts=posts,prev=prev,next=next)


@app.route("/post/<string:post_slug>",methods=['GET'])  # hycha pude 1k string jii slug asel ti write karnychi technich hi ahe
def post_route(post_slug):   #jo ham variable dete he oh hame fuunction ke ander bhi post karna hota he niyamch ahe
    post=Posts.query.filter_by(slug=post_slug).first()    #posts ko quary karo useke bad filter karo slug se
    return render_template('post.html', params=params ,post=post)  #post=post matlab ham sublime se acsees kr sakte he

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/dashboard",methods=['GET', 'POST'])
def dashboard():
    if 'user' in session and session['user']==params['admin_user']: #jo user he oh session me he aur oh admin he to
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts )

    if request.method=='POST':
       ''' Rdirect to panal'''
       username=request.form.get('uname')     #post request se paramter lekar ayega
       userpass=request.form.get('pass')
       if username == params['admin_user'] and userpass == params['admin_password']:
          '''set the section variable'''
          session['user'] = username
          posts=Posts.query.all()  #sare post aa jayege
          return render_template('dashboard.html', params=params,posts=posts )
       else:
           print('password was wrong')
           return redirect('/dashboard')


    else:
     return render_template('login.html', params=params)

@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user']==params['admin_user']):
        if request.method == 'POST':
            title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno=='0':
                post=Posts(title=title,slug=slug,content=content,tagline=tline,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                  post=Posts.query.filter_by(sno=sno).first()
                  post.title=title
                  post.slug =slug
                  post.content= content
                  post.tagline=tline       #update karne keliye
                  post.img_file=img_file
                  post.date=date
                  db.session.commit()
                  return redirect('/edit/' + sno)
        
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,sno=sno,post=post)





@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f=request.files['file_upload']
            f.save(os.path.join('D:\flask.txt\static',secure_filename(f.filename) ))
        return "Uploaded successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients = [params['gmail-user']],
                          body = message + "\nphone number is :- " + phone
                          )
    return render_template('contact.html', params=params)

if __name__ == '__main__':
 app.run(debug=True)




# //tline = request.form.get('tline')
# //            slug = request.form.get('slug')
# //            content = request.form.get('content')
# //            img_file = request.form.get('img_file')
# //            date = datetime.now()
# //
# //            if sno=='0':
# //                post=Posts(title=box_title,slug=slug,content=content,tagline=tline,img_file=img_file,date=date)
# //                db.session.add(post)#   we can add the post
# //                db.session.commit()
# //            else:
# //                post=Posts.query.filter_by(sno=sno).first()
# //                post.title=box_title
# //                post.slug =slug
# //                post.content= content
# //                post.tagline=tline       #update karne keliye
# //                post.img_file=img_file
# //                post.date=date
# //                db.session.commit()
# //
# //                return redirect('/edit/'+ sno)
# //        post = Posts.query.filter_by(sno=sno).first()
# //        return render_template('edit.html',params=params,post=post)



