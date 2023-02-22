from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mpd

class MPLVis(object):

    def plot_temp(self, use_year=None, dpi=300):

        if not use_year:
            use_year = self.now.year

        # Simplified variable names for raw/stats table
        raw = self.raw
        stats = self.stats

        # Get a list of days in 2000 for x axis
        dates = {"month": stats.index.get_level_values(0).values,
                 "day": stats.index.get_level_values(1).values,
                 "year": 2000}
        dates = pd.to_datetime(dates)

        # Create the plot
        fig = plt.figure(figsize=(8,4))
        ax = plt.axes()

        for dcat, color in [('TMAX', 'r'), ('TMIN', 'b')]:
            # Transparent filled areas for some ranges of data max values
            plt.fill_between(dates,
                            stats[(dcat, 'min')], stats[(dcat, 'max')],
                            color=color, alpha=0.1, linewidth=0)
            
            # Average +/- one StDev
            plt.fill_between(dates, 
                             stats[(dcat, 'mean')] - stats[(dcat, 'std')], 
                             stats[(dcat, 'mean')] + stats[(dcat, 'std')],
                             color=color, alpha=0.15, linewidth=0)

            # Plot for the average high/low temps as thin black lines
            plt.plot(dates, stats[(dcat, 'mean')].values, 'k', lw=0.5)

        # Plot most recent year
        mask = raw.index.year == use_year
        # Make sure that there are actually some data points in this year
        if mask.sum() != 0:
            masked = raw[mask]
            maskdates = pd.to_datetime({"day": masked.index.day,
                                    "month": masked.index.month,
                                    "year": 2000})
            plt.plot(maskdates, masked.TMAX, c='r', lw=0.5)
            plt.plot(maskdates, masked.TMIN, c='b', lw=0.5)

        # And we might want to see a vertical line for today 
        plt.axvline(datetime(2000, self.now.month, self.now.day),
                c='0.1', lw=0.5)

        # Uncheck this command for uniform y-axes limits, otherwise they will
        # auto-set based on data
        #plt.ylim(-50, 110)
        plt.ylabel('Temp')
        plt.xlim(datetime(2000, 1, 1), datetime(2001, 1, 1))
        # The default x label will contain the year, which we don't want
        # This only plots the month
        ax.xaxis.set_major_formatter(mpd.DateFormatter('%b'))
        plt.xlabel('Month')

        plt.tight_layout()

        # Save the plot figure
        plt.savefig(self.folder / 'yearly_plot.png', dpi=dpi)

        plt.show()

    def plot_prcp(self, use_year=None, ptype='PRCP', dpi=300):

        if not use_year:
            use_year = self.now.year

        # Simplified variable names for raw/stats table
        raw = self.raw
        stats = self.stats

        # Get a list of days in 2000 for x axis
        dates = {"month": stats.index.get_level_values(0).values,
                 "day": stats.index.get_level_values(1).values,
                 "year": 2000}
        dates = pd.to_datetime(dates)

        # Calculate some values that will be used in the plots
        av_csum = stats[(ptype, 'mean')].cumsum()
        rgb = raw[ptype].groupby(raw.index.year) 
        csums = rgb.cumsum() 
        csgb = csums.groupby(csums.index.year)
        totals = {}

        # Create the plot here
        fig = plt.figure(figsize=(8,4))
        ### FIRST PLOT ###
        ax1 = plt.subplot(3,3,(1,5))

        # Plot all other years as transparent, thin blue lines
        for year, df in csgb:
            # Need to do this for incomplete years
            maskdates = pd.to_datetime({"day": df.index.day,
                                    "month": df.index.month,
                                    "year": 2000})
            plt.plot(maskdates, df, c='b', lw=0.5, alpha=0.1)
            totals[year] = df.iloc[-1]

        totals = pd.Series(totals)
            
        # Plot for the average precipitation as thin black lines
        plt.plot(dates, av_csum.values, 'k', lw=1, label='Average')

        # Plot most recent year
        mask = raw.index.year == use_year
        # Make sure that there are actually some data points in this year
        if mask.sum() != 0:
            masked = raw[mask]
            maskdates = pd.to_datetime({"day": masked.index.day,
                                    "month": masked.index.month,
                                    "year": 2000})
            plt.plot(maskdates, masked[ptype].cumsum(), c='r', lw=1, 
                    label=str(use_year))

        # And we might want to see a vertical line for today 
        plt.axvline(datetime(2000, self.now.month, self.now.day),
                c='0.1', lw=0.5)

        # Uncheck this command for uniform y-axes limits, otherwise they will
        # auto-set based on data
        #plt.ylim(-30, 110)
        plt.ylabel('Sum')
        plt.xlim(datetime(2000, 1, 1), datetime(2001, 1, 1))
        # Remove the ticks for the x axis
        #ax1.xaxis.set_major_formatter(mpd.DateFormatter('%b'))
        plt.tick_params('x', bottom=False, labelbottom=False)
        plt.legend(loc='upper left')


        ### SECOND PLOT ###
        ax2 = plt.subplot(3,3,(7,8))
        # Some transparent bars for some ranges of data
        # The max range
        plt.bar(dates, stats[(ptype, 'max')], width=1.,
                        color='b', alpha=0.1,)
        # Average + StDev
        plt.bar(dates, stats[(ptype, 'mean')] + stats[(ptype, 'std')],
                         width=1., color='b', alpha=0.15,)

        # Plot for the average as black bars
        plt.bar(dates, stats[(ptype, 'mean')], color='k',)

        # Plot most recent year
        mask = raw.index.year == use_year
        # Make sure that there are actually some data points in this year
        if mask.sum() != 0:
            masked = raw[mask]
            maskdates = pd.to_datetime({"day": masked.index.day,
                                    "month": masked.index.month,
                                    "year": 2000})
            plt.bar(maskdates, masked[ptype], color='r',)

        # And we might want to see a vertical line for today 
        plt.axvline(datetime(2000, self.now.month, self.now.day),
                c='0.1', lw=0.5)

        # Uncheck this command for uniform y-axes limits, otherwise they will
        # auto-set based on data
        #plt.ylim(-30, 110)
        plt.ylabel('Daily')
        plt.xlim(datetime(2000, 1, 1), datetime(2001, 1, 1))
        # The default x label will contain the year, which we don't want
        # This only plots the month
        ax2.xaxis.set_major_formatter(mpd.DateFormatter('%b'))
        plt.xlabel('Month')

        ### Third Plot ###
        ax3 = plt.subplot(3,3,(3,9))

        # Plot the totals as a histogram
        bins = np.arange(int(totals.min()//10)*10, 
                        int(totals.max()//10)*10 + 15, 
                        5)
        plt.hist(totals, bins=bins, color='b', alpha=0.5)

        # Plot the average, current year as vertical lines
        plt.axvline(totals[use_year], color='r', lw=1)
        plt.axvline(totals.mean(), color='k', lw=1)

        plt.ylabel('Count')
        plt.xlabel('Inches Tot.')

        plt.tight_layout()

        plt.savefig(self.folder / 'precip_plot.png', dpi=dpi)

        plt.show()
