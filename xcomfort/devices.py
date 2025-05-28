from contextlib import nullcontext
import rx
from .messages import Messages, ShadeOperationState  # Import ShadeOperationState

class DeviceState:
    def __init__(self, payload):
        self.raw = payload

    def __str__(self):
        return f"DeviceState({self.raw})"

class LightState(DeviceState):
    def __init__(self, switch, dimmvalue, payload):
        DeviceState.__init__(self, payload)
        self.switch = switch
        self.dimmvalue = dimmvalue

    def __str__(self):
        return f"LightState({self.switch}, {self.dimmvalue})"

    __repr__ = __str__

class RcTouchState(DeviceState):
    def __init__(self, temperature, humidity, payload):
        DeviceState.__init__(self, payload)
        self.temperature = temperature
        self.humidity = humidity

    def __str__(self):
        return f"RcTouchState({self.temperature}, {self.humidity})"

    __repr__ = __str__

class HeaterState(DeviceState):
    def __init__(self, payload):
        DeviceState.__init__(self, payload)

    def __str__(self):
        return f"HeaterState({self.payload})"

    __repr__ = __str__

# New ShadeState class for detailed state management
class ShadeState(DeviceState):
    def __init__(self):
        self.raw = {}
        self.current_state: int | None = None
        self.is_safety_enabled: bool | None = None
        self.position: int | None = None

    def update_from_partial_state_update(self, payload: dict) -> None:
        """Aggregate partial state updates from the bridge."""
        self.raw.update(payload)

        if (current_state := payload.get("curstate")) is not None:
            self.current_state = current_state

        if (safety := payload.get("shSafety")) is not None:
            self.is_safety_enabled = safety != 0

        if (position := payload.get("shPos")) is not None:
            self.position = position

    @property
    def is_closed(self) -> bool | None:
        """Return whether the shade is fully closed (position 100)."""
        if self.position is None or 0 < self.position < 100:
            return None
        return self.position == 100

    def __str__(self) -> str:
        return f"ShadeState(current_state={self.current_state}, is_safety_enabled={self.is_safety_enabled}, position={self.position}, raw={self.raw})"

class BridgeDevice:
    def __init__(self, bridge, device_id, name):
        self.bridge = bridge
        self.device_id = device_id
        self.name = name
        self.state = rx.subject.BehaviorSubject(None)

    def handle_state(self, payload):
        self.state.on_next(DeviceState(payload))

class Light(BridgeDevice):
    def __init__(self, bridge, device_id, name, dimmable):
        BridgeDevice.__init__(self, bridge, device_id, name)
        self.dimmable = dimmable

    def interpret_dimmvalue_from_payload(self, switch, payload):
        if not self.dimmable:
            return 99
        if not switch:
            return self.state.value.dimmvalue if self.state.value is not None else 99
        return payload['dimmvalue']

    def handle_state(self, payload):
        switch = payload['switch']
        dimmvalue = self.interpret_dimmvalue_from_payload(switch, payload)
        self.state.on_next(LightState(switch, dimmvalue, payload))

    async def switch(self, switch: bool):
        await self.bridge.switch_device(self.device_id, {"switch": switch})

    async def dimm(self, value: int):
        value = max(0, min(99, value))
        await self.bridge.slide_device(self.device_id, {"dimmvalue": value})

    def __str__(self):
        return f"Light({self.device_id}, \"{self.name}\", dimmable: {self.dimmable}, state:{self.state.value})"

    __repr__ = __str__

class RcTouch(BridgeDevice):
    def __init__(self, bridge, device_id, name, comp_id):
        BridgeDevice.__init__(self, bridge, device_id, name)
        self.comp_id = comp_id

    def handle_state(self, payload):
        print(f"RcTouchState::: {payload}")
        temperature = None
        humidity = None
        if 'info' in payload:
            for info in payload['info']:
                if info['text'] == "1222":
                    temperature = float(info['value'])
                if info['text'] == "1223":
                    humidity = float(info['value'])
        if temperature is not None and humidity is not None:
            self.state.on_next(RcTouchState(temperature, humidity, payload))

class Heater(BridgeDevice):
    def __init__(self, bridge, device_id, name, comp_id):
        BridgeDevice.__init__(self, bridge, device_id, name)
        self.comp_id = comp_id

class Shade(BridgeDevice):
    def __init__(self, bridge, device_id, name, comp_id):
        BridgeDevice.__init__(self, bridge, device_id, name)
        self.comp_id = comp_id
        self.__shade_state = ShadeState()  # Aggregate state across updates
        self.payload = {}  # Store initial payload if needed later

    @property
    def supports_go_to(self) -> bool | None:
        """Check if the shade supports precise position control."""
        if (component := self.bridge._comps.get(self.comp_id)) is not None:
            return component.comp_type == 86 and self.payload.get("shRuntime") == 1
        return None

    def handle_state(self, payload):
        """Update the shade state with incoming data."""
        self.__shade_state.update_from_partial_state_update(payload)
        self.state.on_next(self.__shade_state)

    async def send_state(self, state, **kwargs):
        """Send a state command to the shade, respecting safety checks."""
        if self.__shade_state.is_safety_enabled:
            return  # Skip if safety is enabled, per Jankrib’s logic
        await self.bridge.send_message(
            Messages.SET_DEVICE_SHADING_STATE,
            {"deviceId": self.device_id, "state": state, **kwargs}
        )

    async def move_down(self):
        """Move the shade down (close)."""
        await self.send_state(ShadeOperationState.CLOSE)

    async def move_up(self):
        """Move the shade up (open)."""
        await self.send_state(ShadeOperationState.OPEN)

    async def move_stop(self):
        """Stop the shade movement."""
        await self.send_state(ShadeOperationState.STOP)

    async def move_to_position(self, position: int):
        """Move the shade to a specific position (0-100)."""
        if self.supports_go_to and 0 <= position <= 100:
            await self.send_state(ShadeOperationState.GO_TO, value=position)