"""Constants for the H806SB Led Controller integration."""

from datetime import timedelta

DOMAIN = "h806sb"
CONFIG_VERSION = 1

TRACK_INTERVAL = timedelta(seconds=60)

# config flow
CONF_ACTION = "discovery"
CONF_AUTO_DISCOVERY = "discovery_auto"
CONF_MANUAL_SETUP = "discovery_manual"