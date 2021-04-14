"""
RESTful interface to current playout
====================================
"""
from datetime import datetime

import pkg_resources
from showergel.showergel_bottle import ShowergelBottle

from showergel.liquidsoap_connector import Connection

live_app = ShowergelBottle()

@live_app.get("/live")
def get_live():
    """
    The returned JSON object might contain many more fields, depending on what's
    in the current track's metadata. You can reasonably expect ``title`` and ``artist``.

    :>json source: name of the currently playing source
    :>json on_air: current track start time
    :>json status: status of the current source ("playing" or "connected to ...")
    :>json server_time: server's datetime
    """
    metadata = Connection.get().current()
    metadata["server_time"] = datetime.now().isoformat()
    return metadata

@live_app.get("/parameters")
def get_parameters():
    """
    This returns values from the ``[interface]`` section of the configuration file.

    :>json name: instance name (appears as interface's title)
    :>json version: showergel's version
    """
    version = pkg_resources.get_distribution("showergel").version
    if not version:
        version = "demo"
    return {
        "name": live_app.config.get("interface.name", "Showergel"),
        "version": version,
    }

@live_app.delete("/live")
def delete_live():
    """
    Skips current track: this sends a skip command to the first Liquidsoap output.
    """
    Connection.get().skip()
    return {}
