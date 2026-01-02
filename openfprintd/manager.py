
import dbus.service
import logging
from openfprintd.device import Device
from openfprintd.polkit import check_privilege # <--- IMPORT THIS

INTERFACE_NAME = 'net.reactivated.Fprint.Manager'

class NoSuchDevice(dbus.DBusException):
    _dbus_error_name = 'net.reactivated.Fprint.Error.NoSuchDevice'

class Manager(dbus.service.Object):
    def __init__(self, bus_name):
        dbus.service.Object.__init__(self, bus_name, '/net/reactivated/Fprint/Manager')
        self.bus_name = bus_name
        self.devices = {}

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='', 
                         out_signature='ao',
                         connection_keyword='connection',
                         sender_keyword='sender')
    def GetDevices(self, sender, connection):
        logging.debug("GetDevices")
        return self.devices.values()

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='', 
                         out_signature='o',
                         connection_keyword='connection',
                         sender_keyword='sender')
    def GetDefaultDevice(self, sender, connection):
        logging.debug("GetDefaultDevice")

        if len(self.devices) == 0:
            logging.debug('no devices')
            raise NoSuchDevice()

        v = list(self.devices.values())
        logging.debug('returning %s' % repr(v[0]))

        return v[0]

    # TODO: use a different interface name for this
    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='o', 
                         out_signature='',
                         connection_keyword='connection',
                         sender_keyword='sender')
    def RegisterDevice(self, dev, sender, connection):
        # 1. FIX THE TODO: Enforce Root-only or specific privilege
        # Using a custom action string, or checking if UID is 0 (root).
        # Polkit is cleaner. Let's use a generic 'register' action.
        check_privilege(sender, "net.reactivated.fprint.manager.register")
        
        logging.debug('RegisterDevice %s %s' % (sender, repr(dev)))

        if dev not in self.devices:
            self.devices[dev] = Device(self)

        wrap = self.devices[dev]
        wrap.set_target(dev, sender)
        
    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='', 
                         out_signature='',
                         connection_keyword='connection',
                         sender_keyword='sender')
    def Suspend(self, sender, connection):
        logging.debug('Suspend')

        for dev in self.devices.values():
            dev.Suspend()

        logging.debug('Suspend complete')

    @dbus.service.method(dbus_interface=INTERFACE_NAME,
                         in_signature='', 
                         out_signature='',
                         connection_keyword='connection',
                         sender_keyword='sender')
    def Resume(self, sender, connection):
        logging.debug('Resume')

        for dev in self.devices.values():
            dev.Resume()

        logging.debug('Resume complete')
