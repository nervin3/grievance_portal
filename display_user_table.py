from app import db, User, app  # Import from your app module

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Password Hash: {user.password_hash}")
