#!/usr/bin/env python
import os
from flask import Flask, request, redirect, send_file, session
from flask import url_for, send_from_directory, render_template
from flask_bootstrap import Bootstrap
from PIL import Image
import json
# from random import random
from pyhull.voronoi import VoronoiTess
# import numpy as np
from werkzeug.contrib.cache import SimpleCache
import logging
# from uuid import uuid4


IMG_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'img/')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


app = Flask(__name__)
Bootstrap(app)
app.debug = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['IMG_FOLDER'] = IMG_FOLDER
# app.config['IMAGE_SCALE'] = SCALE
# app.config['IMAGE_RANDOM_OVERLAP'] = RANDOM_OVERLAP
cache = SimpleCache()


def allowed_file(filename):
    """Returns true if file has an dot in filename and extension
    is in ALLOWED_EXTENSION
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            cache.delete('points_spread')
            filename = 'source'
            file.save(os.path.join(app.config['IMG_FOLDER'], filename))
            return redirect(url_for('to_grayscale'))
            # return redirect(url_for('get_file', filename=filename))
    return render_template('index.html')


@app.route('/grayscale')
def to_grayscale():
    try:
        image = Image.open(os.path.join(app.config['IMG_FOLDER'], 'source'))
    except:
        return redirect(url_for('upload_file'))
    image = image.convert('1')
    filename = 'grayscale'
    full_filename = os.path.join(app.config['IMG_FOLDER'], filename)
    image.save(full_filename, "PNG")
    # return redirect(url_for('paper'))
    # return redirect(url_for('get_file', filename=filename))
    return send_file(full_filename, mimetype="image/png")


def to_analog(image):
    points = []
    pixels = list(image.getdata())
    x_size, y_size = image.size
    for y in range(y_size):
        for x in range(x_size):
            pixel = pixels[y * x_size + x]
            xr = x
            if not pixel:
                points.append((xr, y))
    return points


def distance(a, b):
    """Computes manhatan distance of a and b
    """
    return (abs(b[0] - a[0]) + abs(b[1] - a[1]))


def find_closest(origin, points, min = 0):
    """Find closest point to the origin from points in the list.
    Remove closest point from list of points abd return closest point
    """
    closest = (float("inf"), float("inf"))
    closest_distance = distance(origin, closest)
    # app.logger.debug("Initial distance: {}\t{}\t{}".format(origin, closest, closest_distance))
    for point in points:
        actual_distance = distance(origin, point)
        # app.logger.debug("Distance: {}\t{}\t{}".format(origin, point, actual_distance))
        if actual_distance < closest_distance:
            # app.logger.debug("Swapping min-distance: {}<->{}\t{}<->{}".format(closest, point, closest_distance, actual_distance))
            closest = point
            closest_distance = actual_distance
        # If actual_distance is 1 there will be nothing closer
        if actual_distance == 1:
            break
        # If actual distance is smaller or equal to minimal possible use it
        if actual_distance <= min:
            break
    app.logger.debug("Closest: {}<->{} =\t{}".format(origin, closest, closest_distance))
    return closest


def trace(points):
    """Returns sorted trace of all points
    """
    path = []
    point = (0, 0)
    while points:
        point = find_closest(point, points)
        points.remove(point)
        path.append(point)
        if len(points):
            app.logger.debug("Points: {}\n{}".format(len(points), point))
    return path


def voronoi_spread(points):
    # get image boundaries
    boundary_x_min = min(x for (x, y) in points)
    boundary_y_min = min(y for (x, y) in points)
    boundary_x_max = max(x for (x, y) in points)
    boundary_y_max = max(y for (x, y) in points)
    # Move points to centers of voronoi regions
    voronoi = VoronoiTess(points, add_bounding_box=True)
    # compute centroid for every region
    points_centered = []
    for region in voronoi.regions:
        region_vertices = [voronoi.vertices[point_index] for point_index in region]
        if len(region_vertices):
            x_avg = sum(x for (x, y) in region_vertices) / len(region_vertices)
            y_avg = sum(y for (x, y) in region_vertices) / len(region_vertices)
            if boundary_x_min < x_avg < boundary_x_max and boundary_y_min < y_avg < boundary_y_max:
                points_centered.append((x_avg, y_avg))
    # Last Voronoi tesselation from centered points
    # points = VoronoiTess(points_centered, add_bounding_box=True)
    return points


@app.route('/json')
def to_json():
    try:
        image = Image.open(os.path.join(app.config['IMG_FOLDER'], 'grayscale'))
    except:
        to_grayscale()
    image.load()
    image_json = {}
    image_json['size'] = image.size
    points_path = cache.get('points_path')
    if points_path is None:
        # image_json['data'] = list(image.getdata())
        points_analogue = to_analog(image)
        points_path = trace(points_analogue)
        cache.set('points_path', points_path, timeout=60 * 60 * 60)
    image_json['analog_data'] = points_path
    # pixel = []
    return json.JSONEncoder().encode(image_json)


@app.route('/paper')
def paper():
    return render_template('paper.html')


@app.route('/img/<filename>')
def get_file(filename):
    return send_from_directory(app.config['IMG_FOLDER'], filename)

if __name__ == '__main__':
    app.logger.setLevel(logging.INFO)
    app.run(host='0.0.0.0')
