import unittest
import os
import tempfile
from app import app
from config import Config

class ImageCaptionGeneratorTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = app.test_client()
        self.app.testing = True
        
    def test_index_route(self):
        """Test the main index route."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AI Caption Generator', response.data)
    
    def test_generate_caption_no_file(self):
        """Test caption generation without file."""
        response = self.app.post('/generate_caption')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'No file part', response.data)
    
    def test_generate_caption_empty_filename(self):
        """Test caption generation with empty filename."""
        data = {'file': (tempfile.NamedTemporaryFile(), '')}
        response = self.app.post('/generate_caption', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'No selected file', response.data)
    
    def test_config_values(self):
        """Test configuration values."""
        self.assertIsInstance(Config.ALLOWED_EXTENSIONS, set)
        self.assertIn('jpg', Config.ALLOWED_EXTENSIONS)
        self.assertIn('png', Config.ALLOWED_EXTENSIONS)
        self.assertEqual(Config.MAX_CONTENT_LENGTH, 16 * 1024 * 1024)

if __name__ == '__main__':
    unittest.main()