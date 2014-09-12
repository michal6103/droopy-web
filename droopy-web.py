#!/usr/bin/env python
import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from flask_bootstrap import Bootstrap
#from werkzeug import secure_filename
from PIL import Image
import json
from random import random


IMG_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'img/')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
SCALE = 10.0


app = Flask(__name__)
Bootstrap(app)
app.debug = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['IMG_FOLDER'] = IMG_FOLDER
app.config['IMAGE_SCALE'] = SCALE


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
            return redirect(url_for('to_grayscale'))
            #return redirect(url_for('get_file', filename=filename))
    return render_template('index.html')


@app.route('/grayscale')
def to_grayscale():
    try:
        image = Image.open(os.path.join(app.config['IMG_FOLDER'], 'source.png'))
    except:
        return redirect(url_for('upload_file'))
    image = image.convert('L', dither=Image.NONE)
    filename = 'grayscale.png'
    image.save(os.path.join(app.config['IMG_FOLDER'], filename))
    return redirect(url_for('paper'))
    #return redirect(url_for('get_file', filename=filename))


def to_analog(image):
    points = []
    scale = app.config['IMAGE_SCALE']
    pixels = list(image.getdata())
    x_size, y_size = image.size
    for x in range(x_size):
        for y in range(y_size):
            pixel = pixels[y * x_size + x]
            #generate random pointo for every brightness point in pixel
            for i in range(int((255 - pixel) / 16)):
                points.append(((x + random()) * scale, (y + random()) * scale))
    return points


@app.route('/json')
def to_json():
    try:
        image = Image.open(os.path.join(app.config['IMG_FOLDER'], 'grayscale.png'))
    except:
        to_grayscale()
    #grayscale_pixels = image.load()
    image.load()
    image = image.convert('L', dither=Image.NONE)
    image_json = {}
    image_json['size'] = image.size
    image_json['data'] = list(image.getdata())
    image_json['analog_data'] = to_analog(image)
    #pixel = []
    return json.JSONEncoder().encode(image_json)


@app.route('/paper')
def paper():
    return render_template('paper.html')


@app.route('/img/<filename>')
def get_file(filename):
    return send_from_directory(app.config['IMG_FOLDER'], filename)

if __name__ == '__main__':
    app.run()
