"""The PyCGMS package provides a python implementation of the crop simulation
system embedded in the Crop Growth Monitoring System (CGMS). Under the hood,
the actual crop simulations are carried out by the WOFOST implementation in
[PCSE] which provides a fully open source implementation of many crop simulation
models developed in Wageningen. PyCGMS was designed to be compatible
with all versions of the CGMS database and can therefore also run on legacy CGMS
implementations.
"""
from . import runner

__version__ = "0.1.0"

def start():
    runner.main()

