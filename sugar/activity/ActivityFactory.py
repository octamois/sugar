# Copyright (C) 2006, Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
import sys
import logging

import dbus
import dbus.service
import gobject
import gtk

from sugar.presence.PresenceService import PresenceService
from sugar.activity import bundleregistry
from sugar.activity.bundle import Bundle
from sugar import logger

_ACTIVITY_SERVICE_NAME = "org.laptop.Activity"
_ACTIVITY_SERVICE_PATH = "/org/laptop/Activity"
_ACTIVITY_INTERFACE = "org.laptop.Activity"

def get_path(activity_name):
    """Returns the activity path"""
    return '/' + activity_name.replace('.', '/')

class ActivityFactory(dbus.service.Object):
    """Dbus service that takes care of creating new instances of an activity"""

    def __init__(self, activity_type, activity_class):
        self._activity_type = activity_type
        self._activities = []

        splitted_module = activity_class.rsplit('.', 1)
        module_name = splitted_module[0]
        class_name = splitted_module[1]

        module = __import__(module_name)        
        for comp in module_name.split('.')[1:]:
            module = getattr(module, comp)
        if hasattr(module, 'start'):
            module.start()

        self._module = module
        self._constructor = getattr(module, class_name)
    
        bus = dbus.SessionBus()
        factory = activity_type
        bus_name = dbus.service.BusName(factory, bus = bus) 
        dbus.service.Object.__init__(self, bus_name, get_path(factory))

    @dbus.service.method("com.redhat.Sugar.ActivityFactory")
    def create(self):
        activity = self._constructor()

        self._activities.append(activity)
        activity.connect('destroy', self._activity_destroy_cb)

        return activity.window.xid

    def _activity_destroy_cb(self, activity):
        self._activities.remove(activity)

        if hasattr(self._module, 'stop'):
            self._module.stop()

        if len(self._activities) == 0:
            gtk.main_quit()

class ActivityCreationHandler(gobject.GObject):

    __gsignals__ = {
        'error':       (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE, 
                       ([gobject.TYPE_PYOBJECT])),
        'success':     (gobject.SIGNAL_RUN_FIRST,
                        gobject.TYPE_NONE, 
                       ([gobject.TYPE_PYOBJECT]))
    }

    def __init__(self, service_name):
        gobject.GObject.__init__(self)

        registry = bundleregistry.get_registry()
        bundle = registry.get_bundle(service_name)

        bus = dbus.SessionBus()
        proxy_obj = bus.get_object(service_name, bundle.get_object_path())
        factory = dbus.Interface(proxy_obj, "com.redhat.Sugar.ActivityFactory")

        factory.create(reply_handler=self._reply_handler, error_handler=self._error_handler)

    def _reply_handler(self, xid):
        bus = dbus.SessionBus()
        proxy_obj = bus.get_object(_ACTIVITY_SERVICE_NAME + '%d' % xid,
                                   _ACTIVITY_SERVICE_PATH + "/%s" % xid)
        activity = dbus.Interface(proxy_obj, _ACTIVITY_INTERFACE)
        self.emit('success', activity)

    def _error_handler(self, err):
        logging.debug("Couldn't create activity: %s" % err)
        self.emit('error', err)

def create(service_name):
    """Create a new activity from its name."""
    return ActivityCreationHandler(service_name)

def start_factory(activity_class, bundle_path):
    """Start the activity factory."""
    bundle = Bundle(bundle_path)

    logger.start(bundle.get_name())

    os.environ['SUGAR_BUNDLE_PATH'] = bundle_path
    os.environ['SUGAR_BUNDLE_SERVICE_NAME'] = bundle.get_service_name()
    os.environ['SUGAR_BUNDLE_DEFAULT_TYPE'] = bundle.get_default_type()

    factory = ActivityFactory(bundle.get_service_name(), activity_class)
