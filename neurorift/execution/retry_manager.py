import time


class RetryManager:
    def __init__(self, retries=2):
        self.retries = retries

    def wait(self, attempt):
        time.sleep(2**attempt)
