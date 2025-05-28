# xcomfort-python

Unofficial python package for communicating with Eaton xComfort Bridge.
This fork is based on : [alexbrasetvik](https://github.com/alexbrasetvik) - `xcomfort-python` library.

## Credits

- **Original Author**: [jankrib](https://pypi.org/project/xcomfort/0.1.2/) - Created the original `xcomfort-python` library.
- **Contributor**: [oywino](https://github.com/oywino) - Maintaining this fork with updates and enhancements.

## Changes in This Fork

- Re-implemented advanced shade control features from the original library v0.1.2 on PyPI which was later abandoned by [alexbrasetvik](https://github.com/alexbrasetvik). 
  The xComfort Python library is thus again support the enhanced `Shade` class with detailed state management, safety checks, and precise position control. The changes are confined to `devices.py` and `messages.py`, ensuring compatibility with existing integrations.
  
  Key Updates:
  - **devices.py**:
    - Added `ShadeState` class to aggregate partial state updates (e.g., position, safety status) from the bridge.
    - Enhanced `Shade` class with:
      - `__shade_state` for cohesive state tracking.
      - `supports_go_to` property to check for position control capability.
      - `handle_state` method for reactive state updates.
      - `send_state` method with safety checks to prevent operations when safety mode is active.
      - Updated `move_up`, `move_down`, `move_stop`, and added `move_to_position` for precise control.
  - **messages.py**:
    - Added `ShadeOperationState` enum to define shade commands (e.g., `OPEN`, `CLOSE`, `STOP`, `GO_TO`), aligning with the bridge’s protocol.
  
  These changes enable robust shade control, including position setting and safety-aware operations, while maintaining backward compatibility with the existing integration.

## Usage

```python
import asyncio
from xcomfort import Bridge

def observe_device(device):
    device.state.subscribe(lambda state: print(f"Device state [{device.device_id}] '{device.name}': {state}"))

async def main():
    bridge = Bridge(<ip_address>, <auth_key>)

    runTask = asyncio.create_task(bridge.run())

    devices = await bridge.get_devices()

    for device in devices.values():
        observe_device(device)

    # Wait 50 seconds. Try flipping the light switch manually while you wait
    await asyncio.sleep(50) 

    # Turn off all the lights.
    # for device in devices.values():
    #     await device.switch(False)
    #
    # await asyncio.sleep(5)

    await bridge.close()
    await runTask

asyncio.run(main())
```

## Tests

```python
python -m pytest
```
