import logging
from flask import Flask, jsonify, render_template, request
import json
from error import *
from common import CINEMATCH_EMAIL, PROD_DB_STRING
from friends import friends_bp
from users import users_bp
from movies import movies_bp
from groups import groups_bp
from database import db, data_logger, mail

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = PROD_DB_STRING
    app.config['TESTING'] = False
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=465,
        MAIL_USE_SSL=True,
        MAIL_DEFAULT_SENDER=CINEMATCH_EMAIL,
        MAIL_USERNAME = CINEMATCH_EMAIL,
        MAIL_PASSWORD = 'mkfocwgeejsxrehj',
        MAIL_SUPPRESS_SEND=False
    )

    db.init_app(app)
    mail.init_app(app)

    with app.app_context():
        db.create_all()
        db.metadata.reflect(db.engine)

    """
    Basic home and error endpoints
    """
    @app.errorhandler(APIError)
    def handle_exception(err):
        response = {"error": err.description, "code": err.code}
        return jsonify(response), err.code

    @app.route('/', methods=['GET'])
    def get():
        return render_template('index.html')

    @app.route('/analytics/update', methods=['POST'])
    def analytics():
        content_type = request.headers.get('Content-Type')
        # ensure json data is passed in
        if (content_type != 'application/json'):
            raise APITypeError('Content type not supported (JSON Required)')
        content = json.loads(request.data)
        if 'instance' not in content:
            raise APITypeError('Missing information (instance)')

        inst = content['instance']
        data_logger.update_table(int(inst))
        response = {"message": "success"}
        return jsonify(response)
    
    @app.route('/stats', methods=['GET'])
    def times():
        variables = data_logger.get_stats()
        return render_template('home.html', **variables)

    app.register_blueprint(friends_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(users_bp)

    return app


if __name__ == "__main__":
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app = create_app()
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.run(port=3000)