class Channel:
    def connect(self):
        return True

    def receive_message(self, payload=None):
        return payload or {}

    def send_message(self, message):
        return message

    def close(self):
        return True
