# encoding: utf-8
# Services go here or (in case of MUCH SERVICE) to services/

from django.db.utils import InterfaceError
from django.db import connection


from smsbank.apps.hive.models import (
    Device,
    Sms,
    DeviceList,
    CallForwarding
)

########################
# Working with Devices #
########################


def device_exists(ip, port):
    """Check if device exists. Return either device or True."""
    try:
        return Device.objects.get(ip=ip, port=port)
    except Device.DoesNotExist:
        return False


def get_or_create_device(ip, port, status=True):
    """Either get existing or create new device."""
    device = device_exists(ip, port)
    if not device:
        device = Device(ip=ip, port=port, online=status)
        device.save()

    return device


def get_device_by_id(device_id):
    """Get device by id"""
    try:
        return Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        return None


def list_sms(device, inbox=False):
    """Get SMS sent from the device"""
    return Sms.objects.filter(device=device, inbox=inbox).order_by('-date')


def delete_sms(id):
    """Delete SMS by id"""
    Sms.objects.filter(id=id).delete()


###########################
# Methods for GOIP Daemon #
###########################


def get_device(device_id):
    """Get device by devid, as provided by GOIP daemon."""
    try:
        return Device.objects.get(device_id=device_id)
    except Device.DoesNotExist:
        return None


def initialize_device(device_id, ip, port, online=True):
    """Get or create device using  devid, as provided by GOIP daemon."""
    device = get_device(device_id)
    if not device:
        device = Device(
            ip=ip,
            port=port,
            device_id=device_id,
            online=online
        )
        # Re-open database connection
        # in case of invalid reference passed in fork
        try:
            device.save()
        except InterfaceError:
            connection.close()
            device.save()

    return device


def update_device_status(device_id, gsm_status):
    """Update device status based on gsm_status"""
    device = get_device(device_id)
    if device:
        device.online = bool(gsm_status)
        device.save()


def new_sms(recipient, message, inbox=False, device_id=None):
    """Create new SMS."""
    sms = Sms(recipient=recipient, message=message, inbox=inbox)
    if device_id:
            device = get_device(device_id)
            if device:
                sms.device = device

    # Try to reopen database connection if something goes wrong
    try:
        sms.save()
    except InterfaceError:
        connection.close()
        sms.save()

    return sms


#########################
# Working with profiles #
#########################

def associate_profiles(user):
    """Create default profiles for new user"""
    # Associate device list
    profile = DeviceList()
    profile.user = user
    profile.save()

    # Also add forwarding profile
    new_call_forwarding_profile(user)

    return user


def new_call_forwarding_profile(user):
    """Associate new call forwarding profile with user"""
    forwarding = CallForwarding()
    forwarding.user = user
    forwarding.save()

    return forwarding
