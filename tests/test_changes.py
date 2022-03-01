import unittest
from gitinspector import changes


FAKE_FILE_NAME = 'Arbitrary.ext'
FAKE_COMMIT_STRING = "1614563270|2021-02-28|53d81bcd2612dbc47e73c71ee43baae83c1ec252|JP White|jpwhite3@gmail.com"


class TestAuthorInfo(unittest.TestCase):

    def test_AuthorInfo_attrs(self):
        author = changes.AuthorInfo()
        expected_email = None
        expected_insertions = 0
        expected_deletions = 0
        expected_commits = 0
        self.assertEqual(expected_email, author.email)
        self.assertEqual(expected_insertions, author.insertions)
        self.assertEqual(expected_deletions, author.deletions)
        self.assertEqual(expected_commits, author.commits)


class TestFileDiff(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        pass

    def test_FileDiff_init(self):
        test_string = 'ArbitraryName|-++-+'
        file_diff = changes.FileDiff(test_string)
        expected_name = 'ArbitraryName'
        self.assertEqual(expected_name, file_diff.name)
        expected_insertions = 3
        self.assertEqual(expected_insertions, file_diff.insertions)
        expected_deletions = 2
        self.assertEqual(expected_deletions, file_diff.deletions)

    def test_is_not_filediff_line(self):
        actual = changes.FileDiff.is_filediff_line(FAKE_FILE_NAME)
        self.assertFalse(actual)

    def test_is_filediff_line(self):
        test_file_diff_string = "arbitrary|--- a/file.txt"
        actual = changes.FileDiff.is_filediff_line(test_file_diff_string)
        self.assertTrue(actual)

    def test_get_extension(self):
        expected = 'ext'
        actual = changes.FileDiff.get_extension(FAKE_FILE_NAME)
        self.assertEqual(actual, expected)

    def test_get_extension_from_file_without_extension(self):
        test_file_name = 'Arbitrary'
        expected = ''
        actual = changes.FileDiff.get_extension(test_file_name)
        self.assertEqual(actual, expected)

    def test_get_filename(self):
        expected = FAKE_FILE_NAME
        actual = changes.FileDiff.get_filename(expected)
        self.assertEqual(actual, expected)

    def test_is_not_valid_extension(self):
        return_value = changes.FileDiff.is_valid_extension(FAKE_FILE_NAME)
        self.assertFalse(return_value)

    def test_is_valid_extension(self):
        test_file_name = 'Arbitrary.cpp'
        return_value = changes.FileDiff.is_valid_extension(test_file_name)
        self.assertTrue(return_value)


class TestCommitClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        pass

    def test_Commit_init(self):
        commit = changes.Commit(FAKE_COMMIT_STRING)
        expected_timestamp = '1614563270'
        expected_date = '2021-02-28'
        expected_sha = '53d81bcd2612dbc47e73c71ee43baae83c1ec252'
        expected_author = 'JP White'
        expected_email = 'jpwhite3@gmail.com'
        self.assertEqual(expected_timestamp, commit.timestamp)
        self.assertEqual(expected_date, commit.date)
        self.assertEqual(expected_sha, commit.sha)
        self.assertEqual(expected_author, commit.author)
        self.assertEqual(expected_email, commit.email)

    def test_get_author_and_email(self):
        expected_author = 'JP White'
        expected_email = 'jpwhite3@gmail.com'
        actual_author, actual_email = changes.Commit.get_author_and_email(FAKE_COMMIT_STRING)
        self.assertEqual(expected_author, actual_author)
        self.assertEqual(expected_email, actual_email)

    def test_is_commit_line(self):
        return_value = changes.Commit.is_commit_line(FAKE_COMMIT_STRING)
        self.assertTrue(return_value)

    def test_add_filediff(self):
        commit = changes.Commit(FAKE_COMMIT_STRING)
        commit.add_filediff(1)
        expected = [1]
        actual = commit.get_filediffs()
        self.assertEqual(expected, actual)
