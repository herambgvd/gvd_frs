"""
MongoDB Database Configuration and Connection Management
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class Database:
    """MongoDB Database Manager"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.database = None
    
    async def connect(self):
        """Connect to MongoDB database"""
        try:
            # Create MongoDB client
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            
            # Get database
            self.database = self.client[settings.DATABASE_NAME]
            
            logger.info(f"Successfully connected to MongoDB database: {settings.DATABASE_NAME}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise e
    
    async def close(self):
        """Close database connection"""
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def get_collection(self, collection_name: str):
        """Get collection from database"""
        if self.database is None:
            raise Exception("Database not connected")
        return self.database[collection_name]


# Global database instance
database = Database()


async def connect_to_mongodb():
    """Connect to MongoDB on application startup"""
    await database.connect()


async def close_mongodb_connection():
    """Close MongoDB connection on application shutdown"""
    await database.close()


def get_database():
    """Get database instance"""
    return database.database


def get_collection(collection_name: str):
    """Get collection by name"""
    return database.get_collection(collection_name)