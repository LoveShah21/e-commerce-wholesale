"""
Tests for security utilities.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from utils.security import (
    validate_file_size,
    validate_file_extension,
    sanitize_filename,
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_SIZE
)


class FileValidationTests(TestCase):
    """Test file validation functions."""
    
    def test_validate_file_size_valid(self):
        """Test that valid file size passes validation."""
        # Create a small file (1 KB)
        file = SimpleUploadedFile("test.jpg", b"x" * 1024, content_type="image/jpeg")
        
        # Should not raise exception
        try:
            validate_file_size(file, MAX_IMAGE_SIZE)
        except ValidationError:
            self.fail("validate_file_size raised ValidationError unexpectedly")
    
    def test_validate_file_size_too_large(self):
        """Test that oversized file fails validation."""
        # Create a file larger than max size
        file = SimpleUploadedFile("test.jpg", b"x" * (MAX_IMAGE_SIZE + 1), content_type="image/jpeg")
        
        # Should raise ValidationError
        with self.assertRaises(ValidationError):
            validate_file_size(file, MAX_IMAGE_SIZE)
    
    def test_validate_file_extension_valid(self):
        """Test that valid file extension passes validation."""
        file = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        
        # Should not raise exception
        try:
            validate_file_extension(file, ALLOWED_IMAGE_TYPES)
        except ValidationError:
            self.fail("validate_file_extension raised ValidationError unexpectedly")
    
    def test_validate_file_extension_invalid(self):
        """Test that invalid file extension fails validation."""
        file = SimpleUploadedFile("test.exe", b"content", content_type="application/x-msdownload")
        
        # Should raise ValidationError
        with self.assertRaises(ValidationError):
            validate_file_extension(file, ALLOWED_IMAGE_TYPES)
    
    def test_sanitize_filename_removes_path(self):
        """Test that path components are removed from filename."""
        filename = "../../etc/passwd.txt"
        sanitized = sanitize_filename(filename)
        
        self.assertNotIn("..", sanitized)
        self.assertNotIn("/", sanitized)
    
    def test_sanitize_filename_removes_special_chars(self):
        """Test that special characters are removed."""
        filename = "test<>file|name?.txt"
        sanitized = sanitize_filename(filename)
        
        # Should only contain alphanumeric, dots, dashes, underscores
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertNotIn("|", sanitized)
        self.assertNotIn("?", sanitized)
    
    def test_sanitize_filename_replaces_spaces(self):
        """Test that spaces are replaced with underscores."""
        filename = "test file name.txt"
        sanitized = sanitize_filename(filename)
        
        self.assertNotIn(" ", sanitized)
        self.assertIn("_", sanitized)
    
    def test_sanitize_filename_limits_length(self):
        """Test that filename length is limited."""
        filename = "a" * 200 + ".txt"
        sanitized = sanitize_filename(filename)
        
        # Should be limited to 100 chars + extension
        self.assertLessEqual(len(sanitized), 104)  # 100 + ".txt"


class SecurityHeadersTests(TestCase):
    """Test security headers middleware."""
    
    def test_security_headers_present(self):
        """Test that security headers are added to responses."""
        response = self.client.get('/')
        
        # Check for security headers
        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        
        self.assertIn('X-XSS-Protection', response)
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
        
        self.assertIn('Referrer-Policy', response)
        self.assertEqual(response['Referrer-Policy'], 'strict-origin-when-cross-origin')
