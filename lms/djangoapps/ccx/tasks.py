"""
Asynchronous tasks for the CCX app.
"""

from django.dispatch import receiver
import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator
from ccx_keys.locator import CCXLocator
from xmodule.modulestore.django import SignalHandler
from lms import CELERY_APP

from .models import CustomCourseForEdX

log = logging.getLogger("edx.ccx")


@receiver(SignalHandler.course_published)
def course_published_handler(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Consume signals that indicate course published. If course already a CCX, do nothing.
    """
    if not isinstance(course_key, CCXLocator):
        send_ccx_course_published.delay(unicode(course_key))


@CELERY_APP.task
def send_ccx_course_published(course_key):
    """
    Find all CCX derived from this course, and send course published event for them.
    """
    course_key = CourseLocator.from_string(course_key)
    for ccx in CustomCourseForEdX.objects.filter(course_id=course_key):
        try:
            ccx_key = CCXLocator.from_course_locator(course_key, ccx.id)
        except InvalidKeyError:
            log.info('Attempt to publish course with deprecated id. Course: %s. CCX: %s', course_key, ccx.id)
            continue
        responses = SignalHandler.course_published.send(
            sender=ccx,
            course_key=ccx_key
        )
        for rec, response in responses:
            log.info('Signal fired when course is published. Receiver: %s. Response: %s', rec, response)
