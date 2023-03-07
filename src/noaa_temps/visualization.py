from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mpd

class MPLVis(object):

    def plot_temp(self, use_year=None, trends=True, smooth=15, 
                show=True, save=True, dpi=300):
        if not use_year:
            use_year = self.end_date

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
            # Collect some of the data that are needed
            mean = stats[(dcat, 'mean')]
            std = stats[(dcat, 'std')]
            mn = stats[(dcat, 'min')]
            mx = stats[(dcat, 'max')]
            if trends:
                slopes = stats[(dcat, 'slope')]
                icept = stats[(dcat, 'icept')]
                # Calculate some trend data
                final_year = self.now.year - self.start_date
                trend = final_year*slopes + icept

            # Smooth the data if necessary
            if smooth:
                mean = self._lin_smooth(mean, smooth)
                std = self._lin_smooth(std, smooth)
            if smooth and trends:
                icept = self._lin_smooth(icept, smooth)
                trend = self._lin_smooth(trend, smooth)
                
            # Transparent filled areas for extreme data
            mxs = plt.fill_between(dates, mn, mx, color=color, 
                                   alpha=0.1, linewidth=0)

            # Transparent average +/- one StDev
            sts = plt.fill_between(dates, mean - std, mean + std,
                             color=color, alpha=0.2, linewidth=0)
            
            # Plot for the average high/low temps as thin black lines
            mns, = plt.plot(dates, mean, 'k', lw=0.5)
            if trends:
                ics, = plt.plot(dates, icept, ':', c='0.2', lw=0.5)
                tds, = plt.plot(dates, trend, '--', c='0.2', lw=0.5)

        # Start some lists for legend info
        leg_art = [mns,]
        leg_str = ['mean',]
        if trends:
            leg_art.extend([ics, tds])
            leg_str.extend([f'linear est. {self.start_date}', 
                    f'linear est. {self.now.year}',])
            
        # Plot most recent year
        mask = raw.index.year == use_year
        # Make sure that there are actually some data points in this year
        if mask.sum() != 0:
            masked = raw[mask]
            maskdates = pd.to_datetime({"day": masked.index.day,
                                    "month": masked.index.month,
                                    "year": 2000})
            hg, = plt.plot(maskdates, masked.TMAX, c='r', lw=0.5)
            lw, = plt.plot(maskdates, masked.TMIN, c='b', lw=0.5)
            
            leg_art.extend([hg, lw,])
            leg_str.extend([f'{use_year} high', f'{use_year} low',])

        # Add a legend to the figure
        leg_art.extend([sts, mxs])
        leg_str.extend(['mean + std', 'extreme values'])
        plt.legend(leg_art, leg_str, loc='lower center', fontsize=8, 
                labelcolor='0.3')

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

        if save:
            plt.savefig(self.folder / f'yearly_plot.png', 
                    dpi=dpi)
        if show:
            plt.show()
        plt.close()

    def plot_prcp(self, use_year=None, ptype='PRCP', n_missing=10, 
                show=True, save=True, dpi=300):

        if not use_year:
            use_year = self.end_date

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
            # Skip years that do not have enough data points
            if len(df) < (365-n_missing): continue

            # Need to redo this every time for incomplete years
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
        plt.axvline(totals.mean(), color='k', lw=1)
        mask = raw.index.year == use_year
        # Make sure that there are actually some data points in this year
        if mask.sum() != 0:
            masked = raw[mask]
            plt.axvline(masked[ptype].sum(), color='r', lw=1)

        plt.ylabel('Count')
        plt.xlabel('Inches Tot.')

        plt.tight_layout()

        if save:
            plt.savefig(self.folder / f'precip_plot.png', 
                    dpi=dpi)
        if show:
            plt.show()
        plt.close()

    def plot_daily_temp(self, month, day, temp_type='both', p=0.05, 
                show=True, save=True, dpi=300):
        # Create the figure and axes depending on number of plots
        cats = []
        if temp_type == 'both':
            fig = plt.figure(figsize=(8,4))
            cats.append(['TMIN', plt.subplot(3, 2, (1,3)),
                        plt.subplot(3, 2, 5)])
            cats.append(['TMAX', plt.subplot(3, 2, (2, 4)),
                        plt.subplot(3, 2, 6),])
        elif temp_type in ['TMIN', 'TMAX']:
            fig = plt.figure()
            cats.append([temp_type, plt.subplot(3, 1, (1,2)),
                        plt.subplot(3, 1, 3),])
        else:
            raise ValueError(f'{temp_type} is not a valid entry')

        # Plot the data
        for cat, top, bottom in cats:
            mask = (self.raw.index.month == month) & (self.raw.index.day == day)
            data = self.raw.loc[mask, cat]
            years = data.index.year

            ydiff = self.raw.loc[mask, 'yeardiff']
            slope = self.stats.loc[(month, day), (cat, 'slope')]
            icept = self.stats.loc[(month, day), (cat, 'icept')]
            line = slope*ydiff + icept
            
            pval = self.stats.loc[(month, day), (cat, 'p_slope')]
            lstyle = '-' if pval < p else '--'
            color = 'b' if cat == 'TMIN' else 'r'

            ## TOP PLOT ##
            top.plot(years, data, 'o-', color=color, alpha=0.5, mew=0, ms=4)
            top.plot(years, line, lstyle, color='0.3', lw=1)
            top.tick_params(bottom=False, labelbottom=False,)

            ## BOTTOM PLOT ##
            resid = data-line
            bottom.plot(years, resid, 'ko-', alpha=0.5, mew=0, ms=4)
            bottom.set_xlabel('Year')
            resid_max = 1.15*resid.abs().max()
            bottom.set_ylim(-resid_max, resid_max) 

        cats[0][1].set_ylabel('Temp (deg F)')
        cats[0][2].set_ylabel('Residuals')

        title = f'Temperature Trends for {month}/{day}'
        if temp_type == 'both':
            cats[0][1].set_title('Daily Lows', fontsize=12, color='0.3')
            cats[1][1].set_title('Daily Highs', fontsize=12, color='0.3')
            fig.suptitle(title, fontsize=14, color='0.3')
        else:
            label = 'Low' if temp_type == 'TMIN' else 'High'
            title = f'{label} {title}'
            cats[0][1].set_title(title)

        plt.tight_layout()

        if save:
            plt.savefig(self.folder / f'daily_temp_plot_{temp_type}.png', 
                    dpi=dpi)
        if show:
            plt.show()
        plt.close()

    def plot_daily_trends(self, p=0.05, show=True, save=True, dpi=300):
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
        ax_tl.set_title('Temperature Trends by Date', size=12, color='0.3')

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

        if save:
            plt.savefig(self.folder / 'daily_trends.png', dpi=dpi)
        if show:
            plt.show()
        plt.close()

    def plot_temp_diffs(self, ndays=90, show=True, save=True, dpi=300):
        fig = plt.figure(figsize=(8,4))
        top = plt.subplot(211)
        bot = plt.subplot(212)

        for cat, ax in [('TMAX', top), ('TMIN', bot)]:
            recent = self.raw[[cat]].iloc[-ndays:].reset_index()
            dates = recent['date']
            recent = recent.set_index([recent.date.dt.month, recent.date.dt.day])\
                            .rename_axis(index=['month', 'day'])[cat]
            index = recent.index

            mean = self.stats.loc[index, (cat, 'mean')]
            std = self.stats.loc[index, (cat, 'std')]
            mint = self.stats.loc[index, (cat, 'min')] - mean
            maxt = self.stats.loc[index, (cat, 'max')] - mean
            resid = (recent - mean)
            
            color = 'r' if cat == 'TMAX' else 'b'
            ax.fill_between(dates, mint, maxt, color=color, alpha=0.1, lw=0)
            ax.fill_between(dates, -std, std, color=color, alpha=0.2, lw=0)
            ax.axhline(0, lw=0.5, color='0.2')
            ax.plot(dates, resid, 'o-', color=color, alpha=0.5, mew=0, ms=4)
            
        top.tick_params(bottom=False, labelbottom=False)
        top.set_title(f'Temperature Deviations for Previous {ndays} Days',
                color='0.3', size=12)
        top.set_ylabel('High Temps', color='0.3')
        bot.set_ylabel('Low Temps', color='0.3')
        bot.xaxis.set_major_formatter(mpd.DateFormatter('%d-%b'))
        bot.set_xlabel('Dates', color='0.3')
        fig.supylabel('Difference (Actual - Mean)', color='0.3')

        plt.tight_layout()

        if save:
            plt.savefig(self.folder / 'temp_diffs.png', dpi=dpi)
        if show:
            plt.show()
        plt.close()
