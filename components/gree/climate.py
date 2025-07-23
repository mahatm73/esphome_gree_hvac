import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import climate, uart
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
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await climate.register_climate(var, config)

    # UART bus
    cg.add(var.set_uart_id(config[CONF_UART_ID]))

    # Swing commands
    if CONF_SWING_ON_COMMAND in config:
        cg.add(var.set_swing_on_command(config[CONF_SWING_ON_COMMAND]))
    if CONF_SWING_OFF_COMMAND in config:
        cg.add(var.set_swing_off_command(config[CONF_SWING_OFF_COMMAND]))

    return var


def to_hass_config(data, config):
    hass = climate.core_to_hass_config(data, config)
    hass['supported_features'] |= climate.SUPPORT_SWING_MODE
    hass['swing_modes'] = [climate.CLIMATE_SWING_OFF, climate.CLIMATE_SWING_ON]
    return hass

# Python wrapper
class GreeClimate(climate.Climate, cg.Component, cg.PollingComponent):
    """Gree HVAC Climate integration with swing support"""
    def __init__(self) -> None:
        super().__init__()
        self._uart = None
        self._swing_on = None
        self._swing_off = None

    def set_uart_id(self, uart_var) -> None:
        self._uart = uart_var

    def set_swing_on_command(self, code: int) -> None:
        self._swing_on = code

    def set_swing_off_command(self, code: int) -> None:
        self._swing_off = code

    def control(self, call):
        # Standard commands
        self._send_mode_and_temp(call)
        self._send_fan_mode(call)

        # Swing (louver)
        swing_mode = call.get_swing_mode()
        if swing_mode is not None and self._uart is not None:
            if swing_mode == climate.CLIMATE_SWING_ON and self._swing_on is not None:
                self._uart.write_byte(self._swing_on)
            elif swing_mode == climate.CLIMATE_SWING_OFF and self._swing_off is not None:
                self._uart.write_byte(self._swing_off)

    def dump_config(self) -> None:
        super().dump_config()
        _LOGGER = cg.get_logger(__name__)
        _LOGGER.info("  Swing ON command: %s", self._swing_on)
        _LOGGER.info("  Swing OFF command: %s", self._swing_off)
