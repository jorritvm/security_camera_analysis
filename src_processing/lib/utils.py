import time
import logging

# logging
def setup_logging():
    logging.basicConfig(
        format='[%(asctime)s] %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
        level=logging.INFO
    )

def log(s):
    logging.info(s)


# timers
class Timer:
    def __init__(self, name="Timer"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    def elapsed(self):
        if self.start_time is None or self.end_time is None:
            return f"{self.name}: Timer not started or stopped."
        total_seconds = int(self.end_time - self.start_time)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{self.name}: {hours:02d}:{minutes:02d}:{seconds:02d}"