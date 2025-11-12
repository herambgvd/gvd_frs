"""
Tests for POI (Person of Interest) functionality
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock
import uuid

from apps.poi.models import POICreate, POIUpdate, POIQuery
from apps.poi.controller import POIController


class TestPOIController:
    """Test POI Controller functionality"""
    
    @pytest.fixture
    def mock_db_client(self):
        """Mock database client"""
        mock_client = Mock()
        mock_db = Mock()
        mock_collection = AsyncMock()
        mock_watchlist_collection = AsyncMock()
        
        mock_client.__getitem__.return_value = mock_db
        mock_db.poi_persons = mock_collection
        mock_db.groups = mock_watchlist_collection
        
        return mock_client
    
    @pytest.fixture
    def controller(self, mock_db_client):
        """Create POI controller with mocked dependencies"""
        return POIController(mock_db_client, "test_db")
    
    def test_poi_create_model(self):
        """Test POI creation model validation"""
        # Valid POI data
        poi_data = POICreate(
            full_name="John Doe",
            gender="male",
            age=30,
            additional_info="Test person",
            tagged_watchlist_id="507f1f77bcf86cd799439011",
            organization_id="507f1f77bcf86cd799439012",
            created_by="user123"
        )
        
        assert poi_data.full_name == "John Doe"
        assert poi_data.gender == "male"
        assert poi_data.age == 30
        assert poi_data.additional_info == "Test person"
    
    def test_poi_create_validation(self):
        """Test POI creation validation"""
        # Test invalid age
        with pytest.raises(ValueError):
            POICreate(
                full_name="John Doe",
                gender="male",
                age=150,  # Invalid age
                organization_id="507f1f77bcf86cd799439012",
                created_by="user123"
            )
    
    def test_poi_update_model(self):
        """Test POI update model"""
        update_data = POIUpdate(
            full_name="Jane Doe",
            age=25
        )
        
        assert update_data.full_name == "Jane Doe"
        assert update_data.age == 25
        assert update_data.gender is None  # Optional field
    
    def test_poi_query_model(self):
        """Test POI query parameters"""
        query = POIQuery(
            page=2,
            limit=10,
            search="john",
            gender="male",
            min_age=20,
            max_age=40,
            tagged_watchlist_id="507f1f77bcf86cd799439011",
            organization_id="507f1f77bcf86cd799439012"
        )
        
        assert query.page == 2
        assert query.limit == 10
        assert query.search == "john"
        assert query.gender == "male"
        assert query.min_age == 20
        assert query.max_age == 40
    
    @pytest.mark.asyncio
    async def test_create_poi_success(self, controller):
        """Test successful POI creation"""
        # Mock successful database operations
        controller.watchlist_collection.find_one = AsyncMock(return_value={"_id": "watchlist123"})
        controller.collection.insert_one = AsyncMock(return_value=Mock(acknowledged=True))
        controller.collection.find_one = AsyncMock(return_value={
            "person_id": "person123",
            "full_name": "John Doe",
            "gender": "male",
            "age": 30,
            "organization_id": "org123",
            "created_by": "user123",
            "created_at": datetime.utcnow(),
            "is_active": True
        })
        
        poi_data = POICreate(
            full_name="John Doe",
            gender="male",
            age=30,
            tagged_watchlist_id="watchlist123",
            organization_id="org123",
            created_by="user123"
        )
        
        result = await controller.create_poi(poi_data, "user123")
        
        assert result.full_name == "John Doe"
        assert result.gender == "male"
        assert result.age == 30
    
    @pytest.mark.asyncio
    async def test_create_poi_invalid_watchlist(self, controller):
        """Test POI creation with invalid watchlist"""
        # Mock watchlist not found
        controller.watchlist_collection.find_one = AsyncMock(return_value=None)
        
        poi_data = POICreate(
            full_name="John Doe",
            gender="male",
            age=30,
            tagged_watchlist_id="invalid_watchlist",
            organization_id="org123",
            created_by="user123"
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await controller.create_poi(poi_data, "user123")


def test_sample_poi_data():
    """Test sample POI data structures"""
    sample_poi = {
        "person_id": str(uuid.uuid4()),
        "full_name": "Alice Johnson",
        "gender": "female",
        "age": 28,
        "additional_info": "Marketing Manager",
        "tagged_watchlist_id": None,
        "organization_id": "org_123",
        "created_by": "admin_user",
        "person_image_path": "/uploads/person_profiles/alice_johnson.jpg",
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    assert sample_poi["full_name"] == "Alice Johnson"
    assert sample_poi["gender"] == "female"
    assert sample_poi["age"] == 28
    assert sample_poi["is_active"] is True


def test_poi_search_scenarios():
    """Test different POI search scenarios"""
    # Search by name
    name_query = POIQuery(search="Alice")
    assert name_query.search == "Alice"
    
    # Search by gender and age range
    gender_age_query = POIQuery(
        gender="female",
        min_age=25,
        max_age=35
    )
    assert gender_age_query.gender == "female"
    assert gender_age_query.min_age == 25
    assert gender_age_query.max_age == 35
    
    # Search by watchlist
    watchlist_query = POIQuery(
        tagged_watchlist_id="watchlist_vip"
    )
    assert watchlist_query.tagged_watchlist_id == "watchlist_vip"


if __name__ == "__main__":
    # Run basic tests
    print("Testing POI models...")
    
    # Test POI creation
    poi_create = POICreate(
        full_name="Test User",
        gender="male",
        age=25,
        organization_id="test_org",
        created_by="test_user"
    )
    print(f"✓ POI Create: {poi_create.full_name}")
    
    # Test POI query
    poi_query = POIQuery(
        page=1,
        limit=20,
        search="test",
        gender="male"
    )
    print(f"✓ POI Query: page={poi_query.page}, search='{poi_query.search}'")
    
    print("All tests completed successfully!")
