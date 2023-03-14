"""User model tests."""

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

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    """Test model for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does __repr__ correctly display the user?"""

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(user)
        db.session.commit()

        self.assertEqual(user.__repr__(), f"<User #{user.id}: testuser, test@test.com>")



    def test_is_following(self):
        """Does is_following correctly detect when user1 is following user2?"""

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD1"
        )

        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add_all([user1, user2])
        db.session.commit()

        # user1.is_following(user2) should return False
        self.assertFalse(user1.is_following(user2))

        follow = Follows(user_being_followed_id=user2.id, user_following_id=user1.id)
        db.session.add(follow)
        db.session.commit()

        # user1.is_following(user2) should return True
        self.assertTrue(user1.is_following(user2))

    def test_is_followed_by(self):
        """Does is_followed_by correctly detect when user1 is followed by user2?"""

        user1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD1"
        )

        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add_all([user1, user2])
        db.session.commit()

        # user1.is_followed_by(user2) should return False
        self.assertFalse(user1.is_followed_by(user2))

        follow = Follows(user_being_followed_id=user1.id, user_following_id=user2.id)
        db.session.add(follow)
        db.session.commit()

        # user1.is_followed_by(user2) should return True
        self.assertTrue(user1.is_followed_by(user2))

    def test_user_signup(self):
        """
        Does User.signup successfully create a new User given valid credentials
        and fail to create a new User if any of the validations fail?
        """

        # creating and commiting a user with proper credentials should correctly create that User
        user1 = User.signup("testuser", "test1@test.com", "HASHED_PASSWORD1", "")
        db.session.add(user1)
        db.session.commit()
        self.assertIsInstance(user1, User)
        self.assertIn(user1, User.query.all())

        # attempting to commit a user with a duplicate username should yield an IntegrityError exception
        user2 = User.signup("testuser", "test2@test.com", "HASHED_PASSWORD2", "")
        db.session.add(user2)
        self.assertRaises(IntegrityError, db.session.commit)

        # test other validations on creation?

    def test_user_authenticate(self):
        """
        Does User.authenticate:
        1) successfully return a user when given a valid username and password?
        2) fail to return a user when the username is invalid? AND
        3) fail to return a user when the password is invalid?
        """

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(user)
        db.session.commit()

        # Strange error with 1st and 3rd assert statements below, shows "invalid salt" but it's bcrypt that handles that...
        # User.authenticate should return the user when passed valid credentials
        self.assertIs(user, User.authenticate(username="testuser", password="HASHED_PASSWORD"))

        # User.authenticate should return False when passed an incorrect username
        self.assertFalse(User.authenticate(username="testuse", password="HASHED_PASSWORD"))

        # User.authenticate should return False when passed an incorrect password
        self.assertFalse(User.authenticate(username="testuser", password="HASHEDPASSWORD"))