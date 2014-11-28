#!/usr/bin/env python
import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from flask_bootstrap import Bootstrap
#from werkzeug import secure_filename
from PIL import Image
import json
from random import random
from pyhull.voronoi import VoronoiTess
import numpy as np
from werkzeug.contrib.cache import SimpleCache



IMG_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'img/')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
SCALE =0.1


app = Flask(__name__)
Bootstrap(app)
app.debug = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['IMG_FOLDER'] = IMG_FOLDER
app.config['IMAGE_SCALE'] = SCALE
cache = SimpleCache()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            #filename = secure_filename(file.filename)
            cache.delete('points_spread')
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
    offset_x = 0.0
    offset_y = 0.0
    pixels = list(image.getdata())
    x_size, y_size = image.size
    for y in range(y_size):
        for x in range(x_size):
            if y % 2:
                pixel = pixels[y * x_size + x]
                xr = x;
            else:
                pixel = pixels[y * x_size - x]
                xr = x_size - x;

            #generate random points for every brightness point in pixel
            for i in range(int((255 - pixel) / 16)):
                points.append(((xr + random()*1.0) * scale + offset_x, (y + random()*1.0) * scale + offset_y))
    return points


def voronoi_spread(points, boundary):
    #Move points to centers of voronoi regions
    voronoi = VoronoiTess(points, add_bounding_box=True)
    #compute centroid for every region
    points_centered = []
    for region in voronoi.regions:
        region_vertices = [voronoi.vertices[point_index] for point_index in region]
        x_avg = sum(x for (x, y) in region_vertices) / len(region_vertices)
        y_avg = sum(y for (x, y) in region_vertices) / len(region_vertices)
        if 0 < x_avg < boundary[0] and 0 < y_avg < boundary[1]:
            points_centered.append((x_avg, y_avg))
    return points_centered


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
    points_spread = cache.get('points_spread')
    if points_spread is None:
        points_randomized = to_analog(image)
        points_spread = points_randomized
        for i in range(2):
            print("Voronoi iteration {}".format(i))
            points_spread = voronoi_spread(points_spread, image.size)
        cache.set('points_spread', points_spread, timeout = 60 * 60)
    image_json['analog_data'] = points_spread 
    #pixel = []
    return json.JSONEncoder().encode(image_json)


@app.route('/paper')
def paper():
    return render_template('paper.html')


@app.route('/img/<filename>')
def get_file(filename):
    return send_from_directory(app.config['IMG_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
