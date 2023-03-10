from .core import NOAAWeatherCore
from .datastore import ParquetStore 
from .visualization import MPLVis

class NOAAWeatherParqMPL(NOAAWeatherCore, ParquetStore, MPLVis):
    pass
