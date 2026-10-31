"""
Seeds the database with a runnable demo dataset: a Ministry admin account, a
School admin account, a set of schools (via the algorithm package's
synthetic data generator), and a cohort of student accounts with results
already uploaded -- enough to log in as any role and immediately see
something real, and to run a placement immediately via the API or
`manage.py run_placement`.
"""

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from placement_algorithm.data_gen import generate_schools, generate_students

from placements.models import Appeal, School, Student

User = get_user_model()

# Synthetic but realistic-looking names, so demo screens and screenshots read
# like a real cohort. These are generated combinations, not real people.
FIRST_NAMES = [
    "Brian", "Faith", "Kevin", "Mercy", "Dennis", "Joy", "Collins", "Sharon", "Victor", "Grace",
    "Ian", "Esther", "Kelvin", "Purity", "Emmanuel", "Cynthia", "Felix", "Ann", "Hillary", "Diana",
    "Allan", "Winnie", "Edwin", "Naomi", "Samuel", "Lydia", "Kipchumba", "Chebet", "Otieno", "Achieng",
    "Mutua", "Wanjiru", "Kamau", "Njeri", "Omondi", "Atieno", "Kiprono", "Jepkosgei", "Wafula", "Nafula",
]
LAST_NAMES = [
    "Kiptoo", "Wanjiku", "Odhiambo", "Mwangi", "Cheruiyot", "Njoroge", "Ochieng", "Kariuki", "Rotich", "Mutiso",
    "Owino", "Kimani", "Langat", "Wambui", "Barasa", "Koech", "Nyambura", "Onyango", "Kirui", "Muthoni",
    "Wekesa", "Kosgei", "Gitau", "Akinyi", "Juma", "Hassan", "Mohamed", "Ekiru", "Lokwang", "Mumbua",
]

SAMPLE_APPEALS = [
    ("The placed school is far from home and the daily commute is not affordable for our family.", "pending", ""),
    ("I would like a school closer to home because I help care for younger siblings after school.", "pending", ""),
    ("Requesting a day school near home for medical follow-up reasons.", "under_review", ""),
    ("Placed school is in a different county; requesting a nearer school with available slots.", "approved",
     "Approved: a nearer school with available capacity was identified."),
    ("Requesting a transfer to a national school.", "rejected",
     "Rejected: placement follows the combined merit and proximity score; no qualifying slot was available."),
]


class Command(BaseCommand):
    help = "Seed the database with demo users, schools and students for local development/demo purposes."

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=600)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument(
            "--capacity-ratio",
            type=float,
            default=1.5,
            help="Scale school capacities so total slots are about this multiple of the student cohort "
            "(the generator's capacities are national-scale; a small demo cohort would otherwise fill only "
            "a few percent of them). Use 0 to keep the generator's capacities unchanged.",
        )
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
            ratio = options["capacity_ratio"]
            if ratio > 0:
                total = sum(s.capacity for s in algo_schools) or 1
                factor = ratio * n_students / total
                for s in algo_schools:
                    s.capacity = max(2, round(s.capacity * factor))
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
            rng = random.Random(seed)
            for i, s in enumerate(algo_students):
                username = f"student{i+1:04d}"
                user = User.objects.create(
                    username=username,
                    email=f"{username}@example.com",
                    role="student",
                    first_name=rng.choice(FIRST_NAMES),
                    last_name=rng.choice(LAST_NAMES),
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

        # A parent/guardian account linked to two children (Module 4's parent view).
        parent, created = User.objects.get_or_create(
            username="parent_demo",
            defaults=dict(email="parent_demo@example.com", role="parent", first_name="Jane", last_name="Wanjiku"),
        )
        # Always (re)apply the demo password, role and child links, so re-running the
        # seed repairs a parent_demo account that already exists with a stale password.
        parent.role = "parent"
        parent.is_active = True
        parent.set_password(password)
        parent.save()
        Student.objects.filter(user__username__in=["student0002", "student0003"]).update(parent=parent)
        verb = "Created" if created else "Reset"
        self.stdout.write(self.style.SUCCESS(f"{verb} parent_demo / {password} (linked to student0002, student0003)"))

        # A handful of appeals in different states, so the appeals workflow has data to show.
        if not Appeal.objects.exists():
            students = list(Student.objects.order_by("id")[: len(SAMPLE_APPEALS)])
            for student, (reason, status, notes) in zip(students, SAMPLE_APPEALS):
                Appeal.objects.create(
                    student=student,
                    submitted_by=student.parent or student.user,
                    reason=reason,
                    status=status,
                    resolution_notes=notes,
                    resolved_by=ministry_admin if status in ("approved", "rejected") else None,
                    resolved_at=timezone.now() if status in ("approved", "rejected") else None,
                )
            self.stdout.write(self.style.SUCCESS(f"Created {len(students)} sample appeals"))

        self.stdout.write(self.style.SUCCESS(
            "\nDemo accounts:\n"
            f"  ministry_admin / {password}\n"
            f"  school_admin   / {password}\n"
            f"  parent_demo    / {password}\n"
            f"  student0001..student{n_students:04d} / {password}\n"
            "\nRun `python3 manage.py run_placement` (or trigger it from the Ministry Admin "
            "portal) to generate placements."
        ))
