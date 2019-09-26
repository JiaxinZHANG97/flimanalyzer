#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri May  4 19:37:11 2018

@author: khs3z
"""

import numpy as np
import pandas as pd
import core.preprocessor
import numbers

TRP_RZERO = 2.1
ONE_SIXTH = 1.0/6 

def nadph_perc(nadph_t2):
    return ((nadph_t2 - 1500) / (4400-1500)) * 100

def nadh_perc(nadph_perc):
    return 100.0 - nadph_perc

def tm(a1perc, t1, a2perc, t2):
    return ((a1perc * t1) + (a2perc * t2))/100
    
def trp_Eperc_1(trp_tm, const=3100):
    if const != 0:
        return (1.0 - (trp_tm / const)) * 100
    else:
        return np.NaN
 
def trp_Eperc_2(trp_t1, trp_t2):
    if trp_t2 != 0:
        return (1.0 - (trp_t1 / trp_t2)) * 100
    else:
        return np.NaN

def trp_Eperc_3(trp_t1, const=3100):
    if const != 0:
        return (1.0 - (trp_t1 / const)) * 100
    else:
        return np.NaN

def trp_r(trp_Eperc):
    # 0<= Eperc < 100
    if trp_Eperc != 0:
        t = (100.0/trp_Eperc - 1)
        if t >= 0:
            return TRP_RZERO * t ** ONE_SIXTH
    return np.NaN
    
def ratio(v1, v2):
    if (v2 != 0):
        # force float values
        return float(v1) / v2
    else:
        return np.NaN

class dataanalyzer():
    
    def __init__(self):
        self.additional_columns = []
        self.functions = {
                'NADPH %': [nadph_perc,['NAD(P)H t2']],
                'NAD(P)H tm': [tm,['NAD(P)H a1[%]','NAD(P)H t1','NAD(P)H a2[%]','NAD(P)H t2']],
                'NAD(P)H a2[%]/a1[%]': [ratio, ['NAD(P)H a2[%]', 'NAD(P)H a1[%]']],
                'NADH %': [nadh_perc,['NADPH %']],
                'NADPH/NADH': [ratio, ['NADPH %', 'NADH %']],
                'trp tm': [tm,['trp a1[%]','trp t1','trp a2[%]','trp t2']],
                'trp E%1': [trp_Eperc_1,['trp tm']],
                'trp E%2': [trp_Eperc_2,['trp t1','trp t2']],
                'trp E%3': [trp_Eperc_3,['trp t1']],
                'trp r1': [trp_r,['trp E%1']],
                'trp r2': [trp_r,['trp E%2']],
                'trp r3': [trp_r,['trp E%3']],
                'trp a1[%]/a2[%]': [ratio, ['trp a1[%]', 'trp a2[%]']],
                'FAD tm': [tm,['FAD a1[%]','FAD t1','FAD a2[%]','FAD t2']],
                'FAD a1[%]/a2[%]': [ratio, ['FAD a1[%]', 'FAD a2[%]']],
                'FAD photons/NAD(P)H photons': [ratio, ['FAD photons', 'NAD(P)H photons']],
                'NAD(P)H tm/FAD tm': [ratio,['NAD(P)H tm','FAD tm']],
                'FLIRR (NAD(P)H a2[%]/FAD a1[%])': [ratio, ['NAD(P)H a2[%]', 'FAD a1[%]']],
                'NADPH a2/FAD a1': [ratio, ['NAD(P)H a2', 'FAD a1']],
                }
        self.rangefilters = {}

        
    def add_functions(self, newfuncs):
        if newfuncs is not None:
            self.functions.update(newfuncs)

            
    def add_rangefilters(self, newfilters):
        if newfilters is not None:
            self.rangefilters.update(newfilters)

            
    def set_rangefilters(self, newfilters):
        if newfilters is not None:
            self.rangefilters = newfilters
    
        
    def get_rangefilters(self):
        return self.rangefilters
    
    
    def add_columns(self, ncols):
        if ncols is not None:
            self.additional_columns.extend(ncols)
    
    
    def get_additional_columns(self):
        return self.additional_columns
    
    
    def columns_available(self, data, args):
        for arg in args:
            if not isinstance(arg, numbers.Number) and data.get(arg) is None:
                return False
        return True
    
    
    def calculate(self, data, inplace=True):
        calculated = []
        skipped = []
        if not inplace:
            data = data.copy()
        for acol in self.additional_columns:
            #if acol == 'NADH tm':
                #(NADH-a1% * NADH-t1) + (NADH-a2% * NADH-t2)/100
            if acol in self.functions:
                #NAD(P)H % = (('NAD(P)H t2') - 1500 / (4400-1500)) *100
                func = np.vectorize(self.functions[acol][0])
                colargs = self.functions[acol][1]
                if not self.columns_available(data, colargs):
                    skipped.append(self.functions[acol])
                    continue
                data[acol] = func(*np.transpose(data[colargs].values))
                calculated.append(self.functions[acol])
            else:
                skipped.append(self.functions[acol])
        return data, calculated, skipped


    def apply_filter(self, data, dropna=True, onlyselected=False, inplace=True, dropsonly=False):
        usedfilters = []
        skippedfilters = []
        alldroppedrows = []
        if data is None:
            return None, usedfilters, [[k,self.rangefilters[k]] for k in self.rangefilters], len(alldroppedrows)
        print "dataanalyzer.apply_filter: filtering %d rows, %d filters, onlyselected=%s" % (data.shape[0], len(self.rangefilters), str(onlyselected))
        #if dropna:
        #    droppedrows = np.flatnonzero(data.isna().any(axis=0))
        #    usedfilters.append(['drop NaN', 'any', droppedrows])
        #    print "    dropped NaN", len(droppedrows)
        #    alldroppedrows.extend(droppedrows)
        for acol in sorted(self.rangefilters):
            rfilter = self.rangefilters[acol]
            if (onlyselected and not rfilter.is_selected()) or not self.columns_available(data, [acol]):
                skippedfilters.append([acol,rfilter])
                continue
            low,high = rfilter.get_range()
            print "    filtering %s: %f, %f" % (acol, low, high)
            if dropna:
                droppedrows = np.flatnonzero((data[acol] != data[acol]) | (data[acol] > high) | (data[acol] < low))
            else:    
                droppedrows = np.flatnonzero((data[acol] > high) | (data[acol] < low))
            #data = data[(data[acol] >= low) & (data[acol] <= high)]
            usedfilters.append([acol, rfilter, droppedrows])
            alldroppedrows.extend(droppedrows)
        
#        alldroppedrows = sorted(np.unique(alldroppedrows), reverse=True)
        alldroppedrows = np.unique(alldroppedrows)
        filtereddata = data
        if not dropsonly:
            filtereddata = data.drop(alldroppedrows, inplace=inplace)
        return filtereddata, usedfilters, skippedfilters, len(alldroppedrows)
    
    
    def summarize_data(self, title, data, cols, groups=None, aggs=['count', 'min', 'max', 'median', 'mean', 'std']):
        summaries = {}
        
        if cols is None or len(cols) == 0:
            return summaries
        
        for header in cols:
            #categories = [col for col in self.flimanalyzer.get_importer().get_parser().get_regexpatterns()]
            allcats = [x for x in groups]
            allcats.append(header)
            dftitle = title + ', '.join(groups) + " : " + header
            if groups is None or len(groups) == 0:
                summaries[dftitle] = data[allcats].agg(aggs)
            else:                
                summaries[dftitle] = data[allcats].groupby(groups).agg(aggs)
        return summaries

    
    def categorize_data(self, data, col, bins=[-1, 1], labels='1', normalizeto={}, grouping=[], dropna=True, use_minvalue=False, joinmaster=True, add_ascategory=True, category_colheader='Category'):
        if not grouping or len(grouping) == 0:
            return
        ref_cols = [c for c in grouping if c in normalizeto]
        non_ref_cols = [c for c in grouping if c not in ref_cols]
        ref_values = tuple([normalizeto[c] for c in ref_cols])
        unstack_levels = [grouping.index(c) for c in ref_cols]
        print "COLS TO UNSTACK, ref_cols=%s, non_ref_cols=%s, unstack_levels=%s, ref_values=%s" % (str(ref_cols), str(non_ref_cols), str(unstack_levels), str(ref_values))
#        med = data.groupby(grouping)[col].median().unstack(level=0)#.rename(columns=str).reset_index()
        print data.groupby(grouping)[col].median()
        med = data.groupby(grouping)[col].median().unstack(unstack_levels)#.rename(columns=str).reset_index()
        # keep only columns where topindex matches the outermost ref_value for unstacking
        print "unstacked med\n", med
        
        # TEST
#        xs_ref = med.xs(ref_values,level=ref_cols, axis=1, drop_level=True)
#        xs_meds = med.xs(ref_values[0],level=ref_cols[0], axis=1, drop_level=False)
#        print "crossection ref:\n", xs_ref
#        print "crossection others:\n", xs_meds
#        xs_norms = xs_meds.apply(lambda df:(df-xs_ref)/xs_ref * 100)
#        print "crossection norms:\n", xs_norms
        
        
        med = med.loc[:,ref_values[0]]
        if dropna:
            med.dropna(axis=0, inplace=True)
        print 'med\n', med
        print 'med.index\n', med.index
        
#        reorderedcols = [c for c in ref_cols] # [normalizeto]
#        reorderedcols.extend([c for c in med.columns.values if c != ref_cols])
#        med = med[reorderedcols]
#        med = med.xs(level=reorderedcols,axis=1)
#        print 'med[reorderedcols]',med.head()    

        # pick single multi-indexed column
        ref_median = med.loc[:,ref_values[1:]].iloc[:,0]
#        ref_median = med.xs(ref_values[1:], level=ref_cols[1:], axis=1)
        print 'ref_median\n', ref_median, 
        print 'ref_median.index\n', ref_median.index

#        rel = med.iloc[:,1:].apply(lambda df:(df-med[ref_cols])/med[ref_cols]*100)
#        rel = med.apply(lambda df:(df-ref_median)/ref_median * 100, axis=0, raw=True)
        rel = med.apply(lambda df:(df-ref_median)/ref_median * 100)
        print 'rel.columns.values\n', rel.columns.values
        print 'rel.index\n',rel.index
        print 'ref_values[1:]\n', ref_values[1:]
        if len(ref_values) == 2:
            rel.drop(ref_values[1], axis=1, inplace=True)
        else:    
            rel.drop(ref_values[1:], level=0, axis=1, inplace=True)
        print 'rel\n', rel
        print 'rel.index\n',rel.index
        rel.columns = [c+' rel %' for c in rel.columns.values]
        rel['min rel %'] = rel.min(axis=1)
        rel['max rel %'] = rel.max(axis=1)
        print 'rel after addition of min %/max %\n', rel
        print 'rel.index after addition of min %/max %\n', rel.index
        # create category for each column
        for c in rel.columns.values:
            rel['Cat %s' %c] = pd.cut(rel[c], bins=bins, labels=labels)#.rename('cat %s' % col)
#        med = pd.merge(med,rel, on=non_ref_cols)
        if use_minvalue:
            rel[category_colheader] = rel['Cat min rel %']    
        else:    
            rel[category_colheader] = rel['Cat max rel %']    
        print 'med after rel merge', med
        med = pd.merge(med.rename(columns=str).reset_index(),rel.rename(columns=str).reset_index(), on=non_ref_cols)
        if joinmaster:
            if category_colheader in data.columns.values:
                data = data.drop([category_colheader], axis=1)
            print "DATA.INDEX",data.index
            print "REL[COL].INDEX",rel[category_colheader].index
            joineddata = data.join(rel[category_colheader], on=non_ref_cols).rename(index=str, columns={category_colheader: category_colheader})
            print joineddata.dtypes
            if add_ascategory:
                joineddata[category_colheader].astype('category')
                unassigned = 'unassigned'
                joineddata[category_colheader] = joineddata[category_colheader].cat.add_categories([unassigned])
                print "CATEGORIES",joineddata[category_colheader].cat.categories
                joineddata = joineddata.fillna(value={category_colheader:unassigned})
            print joineddata.columns.values    
            return med, core.preprocessor.reorder_columns(joineddata)
        else:
            return med, data

        




