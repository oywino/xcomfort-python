class Rocker(BridgeDevice):
    def __init__(self, bridge, device_id, name, comp_id, payload):
        super().__init__(bridge, device_id, name)
        self.comp_id = comp_id
        self.payload = payload.copy() if payload else {}
        self.is_on = None
        if isinstance(payload, dict) and "curstate" in payload:
            self.is_on = bool(payload["curstate"])
        elif isinstance(payload, bool):
            self.is_on = payload
        self.state = rx.subject.BehaviorSubject(None)

    @property
    def name_with_controlled(self) -> str:
        names_of_controlled: set[str] = set()
        for device_id in self.payload.get("controlId", []):
            device = self.bridge._devices.get(device_id)
            if device:
                names_of_controlled.add(device.name)
        return f"{self.name} ({', '.join(sorted(names_of_controlled))})"

    def handle_state(self, payload, broadcast: bool = True) -> None:
        print(f"Rocker {self.device_id} received state update: {payload}")
        # Update the stored payload
        self.payload.update(payload)
        # Compute the legacy state using 'curstate'
        curstate = payload.get("curstate", self.is_on if self.is_on is not None else False)
        self.is_on = bool(curstate)
        print(f"Rocker {self.device_id} computed legacy is_on: {self.is_on}")
        
        # Compute the new simple boolean state from payload['state']
        state_value = payload.get("state", "0")
        simple_state = str(state_value) == "1"
        print(f"Rocker {self.device_id} computed simple state: {simple_state}")
        
        if broadcast:
            # Create attributes dictionary with selected fields
            attributes = {
                "name": self.payload.get("name"),
                "icon": self.payload.get("icon"),
                "order": self.payload.get("order"),
                "devType": self.payload.get("devType"),
                "state": self.payload.get("state"),
                "curstate": self.payload.get("curstate"),
                "function": self.payload.get("function"),
                "delaytime": self.payload.get("delaytime"),
                "dimmvalueOn": self.payload.get("dimmvalueOn"),
                "dimmvalueOff": self.payload.get("dimmvalueOff"),
                "dimmtime": self.payload.get("dimmtime"),
            }
            # Broadcast a dictionary with new_state and attributes
            self.state.on_next({
                "new_state": simple_state,
                "attributes": attributes
            })

    def __str__(self):
        return f'Rocker({self.device_id}, "{self.name}", is_on: {self.is_on}, payload: {self.payload})'