from delivery_api import create_app
from delivery_api.models import db

app = create_app()
app.app_context().push()
db.create_all()

