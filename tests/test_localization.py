"""Comprehensive tests for localization module."""

import gettext
import locale
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from gitinspector import localization


class TestLocalization(unittest.TestCase):
    """Test suite for localization module."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset global state
        localization.__enabled__ = False
        localization.__installed__ = False
        localization.__translation__ = None
        
        # Create temporary directory for test files
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Reset global state
        localization.__enabled__ = False
        localization.__installed__ = False
        localization.__translation__ = None
        
        # Clean up temporary directory
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_n_function(self):
        """Test N_ dummy function for string constants."""
        test_message = "Test message"
        result = localization.N_(test_message)
        self.assertEqual(result, test_message)

    @patch('locale.setlocale')
    @patch('locale.getlocale')
    def test_init_success_no_translation_file(self, mock_getlocale, mock_setlocale):
        """Test initialization when no translation file exists."""
        mock_getlocale.return_value = ('en_US', 'UTF-8')
        
        with patch('gitinspector.basedir.get_basedir') as mock_get_basedir:
            mock_get_basedir.return_value = str(self.temp_dir)
            
            localization.init()
            
            self.assertTrue(localization.__enabled__)
            self.assertTrue(localization.__installed__)
            self.assertIsInstance(localization.__translation__, gettext.NullTranslations)

    @patch('locale.setlocale')
    @patch('locale.getlocale')
    @patch('gettext.GNUTranslations')
    def test_init_success_with_translation_file(self, mock_gnu_translations, mock_getlocale, mock_setlocale):
        """Test initialization with existing translation file."""
        mock_getlocale.return_value = ('es_ES', 'UTF-8')
        
        # Create a mock translation file
        translations_dir = self.temp_dir / "translations"
        translations_dir.mkdir()
        translation_file = translations_dir / "messages_es.mo"
        
        # Create a simple file (content doesn't matter since we're mocking GNUTranslations)
        translation_file.write_bytes(b'mock translation file')
        
        # Mock the GNUTranslations constructor
        mock_translation_instance = MagicMock()
        mock_gnu_translations.return_value = mock_translation_instance
        
        with patch('gitinspector.basedir.get_basedir') as mock_get_basedir:
            mock_get_basedir.return_value = str(self.temp_dir)
            
            localization.init()
            
            self.assertTrue(localization.__enabled__)
            self.assertTrue(localization.__installed__)
            self.assertEqual(localization.__translation__, mock_translation_instance)

    @patch('locale.setlocale')
    def test_init_locale_error(self, mock_setlocale):
        """Test initialization when locale setting fails."""
        mock_setlocale.side_effect = locale.Error("Locale not available")
        
        localization.init()
        
        self.assertTrue(localization.__enabled__)
        self.assertTrue(localization.__installed__)
        self.assertIsInstance(localization.__translation__, gettext.NullTranslations)

    @patch('locale.setlocale')
    @patch('locale.getlocale')
    @patch('locale.getdefaultlocale')
    @patch.dict(os.environ, {}, clear=True)
    def test_init_windows_lang_fix(self, mock_getdefaultlocale, mock_getlocale, mock_setlocale):
        """Test initialization with Windows LANG environment variable fix."""
        mock_getlocale.return_value = ('de_DE', 'UTF-8')
        mock_getdefaultlocale.return_value = ('de_DE', 'UTF-8')
        
        with patch('gitinspector.basedir.get_basedir') as mock_get_basedir:
            mock_get_basedir.return_value = str(self.temp_dir)
            
            localization.init()
            
            self.assertEqual(os.environ.get('LANG'), 'de_DE')
            self.assertTrue(localization.__enabled__)
            self.assertTrue(localization.__installed__)

    @patch('locale.setlocale')
    @patch('locale.getlocale')
    def test_init_no_locale_warning(self, mock_getlocale, mock_setlocale):
        """Test initialization when system language cannot be determined."""
        mock_getlocale.return_value = (None, None)
        
        with patch('sys.stderr') as mock_stderr:
            localization.init()
            
            # Check that warning was printed
            mock_stderr.write.assert_called()
            warning_calls = [call for call in mock_stderr.write.call_args_list 
                           if 'WARNING: Localization disabled' in str(call)]
            self.assertTrue(len(warning_calls) > 0)

    def test_init_already_installed(self):
        """Test that init doesn't run twice."""
        localization.__installed__ = True
        original_enabled = localization.__enabled__
        
        localization.init()
        
        # Should not change state if already installed
        self.assertEqual(localization.__enabled__, original_enabled)

    def test_check_compatibility_gnu_translations(self):
        """Test compatibility check with GNU translations."""
        mock_translation = MagicMock(spec=gettext.GNUTranslations)
        localization.__translation__ = mock_translation
        
        # Mock the _() function to return header info
        def mock_gettext(msg):
            if msg == "":
                return "Project-Id-Version: gitinspector 0.4.4\nLast-Translator: Test User <test@example.com>\n"
            return msg
        
        with patch('builtins._', side_effect=mock_gettext), \
             patch('sys.stderr') as mock_stderr:
            
            localization.check_compatibility("0.4.3")  # Different version
            
            # Should print warning about outdated translation
            mock_stderr.write.assert_called()
            warning_calls = [call for call in mock_stderr.write.call_args_list 
                           if 'WARNING: The translation' in str(call)]
            self.assertTrue(len(warning_calls) > 0)

    def test_check_compatibility_null_translations(self):
        """Test compatibility check with null translations."""
        localization.__translation__ = gettext.NullTranslations()
        
        # Should not raise any errors or print warnings
        localization.check_compatibility("0.4.4")

    def test_check_compatibility_matching_version(self):
        """Test compatibility check with matching version."""
        mock_translation = MagicMock(spec=gettext.GNUTranslations)
        localization.__translation__ = mock_translation
        
        def mock_gettext(msg):
            if msg == "":
                return "Project-Id-Version: gitinspector 0.4.4\nLast-Translator: Test User <test@example.com>\n"
            return msg
        
        with patch('builtins._', side_effect=mock_gettext), \
             patch('sys.stderr') as mock_stderr:
            
            localization.check_compatibility("0.4.4")  # Matching version
            
            # Should not print any warnings
            self.assertFalse(mock_stderr.write.called)

    def test_get_date_enabled_with_gnu_translations(self):
        """Test get_date with enabled localization and GNU translations."""
        localization.__enabled__ = True
        mock_translation = MagicMock(spec=gettext.GNUTranslations)
        localization.__translation__ = mock_translation
        
        with patch('time.strftime') as mock_strftime:
            mock_strftime.return_value = "01/02/2023"
            
            result = localization.get_date()
            
            self.assertEqual(result, "01/02/2023")
            mock_strftime.assert_called_once_with("%x")

    def test_get_date_enabled_with_bytes_decode(self):
        """Test get_date with bytes that need decoding."""
        localization.__enabled__ = True
        mock_translation = MagicMock(spec=gettext.GNUTranslations)
        localization.__translation__ = mock_translation
        
        # Create a mock bytes object with decode method
        mock_date = MagicMock()
        mock_date.decode.return_value = "decoded_date"
        
        with patch('time.strftime') as mock_strftime:
            mock_strftime.return_value = mock_date
            
            result = localization.get_date()
            
            self.assertEqual(result, "decoded_date")
            mock_date.decode.assert_called_once_with("utf-8", "replace")

    def test_get_date_disabled_or_null_translations(self):
        """Test get_date with disabled localization or null translations."""
        localization.__enabled__ = False
        localization.__translation__ = gettext.NullTranslations()
        
        with patch('time.strftime') as mock_strftime:
            mock_strftime.return_value = "2023/01/02"
            
            result = localization.get_date()
            
            self.assertEqual(result, "2023/01/02")
            mock_strftime.assert_called_once_with("%Y/%m/%d")

    def test_enable_with_gnu_translations(self):
        """Test enabling localization with GNU translations."""
        mock_translation = MagicMock(spec=gettext.GNUTranslations)
        localization.__translation__ = mock_translation
        localization.__enabled__ = False
        
        localization.enable()
        
        self.assertTrue(localization.__enabled__)
        mock_translation.install.assert_called_once_with(True)

    def test_enable_with_null_translations(self):
        """Test enabling localization with null translations."""
        localization.__translation__ = gettext.NullTranslations()
        localization.__enabled__ = False
        
        localization.enable()
        
        # Should not change enabled state for null translations
        self.assertFalse(localization.__enabled__)

    def test_disable(self):
        """Test disabling localization."""
        localization.__enabled__ = True
        localization.__installed__ = True
        
        with patch('gettext.NullTranslations') as mock_null_translations:
            mock_null_instance = MagicMock()
            mock_null_translations.return_value = mock_null_instance
            
            localization.disable()
            
            self.assertFalse(localization.__enabled__)
            mock_null_instance.install.assert_called_once()

    def test_disable_not_installed(self):
        """Test disabling localization when not installed."""
        localization.__enabled__ = True
        localization.__installed__ = False
        
        localization.disable()
        
        self.assertFalse(localization.__enabled__)

    @patch('locale.setlocale')
    @patch('locale.getlocale')
    def test_init_translation_file_io_error(self, mock_getlocale, mock_setlocale):
        """Test initialization when translation file cannot be read."""
        mock_getlocale.return_value = ('fr_FR', 'UTF-8')
        
        with patch('gitinspector.basedir.get_basedir') as mock_get_basedir:
            mock_get_basedir.return_value = str(self.temp_dir)
            
            # Create translations directory but no file
            translations_dir = self.temp_dir / "translations"
            translations_dir.mkdir()
            
            localization.init()
            
            self.assertTrue(localization.__enabled__)
            self.assertTrue(localization.__installed__)
            self.assertIsInstance(localization.__translation__, gettext.NullTranslations)

    def test_module_globals_initial_state(self):
        """Test that module globals are in correct initial state."""
        # Reset to initial state
        localization.__enabled__ = False
        localization.__installed__ = False
        localization.__translation__ = None
        
        self.assertFalse(localization.__enabled__)
        self.assertFalse(localization.__installed__)
        self.assertIsNone(localization.__translation__)

    def test_type_annotations(self):
        """Test that functions have proper type annotations."""
        import inspect
        
        # Test N_ function
        sig = inspect.signature(localization.N_)
        # In Python 3.11+, annotations show as 'str' not '<class 'str'>'
        self.assertIn('str', str(sig.return_annotation))
        
        # Test other functions
        functions_to_check = [
            localization.init,
            localization.check_compatibility,
            localization.get_date,
            localization.enable,
            localization.disable
        ]
        
        for func in functions_to_check:
            sig = inspect.signature(func)
            # Just verify they have annotations (specific types may vary)
            self.assertIsNotNone(sig.return_annotation)


class TestLocalizationIntegration(unittest.TestCase):
    """Integration tests for localization module."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset global state
        localization.__enabled__ = False
        localization.__installed__ = False
        localization.__translation__ = None

    def tearDown(self):
        """Clean up test fixtures."""
        # Reset global state
        localization.__enabled__ = False
        localization.__installed__ = False
        localization.__translation__ = None

    def test_full_initialization_cycle(self):
        """Test complete initialization, enable, disable cycle."""
        # Initialize
        localization.init()
        self.assertTrue(localization.__installed__)
        
        # Enable if not already enabled
        if not localization.__enabled__:
            localization.enable()
        
        # Test get_date functionality
        date_result = localization.get_date()
        self.assertIsInstance(date_result, str)
        self.assertTrue(len(date_result) > 0)
        
        # Disable
        localization.disable()
        self.assertFalse(localization.__enabled__)

    def test_check_compatibility_real_version(self):
        """Test compatibility check with real version."""
        localization.init()
        
        # Should not raise any exceptions
        localization.check_compatibility("0.4.4")


if __name__ == '__main__':
    unittest.main()
