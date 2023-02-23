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

    def plot_daily_temp(self, day, month, cat='TMIN', dpi=300):
        mask = (self.raw.index.month == month) & (self.raw.index.day == day)
        data = self.raw.loc[mask, cat]
        years = data.index.year

        ydiff = self.raw.loc[mask, 'yeardiff']
        slope = self.stats.loc[(month, day), (cat, 'slope')]
        icept = self.stats.loc[(month, day), (cat, 'icept')]
        line = slope*ydiff + icept

        color = 'b' if cat == 'TMIN' else 'b'

        ## TOP PLOT ##
        plt.subplot(3, 1, (1,2))
        plt.plot(years, data, 'o-', color=color, alpha=0.5, mew=0)
        plt.plot(years, line, '0.3', lw=1)
        plt.tick_params(bottom=False, labelbottom=False,)
        plt.ylabel('Temp (deg F)')
        label = 'Low' if cat == 'TMIN' else 'High'
        plt.title(f'{label} Temp Trend for {month}/{day}')

        ## BOTTOM PLOT ##
        plt.subplot(3, 1, 3)
        plt.plot(years, data-line, 'ko-', alpha=0.5, mew=0)
        plt.ylabel('Residuals')
        plt.xlabel('Year')

        plt.tight_layout()

        plt.savefig(self.folder / 'daily_temp_plot.png', dpi=dpi)

        plt.show()

    def plot_daily_trends(self, p=0.05, dpi=300):
        fig = plt.figure(figsize=(8,4))

        ax_tl = plt.subplot(2, 4, (1,3))
        ax_tr = plt.subplot(2, 4, 4)
        ax_bl = plt.subplot(2, 4, (5,7))
        ax_br = plt.subplot(2, 4, 8)

        cats = {'TMAX': [ax_tl, ax_tr, 'r',],
                  'TMIN': [ax_bl, ax_br, 'b'],
               }
        slope_lims = []
        bin_lims = []

        for cat in cats:
            left, right, color = cats[cat]
            slopes = self.stats.loc[:, (cat, 'slope')]
            pvals = self.stats.loc[:, (cat, 'p_slope')]
            dates = pd.to_datetime({'day': slopes.index.get_level_values(1),
                           'month': slopes.index.get_level_values(0),
                           'year': 2000})
            
            # Yearly plot
            left.axhline(0, color='0.3', lw=0.5)
            left.plot(dates, slopes, 'o', color=color, alpha=0.5, ms=2)
            left.plot(dates, slopes.where(pvals < p), 'o', color='k', 
                    alpha=0.7, ms=2.5)

            # Histogram
            right.axhline(0, color='0.3', lw=0.5)
            # Plot the regular histogram
            n, bins, bars = right.hist(slopes, color=color, 
                    orientation='horizontal', alpha=0.5)
            # Plot significant slopes with a slightly darker shading
            right.hist(slopes.where(pvals < p), bins, alpha=0.7, color='k',
                    rwidth=1, orientation='horizontal')
            
            slope_lims.append( slopes.abs().max() )
            bin_lims.append( n.max() )

        y_lim = np.max(slope_lims)*1.2
        x_lim = np.max(bin_lims)*1.2

        ax_tl.tick_params('x', bottom=False, labelbottom=False)
        ax_tl.set_ylim(-y_lim, y_lim)
        ax_tl.set_title('Temperatur Trend by Date', size=12, color='0.3')

        ax_tr.tick_params(left=False, labelleft=False, bottom=False, 
                labelbottom=False)
        ax_tr.set_ylim(-y_lim, y_lim)
        ax_tr.set_xlim(0, x_lim)
        ax_tr.set_title('Trend Histogram', size=12, color='0.3')

        ax_bl.xaxis.set_major_formatter(mpd.DateFormatter('%b'))
        ax_bl.set_xlabel('Month')
        ax_bl.set_ylim(-y_lim, y_lim)

        ax_br.tick_params(left=False, labelleft=False)
        ax_br.set_ylim(-y_lim, y_lim)
        ax_br.set_xlim(0, x_lim)
        ax_br.set_xlabel('Count')

        fig.supylabel('Daily Trend Slopes (deg F/year)', size=12, 
                color='0.3')

        plt.tight_layout()

        plt.savefig(self.folder / 'daily_trends.png', dpi=dpi)

        plt.show()
