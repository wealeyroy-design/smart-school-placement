from django.core.management.base import BaseCommand

from placements.services import run_placement


class Command(BaseCommand):
    help = "Run the proximity-weighted Gale-Shapley placement algorithm against all students with results on file."

    def add_arguments(self, parser):
        parser.add_argument("--merit-weight", type=float, default=0.6)
        parser.add_argument("--proximity-weight", type=float, default=0.4)
        parser.add_argument("--max-distance-km", type=float, default=300.0)
        parser.add_argument("--max-candidates", type=int, default=15)

    def handle(self, *args, **options):
        run = run_placement(
            merit_weight=options["merit_weight"],
            proximity_weight=options["proximity_weight"],
            max_distance_km=options["max_distance_km"],
            max_candidates=options["max_candidates"],
        )
        if run.status == run.Status.COMPLETED:
            self.stdout.write(self.style.SUCCESS(
                f"Run #{run.pk} completed: {run.students_placed}/{run.students_considered} placed, "
                f"avg distance {run.average_distance_km}km, "
                f"{run.proportion_within_threshold * 100:.1f}% within threshold, "
                f"stable={run.is_stable}"
            ))
        else:
            self.stdout.write(self.style.ERROR(f"Run #{run.pk} failed: {run.error_message}"))
