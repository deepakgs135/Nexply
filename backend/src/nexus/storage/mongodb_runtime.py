
from datetime import datetime, timezone
import hashlib
from uuid import UUID

from nexus.core.debug import debug_trace

from bson import ObjectId
from gridfs import GridFSBucket
from pymongo.errors import DuplicateKeyError
from pymongo import MongoClient

from nexus.core.config import (
    MONGODB_DATABASE,
    MONGODB_GRIDFS_BUCKET,
    MONGODB_JD_COLLECTION,
    MONGODB_RESUME_COLLECTION,
    MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    MONGODB_URI,
)


client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
)

db = client[MONGODB_DATABASE]

# Main application collections
resumes = db[MONGODB_RESUME_COLLECTION]
job_descriptions = db[MONGODB_JD_COLLECTION]

# Original uploaded files
file_bucket = GridFSBucket(
    db,
    bucket_name=MONGODB_GRIDFS_BUCKET,
)


