import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import climate, uart
from esphome.components.climate.climate import SUPPORT_SWING_MODE, CLIMATE_SWING_OFF, CLIMATE_SWING_ON
from esphome.const import CONF_ID  

DEPENDENCIES = ['uart']

# Forward declare the C++ class
GreeClimate = cg.global_ns.class_('GreeClimate', cg.PollingComponent, climate.Climate, cg.Component)

CONF_UART_ID = 'uart_id'
CONF_SWING_ON_COMMAND = 'swing_on_command'
CONF_SWING_OFF_COMMAND = 'swing_off_command'

# Define the schema, including swing commands
PLATFORM_SCHEMA = climate.climate_schema({
    cv.GenerateID(CONF_ID): cv.declare_id(GreeClimate),
    cv.Required(CONF_UART_ID): cv.use_id(uart.UARTComponent),
    cv.Optional(CONF_SWING_ON_COMMAND): cv.uint8_t,
    cv.Optional(CONF_SWING_OFF_COMMAND): cv.uint8_t,
})

async def to_code(config):
    # Instantiate the component
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await climate.register_climate(var, config)

    # Set UART bus
    cg.add(var.set_uart_id(config[CONF_UART_ID]))

    # Configure optional swing commands
    if CONF_SWING_ON_COMMAND in config:
        cg.add(var.set_swing_on_command(config[CONF_SWING_ON_COMMAND]))
    if CONF_SWING_OFF_COMMAND in config:
        cg.add(var.set_swing_off_command(config[CONF_SWING_OFF_COMMAND]))

    return var


def to_hass_config(data, config):
    # Base climate config
    hass = climate.core_to_hass_config(data, config)
    # Enable swing support
    hass['supported_features'] |= SUPPORT_SWING_MODE
    hass['swing_modes'] = [CLIMATE_SWING_OFF, CLIMATE_SWING_ON]
    return hass

# Python wrapper class
class GreeClimate(climate.Climate, cg.Component, cg.PollingComponent):
    """Gree HVAC Climate integration with swing support"""
    def __init__(self) -> None:
        super().__init__()
        self._uart = None
        self._swing_on_command = None
        self._swing_off_command = None

    def set_uart_id(self, uart_var) -> None:
        self._uart = uart_var

    def set_swing_on_command(self, code: int) -> None:
        self._swing_on_command = code

    def set_swing_off_command(self, code: int) -> None:
        self._swing_off_command = code

    def control(self, call):
        # Send mode, temperature, fan commands
        self._send_mode_and_temp(call)
        self._send_fan_mode(call)

        # Send swing command if configured
        swing = call.get_swing_mode()
        if swing is not None and self._uart is not None:
            if swing == CLIMATE_SWING_OFF and self._swing_off_command is not None:
                self._uart.write_byte(self._swing_off_command)
            elif swing == CLIMATE_SWING_ON and self._swing_on_command is not None:
                self._uart.write_byte(self._swing_on_command)

    def dump_config(self) -> None:
        super().dump_config()
        _LOGGER = cg.get_logger(__name__)
        _LOGGER.info("  Swing ON command: %s", self._swing_on_command)
        _LOGGER.info("  Swing OFF command: %s", self._swing_off_command)
