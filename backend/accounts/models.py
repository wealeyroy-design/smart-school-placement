"""
Custom user model with roles, per Module 4 of the proposal: role-based web
interfaces for students, parents, school administrators and Ministry
officials, backed by JWT authentication (section 3.4.4).
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    STUDENT = "student", "Student"
    PARENT = "parent", "Parent/Guardian"
    SCHOOL_ADMIN = "school_admin", "School Administrator"
    MINISTRY_ADMIN = "ministry_admin", "Ministry Administrator"


class User(AbstractUser):
    """Extends Django's built-in user with the role field the whole
    system's permission model is built around. Login is by username (kept
    from AbstractUser) with email as a required, unique secondary field."""

    role = models.CharField(max_length=20, choices=Role.choices)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)

    REQUIRED_FIELDS = ["email", "role"]

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_student(self) -> bool:
        return self.role == Role.STUDENT

    @property
    def is_parent(self) -> bool:
        return self.role == Role.PARENT

    @property
    def is_school_admin(self) -> bool:
        return self.role == Role.SCHOOL_ADMIN

    @property
    def is_ministry_admin(self) -> bool:
        return self.role == Role.MINISTRY_ADMIN
