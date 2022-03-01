import os
import sys
import json
import unittest
from hashlib import sha256
from gitinspector import format
from io import StringIO
from contextlib import contextmanager

TEST_STRING = 'arbitrary'


class DummyRepo:
    name = TEST_STRING


@contextmanager
def print_capture(*args, **kwds):
    temp_out = StringIO()  # Create the in-memory "file"
    try:
        sys.stdout = temp_out  # Replace default stdout (terminal) with our stream
        yield temp_out
    finally:
        sys.stdout = sys.__stdout__  # Restore default stdout


class TestFormat(unittest.TestCase):

    def test_InvalidFormatError(self):
        with self.assertRaises(format.InvalidFormatError):
            raise format.InvalidFormatError(TEST_STRING)

    def test_select(self):
        test_format = 'json'
        return_value = format.select(test_format)
        self.assertTrue(return_value)

    def test_get_selected(self):
        test_format = 'json'
        format.select(test_format)
        expected = test_format
        actual = format.get_selected()
        self.assertEqual(expected, actual)

    def test_is_interactive_format(self):
        test_format = 'json'
        format.select(test_format)
        return_value = format.is_interactive_format()
        self.assertFalse(return_value)

    def test__output_html_template__(self):
        test_template_path = os.path.join('html', 'html.header')
        return_value = format.__output_html_template__(test_template_path)
        return_value_hash = sha256(return_value.encode('utf-8')).hexdigest()
        expected_hash = '6b113dca32e7947e21ad9ad910c4995e62672ca4c0bc34577e33d2e328da7b3a'
        self.assertEqual(expected_hash, return_value_hash)

    def test__get_zip_file_content__(self):
        return_value = format.__get_zip_file_content__('LICENSE.txt')
        return_value_hash = sha256(return_value.encode('utf-8')).hexdigest()
        expected_hash = '52cb566b16d84314b92b91361ed072eaaf166e8d3dfa3d0fd3577613925f205c'
        self.assertEqual(expected_hash, return_value_hash)

    def test_json_output_header_and_footer(self):
        test_format = 'json'
        format.select(test_format)
        repos = [DummyRepo()]
        with print_capture() as output:
            format.output_header(repos)
            format.output_footer()
            output_text = output.getvalue()[:-2].replace('\n', '').replace('\t', '')[:-2] + "}}"
            output_json = json.loads(output_text)
            self.assertIn('report_date', output_json['gitinspector'])
            self.assertEqual(output_json['gitinspector']['repository'], 'arbitrary')
            self.assertEqual(output_json['gitinspector']['version'], '0.5.0dev')
