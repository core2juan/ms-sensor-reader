from time import time

class ExporterInterface:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.start_time = int(time())
        return cls._instance

    def __call__(cls, metric):
        raise NotImplementedError("Subclasses must implement this method")
