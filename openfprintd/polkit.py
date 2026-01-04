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

        # 1. Prepare the Subject struct: (sa{sv})
        # Structure: ("system-bus-name", {"name": <Variant('s', sender_name)>})
        subject_value = (
            "system-bus-name", 
            {"name": GLib.Variant("s", sender_dbus_name)}
        )

        # 2. Structure the full request parameters
        # Signature: ((sa{sv})sa{ss}us)
        # Means: (SubjectStruct, action_id, details_dict, flags, cancellation_id)
        # Flags: 1 = Allow User Interaction
        parameters = GLib.Variant(
            "((sa{sv})sa{ss}us)",
            (
                subject_value,
                action_id,
                {},  # details (empty dict)
                1,   # flags (unsigned int 32)
                ""   # cancellation_id (empty string)
            )
        )
        
        # 3. Call CheckAuthorization
        result = authority.call_sync(
            "CheckAuthorization",
            parameters,
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )
        
        # 4. Unpack the result
        # The result variant wraps a tuple containing the return struct.
        # We unpack() once to get the tuple, then take the first element (the struct).
        result_tuple = result.unpack()
        struct_val = result_tuple[0]
        
        # The struct contains (is_authorized, is_challenge, details)
        (is_auth, _, _) = struct_val
        
        if not is_auth:
            logging.warning(f"Polkit denied action '{action_id}' for {sender_dbus_name}")
            raise PermissionError(f"Not authorized for {action_id}")
            
        logging.info(f"Polkit authorized '{action_id}' for {sender_dbus_name}")
        return True

    except Exception as e:
        logging.error(f"Polkit check failed: {e}")
        # Fail closed (deny) if Polkit is broken or error occurs
        raise PermissionError("Authorization check failed")
