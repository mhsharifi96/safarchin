import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def generate_itinerary_task(self, trip_id: str, job_id: int):
    from apps.trips.models import PlanningJob, Trip

    from .orchestrator import generate_itinerary

    job = PlanningJob.objects.get(pk=job_id)
    trip = Trip.objects.get(pk=trip_id)
    job.status = PlanningJob.Status.RUNNING
    job.save(update_fields=["status"])

    try:
        generate_itinerary(trip)
    except Exception as exc:  # noqa: BLE001 - persist the failure instead of losing it
        logger.exception("Itinerary generation failed for trip %s", trip_id)
        job.status = PlanningJob.Status.FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message"])
        trip.status = Trip.Status.READY_FOR_GENERATION
        trip.save(update_fields=["status"])
        raise
    else:
        job.status = PlanningJob.Status.SUCCEEDED
        job.save(update_fields=["status"])
        trip.status = Trip.Status.PLANNED
        trip.save(update_fields=["status"])
