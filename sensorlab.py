#!/usr/bin/env python
"""
Collate a set of files from the SensorLab project, each containing a single
TimeSeries, into a single DataFrame (per type of data).
"""
__author__ = "Martin Blais <blais@furius.ca>"

import os, re
from os.path import *
from pandas.io.parsers import read_csv
import pandas
import matplotlib.pyplot as plt
import numpy as np


def getfiles(root, maxfiles=None):
    """ Return the list of CSV files to process. Filter out all undesirable files."""
    i = 0
    for fn in os.listdir(root):
        # Skip hiddne files created by Mac OS X
        if re.match(r'^\._', fn):
            continue
        # Skip non-data files
        if not re.match(r'.*\.csv$', fn):
            continue

        yield join(root, fn)

        i += 1
        if maxfiles is not None and i == maxfiles: break


def parse_float(fstr):
    """ A safe routine for parsing a float. The data contains some junk values
    (e.g. 'C'), so we need to catch those and return a NaN instead."""
    try:
        return float(fstr)
    except ValueError:
        return np.nan


def remove_outliers(df, nperiods, nstd):
    """ Remove all the outliers by eliminatings values beyond 'nstd' standard
    deviations away from a rolling median of 'nperiods' periods. This sets the
    offending values to nan."""

    # Note: make sure to backfill our hi/lo bounds in order to cull outliers
    # near the beginning of the series.

    # Note: use a median for robustness.
    df = df.copy()
    center = pandas.stats.moments.rolling_median(df, nperiods)
    center.fillna(method='bfill', inplace=True)

    # Note: compute the dispersion off the media
    std = pandas.stats.moments.rolling_std(center, nperiods * 2)
    std.fillna(method='bfill', inplace=True)
    cutoff = nstd * std

    df[(df < (center-cutoff)) | (df > (center+cutoff))] = np.nan
    return df


def main():
    import argparse
    parser = argparse.ArgumentParser(__doc__.strip())

    parser.add_argument('-p', '--period', default='1min', help="Period to resample at")
    parser.add_argument('-k', '--outlier-cutoff', action='store', type=int, default=5,
                        help="Cutoff (in SD) for outlier removal.")

    group = parser.add_argument_group("Options useful during debugging")
    group.add_argument('--maxrows', type=int, help="Maximum nb. of rows to process.")
    group.add_argument('--maxfiles', type=int, help="Maximum nb. of files to process.")
    group.add_argument('--only', action='append', default=[], help="Process only these files.")

    parser.add_argument('root', help='Root directory where the data files are located')
    parser.add_argument('outbase', help='Base of filenames to output (without extension)')

    opts = parser.parse_args()

    outdir = dirname(opts.outbase)
    if not exists(outdir):
        os.makedirs(outdir)

    # Process all the files in a single set.
    dframes = []
    for n, fn in enumerate(sorted(getfiles(opts.root, opts.maxfiles))):
        basefn = basename(fn)

        # Cull empty files.
        if getsize(fn) == 0:
            print "(Skipping empty file)"
            continue

        # Cull files for debugging.
        if opts.only and basefn not in opts.only:
            continue

        # Skip non-source files.
        mo = re.match('XBee.*_(.*)_', basefn)
        if not mo:
            continue

        print "Processing '%s' (%s)" % (fn, n)

        # Extract the sensor ID.
        vname = mo.group(1)

        # Read the CSV file directly; note that we could tell Pandas to use the
        # first column as the index for the returned DataFrame, but the index
        # values aren't unique in the csv files, so we'll clean that up after.
        #
        # This returns a DataFrame with a row index and two columns: time and value.
        df = read_csv(fn, names=['time', vname],
                      converters={vname: parse_float},
                      nrows=opts.maxrows)

        # Drop the non-unique values in the time column and then make that the index.
        df = df.drop_duplicates(['time'], take_last=True)
        index = pandas.DatetimeIndex(df['time'])
        df = df.set_index(index, verify_integrity=True)

        # Sort the values according to the index.
        df.sort()

        dframes.append(df)

    # Concatenate all of the value columns in the given data frames.
    df = pandas.concat(dframes, axis=1)

    # df.to_csv(join(opts.root, 'raw_concatenated.csv'))

    # Resample to a more manageable time resolution.
    df = df.resample(opts.period, how='mean')

    # Remove outliers beyond a cutoff point.
    #global ax; ax = plt.gca()
    df = remove_outliers(df, nperiods=10, nstd=opts.outlier_cutoff)

    # Fill in the missing values.
    df.fillna(method='ffill', inplace=True)

    # Write out the aggregated/resampled data.
    df.to_csv('%s.csv' % opts.outbase)

    # Plot the data.
    source = normpath(opts.root).split(os.sep)[-1]
    title = '%s (%s)' % (source, opts.period)
    df.plot(title=title)
    plt.legend([])
    plt.tight_layout()
    plt.savefig('%s.png' % opts.outbase, dpi=600)


if __name__ == '__main__':
    main()
