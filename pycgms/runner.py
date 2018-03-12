class C(object):
    "A container class"
    pass

import os
import shutil

import argparse
import datetime as dt
import sqlalchemy as sa
import pandas as pd
import numpy as np

import pcse
from pcse.engine import CGMSEngine
from pcse.util import WOFOST71SiteDataProvider, DummySoilDataProvider
from pcse.base_classes import ParameterProvider

# Placeholder for DB version, needed by data_providers
db = C()
from . import data_providers as dp

soil_identifiers = {8:  ("smu_no", "smu_area", "stu_no", "stu_perc"),
                    12: ("smu_no", "smu_area", "stu_no", "stu_perc"),
                    14: ("idsmu", "smu_area", "idstu", "stu_perc")}

# Parameters with date types that cannot be averaged
date_type_variables = ["DOS", "DOE", "DOV", "DOA", "DOM", "DOH"]

def valid_date_type(arg_date_str):
    """custom argparse *date* type for user dates values given from the command line"""
    try:
        return dt.datetime.strptime(arg_date_str, "%Y-%m-%d")
    except ValueError:
        msg = "Given Date ({0}) not valid! Expected format, YYYY-MM-DD!".format(arg_date_str)
    raise argparse.ArgumentTypeError(msg)


def create_parser():
    parser = argparse.ArgumentParser(description='Run a gridded WOFOST simulation on a CGMS database.')
    parser.add_argument('--db_version', dest='db_version', action='store', default=None, choices=[8, 12, 14],
                        help='Type of CGMS DB to use (either 8, 12 or 14).', required=True, type=int
                        )
    parser.add_argument('--dsn', dest='dsn', action='store', default=None, type=str, required=True,
                        help="SQLAlchemy connection URL for CGMS DB to connect to. See also "
                             "http://docs.sqlalchemy.org/en/latest/core/engines.html"
                        )
    parser.add_argument('--crop', dest='crop', action='store', default=None, type=int, required=True,
                        help="Run simulations for given crop number."
                        )
    parser.add_argument('--year', dest='year', action='store', default=None, type=int, required=True,
                        help="Run simulations for given year. "
                             "The year refers to the year in the crop_calendar table which "
                             "usually indicates the year where sowing of emergence takes place."
                        )
    parser.add_argument('--grid', dest='grid', action='store', default=None, type=int,
                        help="Run simulations for given grid. Optional, by default all grids will "
                             "be simulated where the crop is defined."
                        )
    parser.add_argument('--run_till', dest='run_till', action='store', default=None, type=valid_date_type,
                        metavar="yyyy-mm-dd",
                        help="Run simulations up till this date. This is useful for "
                             "simulations in the current year where not all weather data are "
                             "available up till the end of the simulation."
                        )
    parser.add_argument('--output', dest='output', action='store', default=None, type=str, metavar="OUT_PATH",
                        help="Store simulation results at this location. If not provided "
                             "then the system temp location will be used."
                        )
    parser.add_argument('--aggr_level', dest='aggr_level', action='store', default='stu', choices=["stu", "smu", "grid"],
                        help='Aggregation level for output, default is "stu"', required=False, type=str
                        )
    parser.add_argument('--use_isw_date', dest='use_isw_date', action='store', default=False,
                        help='If True the start_date from the table INITIAL_SOIL_WATER will be used as'
                             'campaign_start_date, default False.', required=False, type=bool
                        )

    return parser


def get_preceeding_dekad(c):
    """Finds the dekad as the first dekad preceding the cdate

    :param c: a date object
    :return: the date representing the preceeding dekad
    """
    if c.day < 10:
        prec_dekad = dt.date(c.year, c.month, 1) - dt.timedelta(days=1)
    elif c.day < 20:
        prec_dekad = dt.date(c.year, c.month, 10)
    else:
        prec_dekad = dt.date(c.year, c.month, 20)

    return prec_dekad


def weighted_avg(group, col_name, weight_name):
    """Compute the weighted average for col_name from the grouped dataframe using weight_name as weights.
    """
    d = group[col_name].values
    w = group[weight_name].values
    try:
        return np.average(d, weights=w)
    except Exception as e:
        pass


def group_dataframe(df, groupby, excluding, weightby):
    """Compute weighted averages on the columns of dataframe 'df' using weights from 'weight_column',
     grouped by columns 'groupby' and excluding columns 'excluding'

    :param df: A Pandas DataFrame
    :param groupby: list of columns to group by
    :param exclude: list of columns to exclude
    :param weightby: column to use as weights
    :return: a new DataFrame with weighted averages
    """
    results = {}
    grp = df.groupby(groupby)
    for colname in df.columns:
        if colname in excluding:
            continue
        results[colname] = grp.apply(weighted_avg, colname, weightby)
    return pd.DataFrame(results).reset_index()


def main():

    parser = create_parser()
    args = parser.parse_args()
    if None in [args.crop, args.year, args.dsn, args.db_version]:
        parser.print_help()
        return
    db.version = args.db_version

    # labels for soil columns which differ across database versions
    lbl_smu, lbl_smu_area, lbl_stu, lbl_stu_perc = soil_identifiers[args.db_version]

    engine = sa.create_engine(args.dsn)
    if args.grid is None:
        grids = dp.get_grids(engine, args.cropd, args.year)
    else:
        grids = [args.grid,]
    for grid in grids:
        agro = dp.get_agromanagement(engine, grid, args.crop, args.year)
        # Fix the campaign start/end onto dekad boundaries
        start_dekad = get_preceeding_dekad(agro.campaign_start_date)
        end_dekad = get_preceeding_dekad(agro.campaign_end_date)
        agro.set_campaign_start_date(start_dekad)
        agro.campaign_end_date = end_dekad

        # We want to pull 180 days of additional weather data to allow water balance initialization
        start_date_weather = start_dekad - dt.timedelta(days=180)
        weatherdata = dp.get_weatherdata(engine, grid, start=start_date_weather, end=end_dekad)

        # Fetch or define crop, soil and site data
        cropd = dp.get_cropdata(engine, grid, args.crop, args.year)
        sited = WOFOST71SiteDataProvider(WAV=100)
        soild = DummySoilDataProvider()
        parameters = ParameterProvider(cropdata=cropd, soildata=soild, sitedata=sited)

        # Run WOFOST potential production and convert output to Pandas DataFrame
        mconf = os.path.join(os.path.dirname(__file__), "Wofost71_PP.conf")
        wofost = CGMSEngine(parameters, weatherdata, agro, config=mconf)
        # Run till end of the campaign year or date provided by --run_until
        if args.run_till is not None:
            wofost.run_till(args.run_till)
        else:
            wofost.run_till(agro.campaign_end_date)
        df_simyield_pp = pd.DataFrame(wofost.get_output())
        df_simyield_summary_pp = pd.DataFrame(wofost.get_summary_output())

        # Run water-limited simulation results
        df_simyield_wlp_stu = None
        df_simyield_wlp_summary_stu = None
        soil_iterator = dp.get_soiliterator(engine, grid)
        suitable_stu = dp.get_suitability(engine, args.crop)
        for smu_no, area, stu_no, percentage, soild in soil_iterator:
            # Check if this is a suitable STU
            if stu_no not in suitable_stu:
                print("Skipping stu: %s" % stu_no)
                continue
            print("Processing grid: %i, smu: %i, stu: %i" % (grid, smu_no, stu_no))
            sited = dp.get_sitedata(engine, grid, args.crop, args.year, stu_no)
            if args.use_isw_date:
                agro.set_campaign_start_date(sited.start_date_waterbalance)
            parameters = ParameterProvider(cropdata=cropd, soildata=soild, sitedata=sited)
            mconf = os.path.join(os.path.dirname(__file__), "Wofost71_WLP_FD.conf")
            wofost = CGMSEngine(parameters, weatherdata, agro, config=mconf)
            # Run till end of the campaign year or date provided by --run_until
            if args.run_till is not None:
                wofost.run_till(args.run_till)
            else:
                wofost.run_till(agro.campaign_end_date)

            # Get output
            df = pd.DataFrame(wofost.get_output())
            # remove simulation days before start_dekad due to soil moisture initialization
            ix = df.day >= start_dekad
            df = df[ix]
            # Add soil identifiers for weighted averaging
            df[lbl_smu] = smu_no
            df[lbl_stu] = stu_no
            df[lbl_smu_area] = area
            df[lbl_stu_perc] = percentage
            if df_simyield_wlp_stu is None:
                df_simyield_wlp_stu = df
            else:
                df_simyield_wlp_stu = pd.concat([df_simyield_wlp_stu, df])

            # Get summary output
            df_summary = pd.DataFrame(wofost.get_summary_output())
            df_summary[lbl_smu] = smu_no
            df_summary[lbl_stu] = stu_no
            df_summary[lbl_smu_area] = area
            df_summary[lbl_stu_perc] = percentage
            if df_simyield_wlp_summary_stu is None:
                df_simyield_wlp_summary_stu = df_summary
            else:
                df_simyield_wlp_summary_stu = pd.concat([df_simyield_wlp_summary_stu, df_summary])

        # Start aggregating simulation results
        # First aggregate all STU's into SMU's by using the 'stu_perc' percentages as weights
        if args.aggr_level in ("smu", "grid"):
            df_simyield_wlp_smu = \
                group_dataframe(df_simyield_wlp_stu, groupby=["day", lbl_smu], weightby=lbl_stu_perc,
                                excluding=["day", lbl_smu, lbl_stu, lbl_stu_perc])
            df_simyield_wlp_summary_smu = \
                group_dataframe(df_simyield_wlp_summary_stu, groupby=[lbl_smu], weightby=lbl_stu_perc,
                                excluding=[lbl_smu, lbl_stu, lbl_stu_perc] + date_type_variables)

            # Next aggregate all SMU's to the grid level by using the 'smu_area' as weights
            if args.aggr_level == 'grid':
                df_simyield_wlp_grid = \
                    group_dataframe(df_simyield_wlp_smu, groupby=["day"], weightby=lbl_smu_area,
                                    excluding=["day", lbl_smu, lbl_smu_area])
                df_simyield_wlp_summary_grid = \
                    group_dataframe(df_simyield_wlp_summary_smu, groupby=[], weightby=lbl_smu_area,
                                    excluding=[lbl_smu, lbl_smu_area])

        print(1)
