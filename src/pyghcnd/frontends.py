from .core import NOAAWeatherCore
from .data_store import ParquetStore 
from .visualization import MPLVis

class NOAAWeatherParqMPL(NOAAWeatherCore, ParquetStore, MPLVis):
    pass
