# openfprintd/polkit.py
from gi.repository import GLib, Gio
import logging

def check_privilege(sender_dbus_name, action_id):
    """
    Checks if the D-Bus sender is authorized for the given PolicyKit action.
    Raises PermissionError if not authorized.
    """
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        
        # Connect to PolicyKit Authority
        authority = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.PolicyKit1",
            "/org/freedesktop/PolicyKit1/Authority",
            "org.freedesktop.PolicyKit1.Authority",
            None,
        )

        # Structure the request: (system-bus-name, {'name': ':1.99'})
        subject = GLib.Variant("(s{ss})", ("system-bus-name", {"name": sender_dbus_name}))
        
        # Call CheckAuthorization
        # (subject, action_id, details, flags, cancellation_id)
        # Flags: 1 = Allow User Interaction (Ask for password if needed)
        result = authority.call_sync(
            "CheckAuthorization",
            GLib.Variant("(sa{ss}is)", (subject, action_id, {}, 1, "")),
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )
        
        # Result: (is_authorized, is_challenge, details)
        (is_auth, _, _) = result.unpack()
        
        if not is_auth:
            logging.warning(f"Polkit denied action '{action_id}' for {sender_dbus_name}")
            raise PermissionError(f"Not authorized for {action_id}")
            
        logging.info(f"Polkit authorized '{action_id}' for {sender_dbus_name}")
        return True

    except Exception as e:
        logging.error(f"Polkit check failed: {e}")
        # Fail closed (deny) if Polkit is broken
        raise PermissionError("Authorization check failed")