"""
Security utilities for file upload validation and other security features.
"""
import os
from django.core.exceptions import ValidationError
from django.conf import settings

# Try to import python-magic, but make it optional
try:
    import magic
    MAGIC_AVAILABLE = True
except (ImportError, OSError):
    MAGIC_AVAILABLE = False


# Allowed file types for different upload contexts
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/webp': ['.webp']
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png']
}

# Maximum file sizes (in bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_file_size(file, max_size):
    """
    Validate that file size does not exceed the maximum allowed size.
    
    Args:
        file: UploadedFile object
        max_size: Maximum size in bytes
        
    Raises:
        ValidationError: If file size exceeds max_size
    """
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(
            f'File size exceeds maximum allowed size of {max_size_mb:.1f} MB'
        )


def validate_file_extension(file, allowed_types):
    """
    Validate that file extension matches one of the allowed types.
    
    Args:
        file: UploadedFile object
        allowed_types: Dictionary mapping MIME types to allowed extensions
        
    Raises:
        ValidationError: If file extension is not allowed
    """
    ext = os.path.splitext(file.name)[1].lower()
    allowed_extensions = []
    for extensions in allowed_types.values():
        allowed_extensions.extend(extensions)
    
    if ext not in allowed_extensions:
        raise ValidationError(
            f'File extension "{ext}" is not allowed. '
            f'Allowed extensions: {", ".join(allowed_extensions)}'
        )


def validate_file_mime_type(file, allowed_types):
    """
    Validate file MIME type by reading file content (not just extension).
    This prevents users from uploading malicious files with fake extensions.
    
    Args:
        file: UploadedFile object
        allowed_types: Dictionary mapping MIME types to allowed extensions
        
    Raises:
        ValidationError: If MIME type doesn't match allowed types
    """
    # Read first 2048 bytes to determine MIME type
    file.seek(0)
    file_head = file.read(2048)
    file.seek(0)
    
    # Try to use python-magic if available, otherwise fallback to content_type
    if MAGIC_AVAILABLE:
        try:
            mime = magic.from_buffer(file_head, mime=True)
        except Exception:
            mime = file.content_type
    else:
        # Fallback to content_type if python-magic is not available
        mime = file.content_type
    
    if mime not in allowed_types:
        raise ValidationError(
            f'File type "{mime}" is not allowed. '
            f'Allowed types: {", ".join(allowed_types.keys())}'
        )
    
    # Also validate extension matches MIME type
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_types[mime]:
        raise ValidationError(
            f'File extension "{ext}" does not match file type "{mime}"'
        )


def validate_image_file(file):
    """
    Comprehensive validation for image uploads.
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: If validation fails
    """
    validate_file_size(file, MAX_IMAGE_SIZE)
    validate_file_extension(file, ALLOWED_IMAGE_TYPES)
    validate_file_mime_type(file, ALLOWED_IMAGE_TYPES)
    
    # Additional validation: try to open with PIL to ensure it's a valid image
    try:
        from PIL import Image
        file.seek(0)
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception as e:
        raise ValidationError(f'Invalid image file: {str(e)}')


def validate_document_file(file):
    """
    Comprehensive validation for document uploads (inquiries, etc.).
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: If validation fails
    """
    validate_file_size(file, MAX_DOCUMENT_SIZE)
    validate_file_extension(file, ALLOWED_DOCUMENT_TYPES)
    validate_file_mime_type(file, ALLOWED_DOCUMENT_TYPES)


def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and other attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    import re
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext
