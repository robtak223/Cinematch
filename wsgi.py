from app import create_app
import logging

"""
Gunicorn is used for a more robust server than the built in Flask server. This file contains the configurations.
"""
gunicorn_logger = logging.getLogger('gunicorn.error')
app = create_app()
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)