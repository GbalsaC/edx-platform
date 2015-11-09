"""
Signal handler for invalidating cached course overviews
"""
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler, modulestore

from .models import CourseMode, CourseModeAutoExpirationConfiguration


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    sets the verified mode dates to defaults.
    """
    # TODO: Update if the course end date has changed if mode.expiration_datetime is set to the old date
    course = modulestore().get_course(course_key)
    mode = CourseMode.verified_mode_for_course(course_key)
    if mode is not None and mode.expiration_datetime is None:
        mode.expiration_datetime = course.end - CourseModeAutoExpirationConfiguration.current().verification_window
        mode.save()
