from app.core.database import engine, Base
from app.models import Notification

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
