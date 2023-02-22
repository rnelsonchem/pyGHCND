from .core import NOAAWeatherCore
from .data_store import ParquetStore 

class NOAAWeatherParqMPL(NOAAWeatherCore, ParquetStore):
    pass
