# -*- coding: utf-8 -*-
import os.path
from flask import Flask, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flaskext.uploads import UploadSet, AUDIO, configure_uploads
from sqlalchemy.types import VARCHAR
from sqlalchemy import Column
from subprocess import Popen, PIPE
import argparse


app = Flask(__name__)

current_dir = os.path.realpath('.')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////{}/test.db'.format(current_dir)
app.config['UPLOADED_FILES_DEST'] = '{}/audio/'.format(current_dir)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB file size limit
app.config['SECRET_KEY'] = '\xa1+_\x08o\xe8\xf9Z^=\xb1\xbdT\xc8P\xd5\xabg\xa3\xe6\xd3\x9e)\xc2'

db = SQLAlchemy(app)
db.init_app(app)

audio_files = UploadSet(name='audio', extensions=AUDIO, default_dest=lambda x: x.config['UPLOADED_FILES_DEST'])
configure_uploads(app, audio_files)


class Audio(db.Model):
    """ audio db object """

    __tablename__ = 'audio'

    name = Column('name', VARCHAR(100), primary_key=True, autoincrement=False)
    filename = Column('filename', VARCHAR(100), nullable=False)


@app.route('/')
def index():
    """ list the uploads """
    return (
        u''.join(
            u'<a href=/play/{name}>{name}</a> <a href="/delete/{name}">delete</a><br>'.format(name=a.name)
            for a in Audio.query.all()
        ) +
        '<br><a href="/upload">New Upload</a>'

    )


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """ upload audio file """
    if request.method == 'POST' and 'upload' in request.files:
        filename = audio_files.save(request.files['upload'])
        audio = Audio(name=request.form['name'], filename=filename)
        db.session.add(audio)
        db.session.commit()
        return redirect('/')
    return (
        u'<form method="POST" enctype="multipart/form-data">'
        u'  name: <input name="name" type"string">'
        u'  <input name="upload" type="file">'
        u'  <button type="submit">Upload</button>'
        u'</form>'
    )


@app.route('/delete/<name>')
def delete(name):
    """ delete an uploaded file """
    audio = Audio.query.get_or_404(name)
    db.session.delete(audio)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/play/<name>')
def play(name):
    """ play audio file """
    audio = Audio.query.get_or_404(name)
    command = 'mpg321 -q {dir}/{file}'.format(dir=app.config['UPLOADED_FILES_DEST'], file=audio.filename)
    p = Popen(args=command, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()

    if p.returncode != 0:
        app.logger.exception(err)

    return out
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8080, type=int, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Debug application')
    pargs = parser.parse_args()

    db.create_all()
    app.run(host='0.0.0.0', port=pargs.port, debug=pargs.debug)
