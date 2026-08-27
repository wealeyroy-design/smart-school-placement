from rest_framework import permissions


class IsMinistryAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_ministry_admin)


class IsSchoolAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_school_admin)


class IsMinistryOrSchoolAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_ministry_admin or user.is_school_admin))


class IsSchoolOwnerOrMinistryAdmin(permissions.BasePermission):
    """Object-level: a school_admin may only modify schools they administer;
    a ministry_admin may modify any school."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if user.is_ministry_admin:
            return True
        return user.is_school_admin and obj.administrator_id == user.id


class IsStudentSelfParentOrAdmin(permissions.BasePermission):
    """Object-level access to a Student record: the student themself, their
    linked parent account, a ministry_admin, or the school_admin of the
    school they're currently placed at (read-only for the school_admin
    case -- see the viewset's get_queryset for the school_admin listing)."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_ministry_admin:
            return True
        if obj.user_id == user.id:
            return True
        if obj.parent_id == user.id:
            return True
        if request.method in permissions.SAFE_METHODS and user.is_school_admin:
            placement = getattr(obj, "placement", None)
            return placement is not None and placement.school.administrator_id == user.id
        return False
