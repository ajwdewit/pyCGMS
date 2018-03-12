import sqlalchemy as sa

from .runner import db
from pcse.db import cgms8, cgms12, cgms14
# Note: you cannot import the dataproviders from the right CGMS version here
# already because db.version will only be available AFTER this module has
# been imported.


def get_agromanagement(engine, grid, crop, year):

    if db.version == 8:
        agro = cgms8.AgroManagementDataProvider(engine, crop_no=crop, grid_no=grid, campaign_year=year)
    elif db.version == 12:
        agro = cgms12.AgroManagementDataProvider(engine, crop_no=crop, grid_no=grid, campaign_year=year)
    else:
        agro = cgms14.AgroManagementDataProvider(engine, idgrid=grid, idcrop_parametrization=crop,
                                                 campaign_year=year)
    return agro


def get_weatherdata(engine, grid, start, end):
    if db.version == 8:
        wdp = cgms8.GridWeatherDataProvider(engine, grid_no=grid, start_date=start, end_date=end, use_cache=False)
    elif db.version == 12:
        wdp = cgms12.WeatherObsGridDataProvider(engine, grid_no=grid, start_date=start, end_date=end, use_cache=False)
    else:
        wdp = cgms14.WeatherObsGridDataProvider(engine, idgrid=grid, start_date=start, end_date=end, use_cache=False)

    return wdp


def get_cropdata(engine, grid, crop, year):
    if db.version == 8:
        cropd = cgms8.CropDataProvider(engine, crop_no=crop, grid_no=grid, campaign_year=year)
    elif db.version == 12:
        cropd = cgms12.CropDataProvider(engine, crop_no=crop, grid_no=grid, campaign_year=year)
    else:
        cropd = cgms14.CropDataProvider(engine, idgrid=grid, idcrop_parametrization=crop)

    return cropd


def get_soiliterator(engine, grid):
    if db.version == 8:
        soild = cgms8.SoilDataIterator(engine, grid_no=grid)
    elif db.version == 12:
        soild = cgms12.SoilDataIterator(engine, grid_no=grid)
    else:
        soild = cgms14.SoilDataIterator(engine, idgrid=grid)

    return soild


def get_sitedata(engine, grid, crop, year, stu):
    if db.version == 8:
        sited = cgms8.SiteDataProvider(engine, grid_no=grid, crop_no=crop, campaign_year=year, stu_no=stu)
    elif db.version == 12:
        sited = cgms12.SiteDataProvider(engine, grid_no=grid, crop_no=crop, campaign_year=year, stu_no=stu)
    else:
        sited = cgms14.SiteDataProvider(engine, idgrid=grid, idcrop_parametrization=crop,
                                        campaign_year=year, idstu=stu)

    return sited


def get_suitability(engine, crop):
    if db.version == 8:
        suitability = cgms8.STU_Suitability(engine, crop_no=crop)
    elif db.version == 12:
        suitability = cgms12.STU_Suitability(engine, crop_no=crop)
    else:
        suitability = cgms14.STU_Suitability(engine, idcrop_parametrization=crop)

    return suitability


def get_grids(engine, crop, year):
    meta = sa.MetaData(engine)
    if db.version in (8, 12):
        tbl = sa.Table('crop_calendar', meta, autoload=True)
        s = sa.select([tbl.c.grid_no], sa.and_(tbl.c.crop_no==crop,
                                                tbl.c.year==year)).distinct()
        rows = s.execute()
        grids = [r.grid_no for r in rows]
    else:
        tbl = sa.Table('crop_spatializations', meta, autoload=True)
        s = sa.select([tbl.c.idgrid], tbl.c.idcrop_parametrization==crop).distinct()
        rows = s.execute()
        grids = [r.idgrid for r in rows]

    return grids

