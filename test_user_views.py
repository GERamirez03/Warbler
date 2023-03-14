"""User views tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Since we will be testing adding and removing messages, we will need to disable CSRF tokens
app.config['WTF_CSRF_ENABLED'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

class UserViewsTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(user)
        db.session.commit()

        message = Message(text="Test", user_id=user.id)

        db.session.add(message)
        db.session.commit()

        self.user_id = user.id
        self.message_id = message.id
    
    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_logged_out_restrictions(self):
        """
        When logged out, are you prohibited from:
        1) visiting a user's follower/following pages?
        2) adding messages?
        3) deleting messages?
        """

        # logged out users should be prohibited from adding messages
        data = {"text": "Test"}
        response = self.client.post("/messages/new", data=data, follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Access unauthorized.", html)

        # logged out users should be prohibited from deleting messages
        response = self.client.post(f"/messages/{self.message_id}/delete", follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Access unauthorized.", html)

        ##### logged out users should be prohibited from visiting a user's follower/following pages #####

        # followers
        response = self.client.get(f"/users/{self.user_id}/followers", follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Access unauthorized.", html)

        # following
        response = self.client.get(f"/users/{self.user_id}/following", follow_redirects=True)
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Access unauthorized.", html)

    def test_logged_in_functionality(self):
        """
        When logged in, can you:
        1) can you add a message as yourself?
        2) can you delete a message as yourself?
        """

        # "log in" by adding test user's id to the session
        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.user_id

            # proceed with tests

            # logged in users should be able to add a message as themselves
            data = {"text": "Test2"}
            response = self.client.post("/messages/new", data=data, follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)

            # checking for "Test" suffices because our new message route redirects to
            # the poster's profile page, which includes their messages.
            # So this assert checks that the message was posted
            # AND the author is the logged in user.
            self.assertIn("Test2", html)


            # logged in users should be able to delete a message as themselves
            response = self.client.post(f"/messages/{self.message_id}/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertNotIn("Test", html)

    def test_logged_in_restrictions(self):
        """
        When logged in, are you prohibited from:
        1) adding a message as another user?
        2) deleting a message as another user?
        """

        # create and log in as new user to test restrictions
        test_user = User(
            email="test_user@test.com",
            username="test_user",
            password="HASH_PWD"
        )
        db.session.add(test_user)
        db.session.commit()

        # "log in" by adding test user's id to the session
        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = test_user.id

            # proceed with tests

            # logged in users should be prohibited from deleting a message as another user
            response = self.client.post(f"/messages/{self.message_id}/delete", follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized.", html)

            # confused about how someone would impersonate a different user and post
            # a message that way if the route requires users to be signed in AND
            # always uses the signed-in user as the author



