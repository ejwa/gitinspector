import unittest
from gitinspector import gravatar

TEST_STRING = 'arbitrary'


class TestGravatar(unittest.TestCase):

    def test_get_url(self):
        expected_url = 'https://www.gravatar.com/avatar/c181b12d45d1fd849f885221f3ee3f39?default=identicon'
        arbitrary_email = TEST_STRING + '@example.com'
        actual_url = gravatar.get_url(arbitrary_email)
        self.assertEqual(expected_url, actual_url)
