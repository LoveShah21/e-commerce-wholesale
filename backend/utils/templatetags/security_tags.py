"""
Template tags for security-related functionality.
"""
from django import template
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
import bleach

register = template.Library()


@register.filter(name='sanitize_html')
def sanitize_html(value):
    """
    Sanitize HTML content to prevent XSS attacks.
    Allows only safe HTML tags and attributes.
    
    Usage: {{ user_content|sanitize_html }}
    """
    if not value:
        return ''
    
    # Allowed tags and attributes
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title'],
    }
    
    # Clean the HTML
    cleaned = bleach.clean(
        value,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return mark_safe(cleaned)


@register.filter(name='escape_js')
def escape_js(value):
    """
    Escape a string for safe use in JavaScript.
    
    Usage: {{ user_input|escape_js }}
    """
    if not value:
        return ''
    
    # Escape special characters for JavaScript
    value = str(value)
    value = value.replace('\\', '\\\\')
    value = value.replace('"', '\\"')
    value = value.replace("'", "\\'")
    value = value.replace('\n', '\\n')
    value = value.replace('\r', '\\r')
    value = value.replace('\t', '\\t')
    value = value.replace('<', '\\x3C')
    value = value.replace('>', '\\x3E')
    
    return value


@register.filter(name='safe_url')
def safe_url(value):
    """
    Validate and sanitize URLs to prevent javascript: and data: URLs.
    
    Usage: {{ user_url|safe_url }}
    """
    if not value:
        return ''
    
    value = str(value).strip()
    
    # Block dangerous URL schemes
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
    value_lower = value.lower()
    
    for scheme in dangerous_schemes:
        if value_lower.startswith(scheme):
            return ''
    
    return value
