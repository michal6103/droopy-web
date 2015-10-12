#!/usr/bin/env python
import os
from flask import Flask, request, redirect, send_file
from flask import url_for, send_from_directory, render_template
from flask_bootstrap import Bootstrap
from PIL import Image
import json
# from random import random
from pyhull.voronoi import VoronoiTess
# import numpy as np
from werkzeug.contrib.cache import SimpleCache
import logging
from random import randint
# from uuid import uuid4
#t from math import sqrt
from pymongo import MongoClient



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


def to_points(image):
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
    # return (sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2))
    return (abs(b[0] - a[0]) + abs(b[1] - a[1]))


def find_closest(origin, points, min=1):
    """Find closest point to the origin from points in the list.
    Remove closest point from list of points abd return closest point
    """
    closest = (float("inf"), float("inf"))
    closest_distance = distance(origin, closest)
    # app.logger.debug("Initial distance: {}\t{}\t{}".format(origin,
    # closest, closest_distance))
    for point in points:
        actual_distance = distance(origin, point)
        # app.logger.debug("Distance: {}\t{}\t{}".format(origin,
        # point, actual_distance))
        if actual_distance < closest_distance:
            closest = point
            closest_distance = actual_distance
        # If actual distance is smaller or equal to minimal possible use it
        if closest_distance <= min:
            break
    app.logger.debug("Closest: {}<->{} =\t{}".format(origin,
                                                     closest,
                                                     closest_distance))
    return (closest, closest_distance)


def bounding_boxes_overlap(line1, line2):
    point1, point2 = line1
    x1, y1 = point1
    x2, y2 = point2
    point1, point2 = line2
    x3, y3 = point1
    x4, y4 = point2
    if len(set([x1, x2, x3, x4])) < 4:
        app.logger.debug("Not enough points. Boxes not overlaping".format(line1, line2))
        return False
    x_overlap = False
    y_overlap = False
    # Convert lines to bounding boxes
    if x1 > x2:
        x1, x2 = x2, x1
    if x3 > x4:
        x3, x4 = x4, x3
    if y1 > y2:
        y1, y2 = y2, y1
    if y3 > y4:
        y3, y4 = y4, y3
    # Find if boxes overlap
    if x1 < x3 < x2 or x1 < x4 < x2:
        x_overlap = True
    if x3 <= x1 and x4 >= x2:
        x_overlap = True
    if x1 <= x3 and x2 >= x4:
        x_overlap = True
    if y1 < y3 < y2 or y1 < y4 < y2:
        y_overlap = True
    if y3 <= y1 and y4 >= y2:
        y_overlap = True
    if y1 <= x3 and y2 >= y4:
        y_overlap = True
    app.logger.debug("{} - {} Overlap X: {}\tOverlap Y: {}".format(line1, line2, x_overlap, y_overlap))
    return x_overlap and y_overlap


def orientation(a, b, c):
    """ Based on http://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/
    Return 0 if a,b,c  are colinear
    Return 1 if CCW
    Return -1 if CW

    param: a,b,c
    """
    d = (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])
    if d > 0:
        return 1
    else:
        if d < 0:
            return -1
    return 0


def is_on_segment(line, c):
    """ Returns True if c is on segment, False otherwise. Line and c should
        be colinear

        param: line  two points
        param: c point colinear with line
    """
    return bounding_boxes_overlap(line, (c, c))


def is_colinear(line1, line2):
    """ Check if two segments are colinear.
    Based on http://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/

    Return: True if line1 and line2 are colinear
    Return: Fale if line1 and line2 are not colinear
    """
    a, b = line1
    c, d = line2

    if orientation(a, b, c) == 0 and orientation(a, b, d) == 0:
        return True
    else:
        return False


def is_intersection(line1, line2):
    """ Check if the line1 and line2 are intersected
    """
    if bounding_boxes_overlap(line1, line2):
        a, b = line1
        c, d = line2
        o1 = orientation(a, b, c)
        o2 = orientation(a, b, d)
        o3 = orientation(c, d, a)
        o4 = orientation(c, d, b)
        app.logger.debug("Orientations: {},{},{},{} lines: {}\t{}".format(o1, o2, o3, o4, line1, line2))
        if o1 and o1 == o2:
            app.logger.debug("No intersection: Colinear")
            return False
        if o3 and o3 == o4:
            app.logger.debug("No intersection: Colinear")
            return False
        if is_colinear(line1, line2):
            app.logger.debug("intersection overlaping: {} - {}".format(line1, line2))
            return True
        app.logger.debug("intersection general: {} - {}".format(line1, line2))
        return True
    else:
        app.logger.debug("No intersection, No bounding boxes: {} - {}".format(line1, line2))
        return False


def untangle(path):
    """ Untangle crossed line segments.
    """
    i = 1
    tangled = True
    count = len(path)
    app.logger.debug("Path length: {}".format(count))
    app.logger.info("{}".format(path))
    switched = False
    while tangled:
        # j = 1
        for j in range(i + 2, count):
            a = path[i - 1]
            b = path[i]
            c = path[j - 1]
            d = path[j]
            line1 = (a, b)
            line2 = (c, d)
            app.logger.debug("Checking paths: {}: {} {} from range ({}, {}/{})".format(j, line1, line2, i, j, count))
            if is_intersection(line1, line2):
                # untangle shorter path
                # 1 4 3 2 vs 1 3 2 4
                distance1 = distance(a, d) + distance(c, b)
                distance2 = distance(a, c) + distance(b, d)
                if (distance1 < distance2)  == randint(0,10):
                    # reverse path in from i to j included
                    path[i:j+1] = path[j:i-1:-1]
                    #path[i], path[j] = path[j], path[i]
                else:
                    path[i:j] = path[j-1:i-1:-1]
                    #path[i], path[j - 1] = path[j - 1], path[i]
                app.logger.info("Untangling: i{} j{} l1{},l2{} points {} {} {} {}".format(i, j, line1, line2, path[i - 1], path[i], path[j - 1], path[j]))
                switched = True
        if i == count-3 and not switched:
                tangled = False
        else:
            i += 1
        if switched:
            i = 1
            switched = False
        app.logger.debug("{}".format(path))
        app.logger.debug("Checking paths iteration: {}/{} Tangled: {}".format(i, count, tangled))
    return path


def trace(points):
    """Returns sorted trace of all points
    """
    point = (0, 0)
    path = []
    path.append(point)
    last_distance = 0
    while points:
        point, last_distance = find_closest(point, points, last_distance)
        points.remove(point)
        path.append(point)
        app.logger.debug("Points: {}\n{}".format(len(points), point))
    untangled_path = untangle(path)
    return untangled_path


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
        points = to_points(image)
        # spreaded_points = voronoi_spread(points)
        # voronoi = VoronoiTess(spreaded_points, add_bounding_box=True)
        # voronoi_points = voronoi.vertices
        points_path = trace(points)
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
