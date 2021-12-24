import keyboard

class KeyStateStorage:
    def __init__(self) -> None:
        self.key_stor = {}

    def add_key_listener(self, key):
        def _key_handler():
            self.key_stor[key] = not self.key_stor[key]

        keyboard.add_hotkey(key, _key_handler)
        self.key_stor[key] = False

    def remove(self, key):
        if self.key_stor[key]:
            del self.key_stor[key]

    def __getitem__(self, key):
        return self.key_stor[key]
