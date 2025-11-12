"""
Test file for Groups CRUD functionality using Controller pattern
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

from apps.groups.models import GroupCreate, GroupUpdate
from apps.groups.controller import get_group_controller


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return {
        "userId": "60d5ecb54b24d67c4e8b4567",
        "userType": "organization_admin",
        "organizationId": {"id": "60d5ecb54b24d67c4e8b4566"},
        "email": "admin@test.com"
    }


@pytest.fixture
def super_admin_user():
    """Sample super admin user for testing"""
    return {
        "userId": "60d5ecb54b24d67c4e8b4568",
        "userType": "super_admin",
        "email": "superadmin@test.com"
    }


@pytest.fixture
def sample_group_create():
    """Sample group creation data"""
    return GroupCreate(
        group_name="Test Security Group",
        display_color="#FF5733",
        sound_on_alert=True,
        watchlist_type="blacklist",
        notes="Test group for security purposes",
        organization_id="60d5ecb54b24d67c4e8b4566",
        created_by="60d5ecb54b24d67c4e8b4567"
    )


@pytest.fixture
def sample_group_update():
    """Sample group update data"""
    return GroupUpdate(
        group_name="Updated Security Group",
        display_color="#33C3FF",
        sound_on_alert=False,
        notes="Updated test group"
    )


@pytest.fixture
def mock_group_document():
    """Mock group document from database"""
    return {
        "_id": "60d5ecb54b24d67c4e8b4569",
        "group_name": "Test Security Group",
        "display_color": "#FF5733", 
        "sound_on_alert": True,
        "watchlist_type": "blacklist",
        "notes": "Test group for security purposes",
        "organization_id": "60d5ecb54b24d67c4e8b4566",
        "created_by": "60d5ecb54b24d67c4e8b4567",
        "created_at": "2025-11-10T00:00:00Z",
        "updated_at": "2025-11-10T00:00:00Z",
        "is_active": True
    }


class TestGroupController:
    """Test class for Group controller methods"""
    
    @pytest.mark.asyncio
    async def test_create_group_success(self, sample_group_create, sample_user, mock_group_document):
        """Test successful group creation"""
        with patch('apps.groups.controller.GroupController._groups_collection') as mock_collection:
            # Setup mocks
            mock_collection.find_one = AsyncMock(return_value=None)  # No existing group
            mock_collection.insert_one = AsyncMock(return_value=MagicMock(
                inserted_id="60d5ecb54b24d67c4e8b4569"
            ))
            
            # Mock the find_one call to return the created group
            mock_collection.find_one.side_effect = [None, mock_group_document]
            
            # Test group creation
            result = await get_group_controller().create_group(sample_group_create, sample_user)
            
            # Assertions
            assert result is not None
            assert result.group_name == "Test Security Group"
            assert result.watchlist_type == "blacklist"
            assert mock_collection.find_one.call_count >= 1
            mock_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_group_permission_denied(self, sample_group_create):
        """Test group creation with insufficient permissions"""
        regular_user = {
            "userId": "60d5ecb54b24d67c4e8b4567",
            "userType": "organization_user",  # Not admin
            "organizationId": {"id": "60d5ecb54b24d67c4e8b4566"}
        }
        
        # Test should raise PermissionError
        with pytest.raises(PermissionError):
            await get_group_controller().create_group(sample_group_create, regular_user)
    
    @pytest.mark.asyncio
    async def test_get_group_by_id_success(self, sample_user, mock_group_document):
        """Test successful group retrieval by ID"""
        group_id = "60d5ecb54b24d67c4e8b4569"
        
        with patch('apps.groups.controller.GroupController._groups_collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=mock_group_document)
            
            # Test group retrieval
            result = await get_group_controller().get_group_by_id(group_id, sample_user)
            
            # Assertions
            assert result is not None
            assert result.group_name == "Test Security Group"
            mock_collection.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_group_by_id_not_found(self, sample_user):
        """Test group retrieval when group doesn't exist"""
        group_id = "60d5ecb54b24d67c4e8b4569"
        
        with patch('apps.groups.controller.GroupController._groups_collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=None)
            
            # Test group retrieval
            result = await get_group_controller().get_group_by_id(group_id, sample_user)
            
            # Assertions
            assert result is None
            mock_collection.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_group_success(self, sample_group_update, sample_user, mock_group_document):
        """Test successful group update"""
        group_id = "60d5ecb54b24d67c4e8b4569"
        updated_document = {**mock_group_document, "group_name": "Updated Security Group"}
        
        with patch('apps.groups.controller.GroupController._groups_collection') as mock_collection:
            mock_collection.find_one.side_effect = [mock_group_document, None, updated_document]
            mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
            
            # Test group update
            result = await get_group_controller().update_group(group_id, sample_group_update, sample_user)
            
            # Assertions
            assert result is not None
            assert result.group_name == "Updated Security Group"
            mock_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_group_success(self, sample_user, mock_group_document):
        """Test successful group deletion (soft delete)"""
        group_id = "60d5ecb54b24d67c4e8b4569"
        
        with patch('apps.groups.controller.GroupController._groups_collection') as mock_collection:
            mock_collection.find_one = AsyncMock(return_value=mock_group_document)
            mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
            
            # Test group deletion
            result = await get_group_controller().delete_group(group_id, sample_user)
            
            # Assertions
            assert result is True
            mock_collection.find_one.assert_called_once()
            mock_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_groups_with_pagination(self, sample_user):
        """Test getting groups with pagination"""
        from apps.groups.models import GroupQuery
        
        query = GroupQuery(page=1, limit=20)
        
        with patch('apps.groups.controller.GroupController._groups_collection') as mock_collection:
            # Mock empty results for simplicity
            mock_cursor = MagicMock()
            mock_cursor.skip.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.to_list = AsyncMock(return_value=[])
            
            mock_collection.find.return_value = mock_cursor
            mock_collection.count_documents = AsyncMock(return_value=0)
            
            # Test getting groups
            result = await get_group_controller().get_groups(query, sample_user)
            
            # Assertions
            assert result is not None
            assert result.total_count == 0
            assert result.groups == []
            mock_collection.find.assert_called_once()
            mock_collection.count_documents.assert_called_once()


class TestGroupModels:
    """Test class for Group model validation"""
    
    def test_group_create_valid_data(self):
        """Test GroupCreate with valid data"""
        group_data = GroupCreate(
            group_name="Test Group",
            display_color="#FF5733",
            sound_on_alert=True,
            watchlist_type="whitelist",
            notes="Test notes",
            organization_id="60d5ecb54b24d67c4e8b4566",
            created_by="60d5ecb54b24d67c4e8b4567"
        )
        
        assert group_data.group_name == "Test Group"
        assert group_data.display_color == "#FF5733"
        assert group_data.watchlist_type == "whitelist"
    
    def test_group_create_invalid_color(self):
        """Test GroupCreate with invalid color format"""
        with pytest.raises(ValueError):
            GroupCreate(
                group_name="Test Group",
                display_color="invalid-color",  # Invalid format
                sound_on_alert=True,
                watchlist_type="whitelist",
                organization_id="60d5ecb54b24d67c4e8b4566",
                created_by="60d5ecb54b24d67c4e8b4567"
            )
    
    def test_group_create_invalid_watchlist_type(self):
        """Test GroupCreate with invalid watchlist type"""
        with pytest.raises(ValueError):
            GroupCreate(
                group_name="Test Group",
                display_color="#FF5733",
                sound_on_alert=True,
                watchlist_type="invalid",  # Invalid type
                organization_id="60d5ecb54b24d67c4e8b4566",
                created_by="60d5ecb54b24d67c4e8b4567"
            )
    
    def test_group_update_optional_fields(self):
        """Test GroupUpdate with only some fields provided"""
        group_data = GroupUpdate(
            group_name="Updated Name",
            sound_on_alert=False
        )
        
        assert group_data.group_name == "Updated Name"
        assert group_data.sound_on_alert is False
        assert group_data.display_color is None
        assert group_data.notes is None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__])