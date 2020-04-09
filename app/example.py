import argparse
import warnings
warnings.simplefilter("ignore")

parser = argparse.ArgumentParser(description='A simple command line interface for generating time series from OnEarth WMTS tiles')
parser.add_argument('--layer', type=str,
                    default="MODIS_Aqua_L3_SST_MidIR_9km_Night_Monthly",
                    help='name of tile to use. for more details, run with --listlayers.')

parser.add_argument('--listlayers', action='store_true', default=False, help='list all supported layers.')

parser.add_argument('--startdate', type=str, default="2012-01-01",
                    help='start date for time series (format: YYYY-MM-DD)')

parser.add_argument('--enddate', type=str, default="2013-01-01",
                    help='start date for time series (format: YYYY-MM-DD)')

parser.add_argument('--level', type=int, default=1,
                    help='WMTS tilematrix level to use (higher is better, but more expensive)')

parser.add_argument('--increment', type=str, default="monthly", choices=["monthly", "daily", "annual"],
                    help='time increment to sample between start and end date for time series')

args = parser.parse_args()

from timeseries import time_series, plot, wmts

if args.listlayers:
    layers = list(zip(*wmts.items()))[0]

    print("Layers:")
    for layer in layers:
        print(layer)
    exit(0)

data, dates, ovs = time_series([args.layer], str(args.level), args.startdate, args.enddate, increment=args.increment, typ="single")  # , "AIRS_Methane_Volume_Mixing_Ratio_Daily_Day"
plot([args.layer], dates, str(args.level), data)