# pyCGMS

## The European system for crop monitoring and yield forecasting

The Joint Research Centre of the European Commission runs an operational system for
crop monitoring and yield forecasting called [MARS] (Monitoring Agricultural ReSources).
MARS is used within agricultural monitoring activities applied to Europe, sub-Saharan 
Africa and other areas of the world. Crop yield forecasting is undertaken to provide monthly 
bulletins forecasting crop yields to support the EU's Common Agriculture Policy (CAP). 
Providing early warning of crop shortages or failure provides rapid information for EU 
development aid activities to support food insecure countries.

The MARS system implements different components for monitoring including meteorological 
data, crop simulation modelling, satellite data and field vists. Finally, statistical 
post-processing is used in combination with regional yield statistics to make 
forecasts of actual crop yield and production. 

## The Crop Growth Monitoring System (CGMS)
The crop simulation component in MARS is implemented by a system called [CGMS] (Crop Growth
Monitoring System) which includes the [WOFOST] crop simulation model 
and was originally implemented in C++. CGMS links to a database structure which provides the inputs 
(weather data, crop parameters, soil types and crop calendars) and stores the output 
(simulated biomass, yield, leaf area index, etc) from the crop simulation model.
Several version of this CGMS database structure exist: V8, V12 and the current V14.

The C++ implementation of CGMS is proprietary, owned by EC-JRC and is not available for
download. In recent implementations of CGMS, the C++ version of C++ is superseded by
the crop simulation models implemented in the [BioMA] framework.

## A python version of CGMS

The PyCGMS package provides a python implementation of the crop simulation 
system embedded in the Crop Growth Monitoring System (CGMS). Under the hood,
the actual crop simulations are carried out by the WOFOST implementation in 
[PCSE] which provides a fully open source implementation of many crop simulation
models developed in Wageningen.

PyCGMS was designed to be compatible
with all versions of the CGMS database and can therefore also run on legacy CGMS
implementations. The original C++ CGMS executable also provided functionality for 
interpolating weather data. pyCGMS does not provide this functionality and it will 
not do so in the future as dedicated packages are available for processing of weather
data. 

## Limitations

PyCGMS is very much a work in progress and therefore does not yet provide all functionality
that was implemented by the C++ CGMS version. Notably, PyCGMS does not provide support for
writing output to the CGMS database structure. This is also a design choice because CGMS provides
large amount of simulation output that can be better loaded into the database using 
dedicated loaders. However, such loaders are not yet available.


## Installation and usage

First of all, PyCGMS requires a [CGMS database] structure in order to retrieve its input
data. A definition of the structure can be found in JRC wiki using the link above.
An example CGMS8 database in SQLite can be found [here].

Next, a python environment must be created for PyCGMS. The environment for PyCGMS is similar to
the environment required for PCSE, so please have a look at the detailed instructions there.
After installing PCSE into the environment PyCGMS can be installed with:

    pip install pycgms
    
Note that depending on the database system you are using, additional database drivers may
need to be installed.




[CGMS]: https://www.researchgate.net/publication/262335822_CGMS_Version_80_User_Manual_and_Technical_Documentation
[BioMA]: http://bioma.jrc.ec.europa.eu/
[MARS]: https://ec.europa.eu/jrc/en/mars
[WOFOST]: https://www.sciencedirect.com/science/article/pii/S0308521X17310107
[CGMS-DB]: https://marswiki.jrc.ec.europa.eu/agri4castwiki/index.php/Appendix_5:_Database_objects
[here]: https://wageningenur4-my.sharepoint.com/:u:/g/personal/allard_dewit_wur_nl/EdwuayKW2IhOp6zCYElA0zsB3NGxcKjZc2zE_JGfVPv89Q?e=oeBjPm
[PCSE]: http://pcse.readthedocs.io 
