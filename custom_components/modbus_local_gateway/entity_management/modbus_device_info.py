"""Module for the ModbusDeviceInfo class"""

from __future__ import annotations

import logging
from os.path import join
from typing import Any

from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.yaml import load_yaml
from homeassistant.util.yaml.loader import JSON_TYPE

from ..device_configs import CONFIG_DIR
from .base import (
    ModbusEntityDescription,
    ModbusNumberEntityDescription,
    ModbusSelectEntityDescription,
    ModbusSensorEntityDescription,
    ModbusSwitchEntityDescription,
    ModbusTextEntityDescription,
    ModbusBinarySensorEntityDescription,
)
from .const import (
    BITS,
    CONTROL_TYPE,
    DEFAULT_STATE_CLASS,
    DEVICE,
    TYPE_HOLDING_REGISTER,
    TYPE_INPUT_REGISTER,
    TYPE_COIL,
    TYPE_DISCRETE_INPUT,
    DEVICE_CLASS,
    FLAGS,
    IS_FLOAT,
    IS_STRING,
    MANUFACTURER,
    MAX_READ,
    MAX_READ_DEFAULT,
    MODEL,
    NEVER_RESETS,
    OPTIONS,
    PRECISION,
    REGISTER_ADDRESS,
    REGISTER_COUNT,
    REGISTER_MAP,
    REGISTER_MULTIPLIER,
    REGISTER_OFFSET,
    SHIFT,
    STATE_CLASS,
    NAME,
    UNIT,
    UOM,
    UOM_MAPPING,
    ControlType,
    ModbusDataType,
)

_LOGGER = logging.getLogger(__name__)

DESCRIPTION_TYPE = (
    ModbusNumberEntityDescription
    | ModbusSelectEntityDescription
    | ModbusSensorEntityDescription
    | ModbusSwitchEntityDescription
    | ModbusTextEntityDescription
    | ModbusBinarySensorEntityDescription
)


class DeviceConfigError(HomeAssistantError):
    """Device Configuration Error"""


class ModbusDeviceInfo:
    """Representation of YAML device info"""

    def __init__(self, fname: str) -> None:
        """Initialise the device config"""
        self.fname: str = fname
        filename: str = join(CONFIG_DIR, fname)
        self._config: JSON_TYPE | None = load_yaml(filename)
        if self.manufacturer and self.model:
            _LOGGER.debug("Loaded device config %s", fname)

    @property
    def manufacturer(self) -> str:
        """Manufacturer of the device"""
        if (
            self._config
            and isinstance(self._config, dict)
            and DEVICE in self._config
            and isinstance(self._config[DEVICE], dict)
            and MANUFACTURER in self._config[DEVICE]
        ):
            return self._config[DEVICE][MANUFACTURER]
        raise DeviceConfigError()

    @property
    def model(self) -> str:
        """Model of the device"""
        if (
            self._config
            and isinstance(self._config, dict)
            and DEVICE in self._config
            and isinstance(self._config[DEVICE], dict)
            and MODEL in self._config[DEVICE]
        ):
            return self._config[DEVICE][MODEL]
        raise DeviceConfigError()

    @property
    def max_read_size(self) -> int:
        """Maximum number of registers to read in a single request"""
        if self._config and isinstance(self._config, dict) and DEVICE in self._config:
            return self._config[DEVICE].get(MAX_READ, MAX_READ_DEFAULT)
        raise DeviceConfigError()

    @property
    def entity_descriptions(self) -> tuple[DESCRIPTION_TYPE, ...]:
        """Get the entity descriptions for the device"""
        if not self._config or not isinstance(self._config, dict):
            raise DeviceConfigError()

        descriptions = []
        for section, data_type in [
            (TYPE_HOLDING_REGISTER, ModbusDataType.HOLDING_REGISTER),
            (TYPE_INPUT_REGISTER, ModbusDataType.INPUT_REGISTER),
            (TYPE_COIL, ModbusDataType.COIL),
            (TYPE_DISCRETE_INPUT, ModbusDataType.DISCRETE_INPUT),
        ]:
            if section in self._config and isinstance(self._config[section], dict):
                for entity, entity_data in self._config[section].items():
                    if isinstance(entity_data, dict):
                        desc = self._create_description(entity, data_type, entity_data)
                        if desc:
                            descriptions.append(desc)
        return tuple(descriptions)

    def get_uom(self, data) -> dict[str, str | None]:
        """Get the unit_of_measurement and device class"""
        unit = data.get(UOM)
        state_class: str | None = DEFAULT_STATE_CLASS
        device_class: str | None = None

        if unit in UOM_MAPPING:
            device_class = UOM_MAPPING[unit].get(DEVICE_CLASS, device_class)
            state_class = UOM_MAPPING[unit].get(STATE_CLASS, DEFAULT_STATE_CLASS)
            unit = UOM_MAPPING[unit].get(UNIT, unit)

        device_class = data.get(DEVICE_CLASS, device_class)
        state_class = data.get(STATE_CLASS, state_class)

        if device_class is None or data.get(IS_STRING, False):
            state_class = None

        return {
            "native_unit_of_measurement": unit,
            "device_class": device_class,
            "state_class": state_class,
        }

    def _create_description(self, entity: str, data_type: ModbusDataType, _data: dict[str, Any]) -> DESCRIPTION_TYPE | None:
        """Create an entity description based on data type"""
        uom = self.get_uom(_data)

        default_control_type = {
            ModbusDataType.HOLDING_REGISTER: ControlType.SENSOR,
            ModbusDataType.INPUT_REGISTER: ControlType.SENSOR,
            ModbusDataType.COIL: ControlType.BINARY_SENSOR,
            ModbusDataType.DISCRETE_INPUT: ControlType.BINARY_SENSOR,
        }
        control_type = _data.get(CONTROL_TYPE, default_control_type[data_type])

        # Start with all attributes from _data
        params = dict(_data)

        # Override or add required and computed fields
        params.update({
            "key": entity,
            "name": _data.get(NAME, entity),
            "register_address": _data.get(REGISTER_ADDRESS),
            "register_count": _data.get(REGISTER_COUNT, 1),
            "register_multiplier": _data.get(REGISTER_MULTIPLIER, 1.0),
            "register_offset": _data.get(REGISTER_OFFSET),
            "register_map": _data.get(REGISTER_MAP),
            "string": _data.get(IS_STRING, False),
            "float": _data.get(IS_FLOAT, False),
            "bits": _data.get(BITS),
            "bit_shift": _data.get(SHIFT),
            "flags": _data.get(FLAGS),
            "never_resets": _data.get(NEVER_RESETS, False),
            "data_type": data_type,
            "control_type": control_type,
            # Only include relevant uom keys based on control_type
            "native_unit_of_measurement": uom["native_unit_of_measurement"],
            "device_class": uom["device_class"],
        })

        # Add state_class for sensors only
        if control_type == ControlType.SENSOR:
            params["state_class"] = uom["state_class"]

        # # Handle entity_category directly from _data
        # if "entity_category" in _data:
        #     try:
        #         params["entity_category"] = EntityCategory(_data["entity_category"])
        #     except ValueError:
        #         _LOGGER.warning("Invalid entity_category %s for %s", _data["entity_category"], entity)
        #         del params["entity_category"]  # Remove invalid category

        # Define allowed control types per data type
        allowed_control_types = {
            ModbusDataType.HOLDING_REGISTER: [
                ControlType.SENSOR,
                ControlType.NUMBER,
                ControlType.SELECT,
                ControlType.TEXT,
                ControlType.SWITCH,
            ],
            ModbusDataType.INPUT_REGISTER: [ControlType.SENSOR],
            ModbusDataType.COIL: [ControlType.SWITCH],
            ModbusDataType.DISCRETE_INPUT: [ControlType.BINARY_SENSOR],
        }
        if control_type not in allowed_control_types.get(data_type, []):
            _LOGGER.warning("Invalid control_type %s for data_type %s", control_type, data_type)
            return None

        # Select description class and add control-specific parameters
        desc_cls = None
        if control_type == ControlType.SENSOR:
            desc_cls = ModbusSensorEntityDescription
            params["precision"] = _data.get(PRECISION)
        elif control_type == ControlType.BINARY_SENSOR:
            desc_cls = ModbusBinarySensorEntityDescription
        elif control_type == ControlType.SWITCH:
            desc_cls = ModbusSwitchEntityDescription
            switch_data = _data.get("switch", {})
            if not isinstance(switch_data, dict):
                _LOGGER.warning("Switch configuration for %s should be a dictionary", entity)
                return None
            params["on"] = switch_data.get("on", 1)
            params["off"] = switch_data.get("off", 0)
        elif control_type == ControlType.SELECT:
            desc_cls = ModbusSelectEntityDescription
            params["select_options"] = _data.get(OPTIONS)
            if not params["select_options"]:
                _LOGGER.warning("Missing options for select")
                return None
        elif control_type == ControlType.NUMBER:
            desc_cls = ModbusNumberEntityDescription
            number_data = _data.get("number", {})
            if not isinstance(number_data, dict):
                _LOGGER.warning("Number configuration for %s should be a dictionary", entity)
                return None
            if "min" not in number_data or "max" not in number_data:
                _LOGGER.warning("Missing min or max for number in %s", entity)
                return None
            params["min"] = number_data["min"]
            params["max"] = number_data["max"]
            params["precision"] = _data.get(PRECISION)
        elif control_type == ControlType.TEXT:
            desc_cls = ModbusTextEntityDescription
        else:
            _LOGGER.warning("Unsupported control_type %s", control_type)
            return None

        if desc_cls:
            # Filter out None values and create the description
            desc = desc_cls(**{k: v for k, v in params.items() if v is not None})
            if desc.validate():
                return desc
        return None
