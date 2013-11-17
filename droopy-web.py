#!/bin/env python
import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from werkzeug import secure_filename
from PIL import Image
import json
import random

IMG_FOLDER = './img/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.debug = True
app.config['IMG_FOLDER'] = IMG_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            #filename = secure_filename(file.filename)
            filename = 'source.png'
            file.save(os.path.join(app.config['IMG_FOLDER'], filename))
            return redirect(url_for('get_file', filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.route('/grayscale')
def to_grayscale():
    try:
        image = Image.open(os.path.join(app.config['IMG_FOLDER'],'source.png'))
    except:
        return redirect(url_for('upload_file'))
    image = image.convert('L',dither=Image.NONE)
    filename = 'grayscale.png'
    image.save(os.path.join(app.config['IMG_FOLDER'],filename))
    return redirect(url_for('get_file', filename=filename))

@app.route('/analog')
def to_analog():
    pass

@app.route('/vector')
def to_vector():
    filename = 'vector.png'
    try:
        grayscale_image = Image.open(os.path.join(app.config['IMG_FOLDER'],'grayscale.png'))
    except:
        to_grayscale()
    vector_size = (grayscale_image.size[0]*16, grayscale_image.size[1]*16)
    vector_image = Image.new('L', vector_size, 1)
    vector_pixels = vector_image.load()
    image = {}
    vector_data = []
    for index,pixel in enumerate(grayscale_image.getdata()):
        x = (index % grayscale_image.size[0])*16
        y = (index / grayscale_image.size[0])*16
        #image_json['data'].append([x, y])
        #image_json['data'].append(pixel)
        for i in range(pixel):
            vector_pixels[x+random.randint(0,15), y+random.randint(0,15)] = 255
        #    image_json['data'].append([x, y])
        #    image_json['data'].append(i)
    vector_image.save(os.path.join(app.config['IMG_FOLDER'], filename))
    return redirect(url_for('get_file', filename=filename))

@app.route('/json')
def to_json():
    try:
        image = Image.open(os.path.join(app.config['IMG_FOLDER'],'vector.png'))
    except:
        to_vector()
    image = image.convert('L',dither=Image.NONE)
    image_json = {}
    image_json['size'] = image.size
    image_json['data'] = []
    return json.JSONEncoder().encode(image_json)

@app.route('/paper')
def paper():
    return render_template('paper.html')

@app.route('/img/<filename>')
def get_file(filename):
    return send_from_directory(app.config['IMG_FOLDER'], filename)

if __name__ == '__main__':
    app.run()

