#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat May  5 14:53:15 2018

@author: khs3z
"""


import pandas as pd
import numpy as np
from matplotlib.font_manager import FontProperties
import seaborn as sns

def normalize(value, totalcounts):
    return value / totalcounts


def bindata(binvalues, binedges, groupnames):
    df = pd.DataFrame()
    df['bin edge low'] = binedges[:-1]
    df['bin edge high'] = binedges[1:]
    if len(binvalues.shape) == 1:
        df[groupnames[0]] = binvalues
    else:    
        for i in range(len(binvalues)):
            df[groupnames[i]] = binvalues[i]
    return df


def grouped_meanbarplot_new(ax, data, column, groups=[], dropna=True, pivot_level=1, **kwargs):
    if data is None or not column in data.columns.values:
        return None, None
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()    
    
    if groups is None:
        groups = []
    if len(groups)==0:
        mean = pd.DataFrame(data={'all':[data[column].mean()]}, index=[column])#.to_frame()
        std = pd.DataFrame(data={'all':[data[column].std()]}, index=[column])#.to_frame()
        mean.plot.barh(ax=ax, xerr=std)#,figsize=fsize,width=0.8)
    else:    
        sns.barplot(data=data[column], hue=groups[0]);
            
    
def grouped_meanbarplot(ax, data, column, groups=[], dropna=True, pivot_level=1, **kwargs):
    import matplotlib.pyplot as plt
    plt.rcParams.update({'figure.autolayout': True})
    if data is None or not column in data.columns.values:
        return None, None
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()    
    
    if groups is None:
        groups = []
    if len(groups)==0:
        mean = pd.DataFrame(data={'all':[data[column].mean()]}, index=[column])#.to_frame()
        std = pd.DataFrame(data={'all':[data[column].std()]}, index=[column])#.to_frame()
        ticklabels = ''#mean.index.values
        mean.plot.barh(ax=ax, xerr=std)#,figsize=fsize,width=0.8)
    else:    
        cols = [c for c in groups]
        cols.append(column)
        if dropna:
            groupeddata = data[cols].dropna(how='any', subset=[column]).groupby(groups)
        else:    
            groupeddata = data[cols].groupby(groups)
#        groupeddata = data[cols].groupby(groups)
#        print data.reset_index().set_index(groups).index.unique()
        #df.columns = [' '.join(col).strip() for col in df.columns.values]
        mean = groupeddata.mean()
        std = groupeddata.std()
        no_bars = len(mean)
        if pivot_level < len(groups):
            unstack_level = range(pivot_level)
            print "PIVOTING:", pivot_level, unstack_level
            mean = mean.unstack(unstack_level)
            std = std.unstack(unstack_level)
            mean = mean.dropna(how='all', axis=0)
            std = std.dropna(how='all', axis=0)
        ticklabels = mean.index.values
        bwidth = 0.8# * len(ticklabels)/no_bars 
        fig.set_figheight(1 + no_bars//8)
        fig.set_figwidth(6)
        mean.plot.barh(ax=ax,xerr=std,width=bwidth)           
    
    
    if len(groups) > 1:
        # ticklabels is an array of tuples --> convert individual tuples into string 
#        ticklabels = [', '.join(l) for l in ticklabels]
        ticklabels = [str(l).replace('\'','').replace('(','').replace(')','') for l in ticklabels]
        h, labels = ax.get_legend_handles_labels()
        labels = [l.encode('ascii','ignore').split(',')[1].strip(' \)') for l in labels]
        ax.set_ylabel = ', '.join(groups[pivot_level:])
        no_legendcols = (len(groups)//30 + 1)
        chartbox = ax.get_position()
        ax.set_position([chartbox.x0, chartbox.y0, chartbox.width * (1-0.2 * no_legendcols), chartbox.height])
#        ax.legend(loc='upper center', labels=grouplabels, bbox_to_anchor= (1 + (0.2 * no_legendcols), 1.0), fontsize='small', ncol=no_legendcols)
        ax.legend(labels=labels,  title=', '.join(groups[0:pivot_level]), loc='upper center', bbox_to_anchor= (1 + (0.2 * no_legendcols), 1.0), fontsize='small', ncol=no_legendcols)
        legend = ax.get_legend()
        ax.add_artist(legend)
    else:
        legend = ax.legend()
        legend.remove()
    ax.set_title('Mean %s' % column)
    ax.set_yticklabels(ticklabels)

    #fig.tight_layout(pad=1.5)
    plt.rcParams.update({'figure.autolayout': False})
    return fig,ax
    

def histogram(ax, data, column, groups=[], normalize=None, **kwargs):
    import matplotlib.pyplot as plt
    plt.rcParams.update({'figure.autolayout': True})

    if data is None or not column in data.columns.values:
        return None, None
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure()    
    if groups is None:
        groups = []
                
    newkwargs = kwargs.copy()
    #newkwargs.update({'range':(minx,maxx)})
    totalcounts = data[column].dropna(axis=0,how='all').count()
    pltdata = []
    weights = []
    groupnames = []
    if len(groups)==0:
        groupnames.append('all')
        pltdata = data[column].values
        newkwargs.update({'label':'all'})
        if normalize is not None:
            weights = np.ones_like(data[column].values)/float(totalcounts) * normalize
    else:
        groupeddata = data.groupby(groups)
        newkwargs.update({'label':list(groupeddata.groups)})
        for name,group in groupeddata:
            groupnames.append(name)
            pltdata.append(group[column].values)
            totalcounts = group[column].count()            
            if normalize is not None:
                weights.append(np.ones_like(group[column].values)/float(totalcounts) * normalize)
    if normalize is not None:
        if normalize == 100:
            ax.set_ylabel('relative counts [%]')
        else:
            ax.set_ylabel('relative counts (norm. to %.1f)' % normalize)
            
        newkwargs.update({
                'weights':weights, 
                'normed':False
                })
    else:
        ax.set_ylabel('counts')
#    if newkwargs[range] is not None:    
#        ax.set_xlim(newkwargs[range[0]],newkwargs[range[1]])
    ax.set_xlabel(column)
    ax.set_title(', '.join(groups) + " : " + column)
    fig.set_size_inches(8,8)

    binvalues,binedges,patches = ax.hist(pltdata, **newkwargs)    
    if len(groups) > 0 and len(binvalues) > 1:
        h, labels = ax.get_legend_handles_labels()
        #labels = [l.encode('ascii','ignore').split(',')[1].strip(' \)') for l in labels]
        labels = [l.replace('\'','').replace('(','').replace(')','') for l in labels]
        no_legendcols = (len(binvalues)//30 + 1)
        chartbox = ax.get_position()
        ax.set_position([chartbox.x0, chartbox.y0, chartbox.width* (1-0.2 * no_legendcols), chartbox.height])
        ax.legend(labels=labels, loc='upper center', title=', '.join(groups), bbox_to_anchor= (1 + (0.2 * no_legendcols), 1.0), fontsize='small', ncol=no_legendcols)

    plt.rcParams.update({'figure.autolayout': False})    
    return  np.array(binvalues), binedges, groupnames, fig, ax,

    
def stacked_histogram(ax, data, column, groups=[], minx=None, maxx=None, normalize=None, **kwargs):
    import matplotlib.pyplot as plt

    if data is None or not column in data.columns.values:
        return None, None
    if ax is None:
        fig, ax = plt.Figure()
    else:
        fig = ax.get_figure()    

    totalcounts = data[column].dropna(axis=0,how='all').count()
    newkwargs = kwargs.copy()
    newkwargs.update({'stacked':True, 'range':(minx,maxx)})
    pltdata = []
    weights = []
    if groups is None or len(groups)==0:
        pltdata = data[column].values
        newkwargs.update({'label':'all'})
        if normalize is not None:
            weights = np.ones_like(data[column].values)/float(totalcounts) * normalize
    else:
        groupeddata = data.groupby(groups)
        newkwargs.update({'label':list(groupeddata.groups)})
        for name,group in groupeddata:
            pltdata.append(group[column].values)            
            if normalize is not None:
                weights.append(np.ones_like(group[column].values)/float(totalcounts) * normalize)
    if normalize is not None:
        if normalize == 100:
            ax.set_ylabel('relative counts [%]')
        else:
            ax.set_ylabel('relative counts (norm. to %.1f)' % normalize)
            
        newkwargs.update({
                'weights':weights, 
                'normed':False
                })
    else:
        ax.set_ylabel('counts')
    ax.set_xlim(minx,maxx)
    ax.set_xlabel(column)
    ax.hist(pltdata, **newkwargs)
    ax.legend()
    return fig, ax