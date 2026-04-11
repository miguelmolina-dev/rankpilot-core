import unittest
import base64
import os
from src.io.base64_handler import decode_base64_document

class TestBase64Handler(unittest.TestCase):
    def test_decode_valid_document(self):
        # Create dummy docx content
        dummy_content = b"Dummy docx content"
        b64_string = base64.b64encode(dummy_content).decode('utf-8')

        path = decode_base64_document(b64_string, "test_doc.docx", "/tmp")

        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))

        # Verify content
        with open(path, "rb") as f:
            self.assertEqual(f.read(), dummy_content)

        # Clean up
        os.remove(path)

    def test_decode_invalid_extension(self):
        # Create dummy txt content (not allowed)
        dummy_content = b"Dummy txt content"
        b64_string = base64.b64encode(dummy_content).decode('utf-8')

        path = decode_base64_document(b64_string, "test_doc.txt", "/tmp")

        # Should return None and not create file
        self.assertIsNone(path)
