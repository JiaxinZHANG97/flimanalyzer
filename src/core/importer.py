#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri May  4 02:53:40 2018

@author: khs3z
"""

import os
import glob
import pandas as pd

from parser import  defaultparser
import core.preprocessor

class dataimporter():
    
    def __init__(self):
        self.files = []
        self.defaultdelimiter = '\t'
        self.data = pd.DataFrame()
        self.excluded_files = []
        self.parser = defaultparser()
        self.preprocessor = None
       
    def set_parser(self,parser):
        if parser is not None:
            self.parser = parser
        
    def get_parser(self):
        return self.parser
    
    def set_preprocessor(self,preprocessor):
        self.preprocessor = preprocessor
        
    def get_preprocessor(self):
        return self.preprocessor
    
        
    def set_defaultdelimiter(self, delimiter):
        if delimiter is not None:
            self.defaultdelimiter = delimiter

    
    def get_defaultdelimiter(self):
        return self.defaultdelimiter

    
    def set_files(self, files, extensions=['.txt'], exclude=None, sort=True):
        if exclude is None:
            exclude = self.excluded_files
        self.files = []
        self.add_files(files,extensions,exclude,sort)
        
        
    def set_excluded_files(self, exclude):
        if exclude is None:
            exclude = []
        self.excluded_files = exclude


    def get_excluded_files(self):
        return self.excluded_files
        
    
    def add_files(self, files, extensions=['.txt'], exclude=None, sort=True):
        if files is None:
            return None,0
        if exclude is None:
            exclude = self.excluded_files
        added_files = 0
        skipped_files = 0
        files = [os.path.abspath(f) for f in set(files)]
        ext = tuple(extensions)
        for f in files:
            if os.path.isdir(f):
                filesindir = glob.glob(os.path.join(f,'*'))
                added,skipped = self.add_files(filesindir, extensions=extensions, exclude=exclude)
                added_files += added
                skipped_files += skipped
            else:
                if (os.path.isfile(f) and f.endswith(ext) and not f in self.files and not os.path.basename(f) in exclude):
#                    print('adding',f)
                    self.files.append(f)
                    added_files += 1
                else:
                    skipped_files += 1
        if sort:            
            self.files = sorted(self.files)
        return (added_files, skipped_files)

    
    def remove_files(self, rfiles):
        print "remove",rfiles
        if rfiles is not None:
            self.files = [f for f in self.files if f not in rfiles]
        
        
    def remove_allfiles(self):
        self.files = []
        
        
    def get_files(self):
        return self.files

    
    def get_reserved_categorycols(self, parser=None):
        if parser is None:
            parser = self.parser
        rcatnames = ['Cell line', 'Category', 'FOV', 'Well', 'Cell', 'Treatment', 'Time', 'Compartment']    
        rcatnames.extend([key for key in parser.get_regexpatterns()])
        return sorted(set(rcatnames))
    
    
    def import_data(self, delimiter=None, hparser=None, preprocessor=None, nrows=None): 
        if delimiter is None:
            delimiter = self.defaultdelimiter    
        if hparser is None:
            hparser = self.parser
        if preprocessor is None:
            preprocessor = self.preprocessor
        dflist = []  
        readfiles = 0
        fheaders = []
        for f in self.files:
            if not os.path.isfile(f):
                continue
            # columns defined by parser regexpatterns will use 'category' as dtype
            category_dtypes = {col:'object' for col in self.get_reserved_categorycols(hparser)}
            df = pd.read_table(f, delimiter=delimiter, engine='python', dtype=category_dtypes, nrows=nrows)
            headers = hparser.parsefilename(f)
            for key in headers:
                df[key] = headers[key]
            if preprocessor is not None:
                df,ch = preprocessor.rename_headers(df)
                df,dl = preprocessor.drop_columns(df)
            dflist.append(df)
            fheaders.extend(list(headers.keys()))
            readfiles+=1
        if len(dflist) == 0:
            return #None, None, None
        else:
            fheaders = set(fheaders)
            df = pd.concat(dflist)
            df.reset_index(inplace=True, drop=True)
            allheaders = list(df.columns.values)
            print self.get_reserved_categorycols(hparser)
            for key in self.get_reserved_categorycols(hparser):
                if key in allheaders:
                    df[key] = df[key].astype('category')
            core.preprocessor.reorder_columns(df)
            return df, readfiles, fheaders 

    
