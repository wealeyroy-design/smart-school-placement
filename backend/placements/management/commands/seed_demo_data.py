"""
Seeds the database with a runnable demo dataset: a Ministry admin account, a
School admin account, a set of schools (via the algorithm package's
synthetic data generator), and a cohort of student accounts with results
already uploaded -- enough to log in as any role and immediately see
something real, and to run a placement immediately via the API or
`manage.py run_placement`.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from placement_algorithm.data_gen import generate_schools, generate_students

from placements.models import School, Student

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo users, schools and students for local development/demo purposes."

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=300)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--password", type=str, default="demo-pass-1234")
        parser.add_argument(
            "--fast",
            action="store_true",
            help="Hash demo passwords with the fast MD5 hasher instead of PBKDF2 "
            "(seconds rather than ~15 minutes on slow machines). Only safe for "
            "local demo data -- requires the MD5PasswordHasher fallback in "
            "config/settings.py, which is already present for this project.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        n_students = options["students"]
        seed = options["seed"]
        password = options["password"]

        if options["fast"]:
            from django.conf import settings

            settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

        ministry_admin, created = User.objects.get_or_create(
            username="ministry_admin",
            defaults=dict(
                email="ministry_admin@example.com",
                role="ministry_admin",
                is_staff=True,
                is_superuser=True,  # grants full access to Django admin (/admin/) in addition to the portal
            ),
        )
        if created:
            ministry_admin.set_password(password)
            ministry_admin.save()
            self.stdout.write(self.style.SUCCESS(f"Created ministry_admin / {password}"))

        school_admin, created = User.objects.get_or_create(
            username="school_admin",
            defaults=dict(email="school_admin@example.com", role="school_admin"),
        )
        if created:
            school_admin.set_password(password)
            school_admin.save()
            self.stdout.write(self.style.SUCCESS(f"Created school_admin / {password}"))

        if not School.objects.exists():
            algo_schools = generate_schools(seed=seed)
            schools = [
                School(
                    name=s.name,
                    category=s.category.value,
                    county=s.county,
                    latitude=s.location.lat,
                    longitude=s.location.lon,
                    capacity=s.capacity,
                    performance_rating=s.performance_rating,
                    administrator=school_admin,
                )
                for s in algo_schools
            ]
            School.objects.bulk_create(schools)
            self.stdout.write(self.style.SUCCESS(f"Created {len(schools)} schools"))
        else:
            self.stdout.write("Schools already exist, skipping.")

        existing_students = Student.objects.count()
        if existing_students == 0:
            algo_students = generate_students(n_students, seed=seed)
            for i, s in enumerate(algo_students):
                username = f"student{i+1:04d}"
                user = User.objects.create(
                    username=username,
                    email=f"{username}@example.com",
                    role="student",
                    first_name=f"Student{i+1:04d}",
                )
                user.set_password(password)
                user.save()
                Student.objects.create(
                    user=user,
                    county=s.county,
                    home_latitude=s.home.lat,
                    home_longitude=s.home.lon,
                    exam_score=s.exam_score,
                    results_uploaded_by=ministry_admin,
                )
            self.stdout.write(self.style.SUCCESS(
                f"Created {len(algo_students)} students (usernames student0001.. / password: {password})"
            ))
        else:
            self.stdout.write("Students already exist, skipping.")

        self.stdout.write(self.style.SUCCESS(
            "\nDemo accounts:\n"
            f"  ministry_admin / {password}\n"
            f"  school_admin   / {password}\n"
            f"  student0001..student{n_students:04d} / {password}\n"
            "\nRun `python3 manage.py run_placement` (or trigger it from the Ministry Admin "
            "portal) to generate placements."
        ))
