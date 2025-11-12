"""
Utility functions for POI management
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from PIL import Image
import io


class ImageProcessor:
    """Utility class for image processing operations"""
    
    SUPPORTED_FORMATS = ['jpeg', 'jpg', 'png', 'gif', 'webp']
    MAX_IMAGE_SIZE = (1024, 1024)  # Max dimensions
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def validate_image_file(cls, file_content: bytes, filename: str) -> bool:
        """Validate image file format and size"""
        # Check file size
        if len(file_content) > cls.MAX_FILE_SIZE:
            return False
            
        # Check file extension
        extension = filename.lower().split('.')[-1]
        if extension not in cls.SUPPORTED_FORMATS:
            return False
            
        try:
            # Try to open image to validate format
            image = Image.open(io.BytesIO(file_content))
            image.verify()
            return True
        except Exception:
            return False
    
    @classmethod
    def resize_image(cls, file_content: bytes, max_size: Tuple[int, int] = None) -> bytes:
        """Resize image while maintaining aspect ratio"""
        if max_size is None:
            max_size = cls.MAX_IMAGE_SIZE
            
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
                image = background
            
            # Resize image
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")


class FileUtils:
    """File management utilities"""
    
    @staticmethod
    def generate_unique_filename(original_filename: str, person_id: str = None) -> str:
        """Generate unique filename for uploaded files"""
        extension = original_filename.lower().split('.')[-1]
        unique_id = str(uuid.uuid4())
        
        if person_id:
            return f"{person_id}_{unique_id}.{extension}"
        return f"{unique_id}.{extension}"
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> None:
        """Ensure directory exists, create if not"""
        os.makedirs(directory_path, exist_ok=True)
    
    @staticmethod
    def safe_delete_file(file_path: str) -> bool:
        """Safely delete file, return success status"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0


class ValidationUtils:
    """Data validation utilities"""
    
    @staticmethod
    def validate_person_id(person_id: str) -> bool:
        """Validate person ID format (UUID)"""
        try:
            uuid.UUID(person_id)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_age(age: int) -> bool:
        """Validate age range"""
        return 0 <= age <= 120
    
    @staticmethod
    def validate_gender(gender: str) -> bool:
        """Validate gender value"""
        return gender.lower() in ['male', 'female', 'other']
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace dangerous characters
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
            
        return filename
    
    @staticmethod
    def validate_search_params(search: str) -> str:
        """Validate and sanitize search parameters"""
        if not search:
            return ""
        
        # Remove excessive whitespace and limit length
        search = search.strip()[:100]
        
        # Basic SQL injection protection (for MongoDB regex)
        dangerous_patterns = ['$', '{', '}', '[', ']', '(', ')', '^', '|']
        for pattern in dangerous_patterns:
            search = search.replace(pattern, '')
        
        return search


class DatabaseUtils:
    """Database operation utilities"""
    
    @staticmethod
    def build_search_regex(search_term: str, case_insensitive: bool = True) -> dict:
        """Build MongoDB regex query for search"""
        if not search_term:
            return {}
        
        options = "i" if case_insensitive else ""
        escaped_term = ValidationUtils.validate_search_params(search_term)
        
        return {"$regex": escaped_term, "$options": options}
    
    @staticmethod
    def build_age_filter(min_age: Optional[int], max_age: Optional[int]) -> dict:
        """Build age range filter"""
        age_filter = {}
        
        if min_age is not None:
            age_filter["$gte"] = min_age
        if max_age is not None:
            age_filter["$lte"] = max_age
            
        return age_filter
    
    @staticmethod
    def calculate_skip_limit(page: int, limit: int) -> Tuple[int, int]:
        """Calculate skip and limit values for pagination"""
        page = max(1, page)  # Ensure page is at least 1
        limit = min(max(1, limit), 100)  # Ensure limit is between 1-100
        skip = (page - 1) * limit
        
        return skip, limit
    
    @staticmethod
    def calculate_total_pages(total_count: int, limit: int) -> int:
        """Calculate total pages for pagination"""
        return (total_count + limit - 1) // limit if total_count > 0 else 1


class AuditUtils:
    """Audit and logging utilities"""
    
    @staticmethod
    def create_audit_entry(
        action: str,
        person_id: str,
        user_id: str,
        organization_id: str,
        details: Optional[dict] = None
    ) -> dict:
        """Create audit log entry"""
        return {
            "action": action,
            "person_id": person_id,
            "user_id": user_id,
            "organization_id": organization_id,
            "details": details or {},
            "timestamp": datetime.utcnow(),
            "ip_address": None,  # To be filled by middleware
            "user_agent": None   # To be filled by middleware
        }
    
    @staticmethod
    def create_change_log(old_data: dict, new_data: dict) -> dict:
        """Create change log showing what fields were modified"""
        changes = {}
        
        # Check for changed fields
        for key, new_value in new_data.items():
            old_value = old_data.get(key)
            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value
                }
        
        return changes
