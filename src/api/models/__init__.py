"""Database table models.

Importing this package registers all SQLModel table classes with the shared
metadata, which is required before ``SQLModel.metadata.create_all`` is called.
"""

from src.api.models.user import User
from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.conversation import Conversation
from src.api.models.course_document import CourseDocument
from src.api.models.message import Message

__all__ = ["User", "Course", "CourseEnrollment", "Conversation", "CourseDocument", "Message"]
