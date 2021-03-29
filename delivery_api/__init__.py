# -*- coding: utf-8 -*-
from flask import Flask, jsonify
from werkzeug.exceptions import NotFound, BadRequest, InternalServerError
from .models import db
from .views import bp


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    app.register_blueprint(bp)

    @app.errorhandler(NotFound)
    def handle_not_found(e):
        return jsonify('Not found'), 404

    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        return jsonify('Bad request'), 400

    @app.errorhandler(InternalServerError)
    def handle_not_found(e):
        return jsonify('Internal server error'), 500

    return app
