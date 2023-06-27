from flask_sqlalchemy import SQLAlchemy
from analytics import Analytics
from flask_mail import Mail

data_logger = Analytics()
# Database object
db = SQLAlchemy()
mail = Mail()

