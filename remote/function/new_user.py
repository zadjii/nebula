from datetime import datetime
import getpass
from werkzeug.security import generate_password_hash
from remote import User, get_db
# from remote import remote_db as db

__author__ = 'zadjii'


def new_user(argv):
    db = get_db()
    print 'here we\'ll make a new user'

    email = raw_input('Enter an email for the new user: ').lower()
    # todo validate that this is in fact an email
    # already_exists = User.query.filter_by(email=email).first()
    already_exists = db.session.query(User).filter_by(email=email).first()
    if already_exists:
        print 'A user already exists with that email address.'
        return

    username = raw_input('Enter a username for the new user: ').lower()
    already_exists = db.session.query(User).filter_by(username=username).first()
    if already_exists:
        print 'A user already exists with that username.'
        return

    name = raw_input('Enter a name for the new user: ').lower()
    password = getpass.getpass('Enter a password for the new user: ')
    password_again = getpass.getpass('Enter the password (again): ')

    if password != password_again:
        print 'The passwords entered didn\'t match'
        return

    new_user_instance = User(
        email=email
        , username=username
        , password=generate_password_hash(password)
        , name=name
        , created_on=datetime.utcnow()
    )
    db.session.add(new_user_instance)
    db.session.commit()
    print 'There are now ', db.session.query(User).count(), 'users'

