"""Constants for the Modbus Local Gateway integration."""

from homeassistant.const import Platform

DOMAIN = "modbus_local_gateway"

# PLATFORMS: list[Platform] = [
#     Platform.SENSOR,
#     Platform.BINARY_SENSOR,
#     Platform.NUMBER,
#     Platform.SELECT,
#     Platform.SWITCH,
#     Platform.TEXT,
# ]

TYPES_DIR = "entity_types."

PLATFORMS: list[str] = [
    TYPES_DIR + Platform.SENSOR,
    TYPES_DIR + Platform.BINARY_SENSOR,
    TYPES_DIR + Platform.NUMBER,
    TYPES_DIR + Platform.SELECT,
    TYPES_DIR + Platform.SWITCH,
    TYPES_DIR + Platform.TEXT,
]

CONF_SLAVE_ID = "slave_id"
CONF_DEVICE_INFO = "device_info"
CONF_DEFAULT_SLAVE_ID = 1
CONF_DEFAULT_PORT = 502
CONF_PREFIX = "prefix"
OPTIONS_REFRESH = "refresh"
OPTIONS_DEFAULT_REFRESH = 30
