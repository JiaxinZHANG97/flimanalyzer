#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri May  4 04:02:09 2018

@author: khs3z
"""

import os
import re

def get_available_parsers(pkdir='core.parser'):
    import pkgutil
    import importlib
    for (module_loader, name, ispkg) in pkgutil.iter_modules([pkdir]):
        importlib.import_module('.' + name, __package__)
    parser_classes = {cls.__name__: cls for cls in defaultparser.__subclasses__()}        
    return parser_classes

    
def instantiate_parser(fullname):
    import importlib
    namesplit = fullname.rpartition('.')
    if len(namesplit) != 3:
        return None
    modulename = fullname.rpartition('.')[0]
    classname = fullname.rpartition('.')[2]
    try:
        module = importlib.import_module(modulename)
        class_ = getattr(module, classname)
        parserinstance = class_()
    except Exception:
        parserinstance = None
    return parserinstance    



class defaultparser(object):

    def __init__(self):
        #self.pattern = {
        #        'Treatment':r'[-](\d+?)',
        #        'FOV':r'[-]\d*(\D+?)[_-]',
        #        'Cell':r'[-].*?[_-].*?[_](\d*?)\.'}

        self.init_patterns()
        self.compile_patterns()

    def init_patterns(self):
        self.regexpatterns = {}
        
    def compile_patterns(self):
        if self.regexpatterns is not None and len(self.regexpatterns) > 0:
            self.compiledpatterns = {rp:re.compile(self.regexpatterns[rp]) for rp in self.regexpatterns}
        else:
            self.compiledpatterns = {}    

            
    def get_regexpatterns(self):
        return self.regexpatterns

        
    def set_regexpatterns(self, patterns):
        self.regexpatterns = patterns
        self.compile_patterns()        

        
    def parsefilename(self, fname):
        components = {'Directory':os.path.dirname(fname), 'File':os.path.basename(fname)}
        for pattern in self.regexpatterns:    
            # convert \ in windows style path to / in POSIX style
            match = re.search(self.regexpatterns[pattern], fname.replace("\\",'/'))
            if match is not None:
                matchstr = match.group(1)
                if match.group(1) == '':
                    components[pattern] = '?'
                else:
                    components[pattern] = str(matchstr)
        return components       



class no_parser(defaultparser):

    def set_regexpatterns(self, patterns):
        pass
    
    
    def parsefilename(self, fname):
        return {}

    
        
class compartment_fov_treatment_cell_parser(defaultparser):
    
    def init_patterns(self):
        self.regexpatterns = {
                'Compartment':r'.*/(.*?)/',
                'FOV':r'.*/.*?[_-](.*?)[_-]',
                'Treatment':r'.*/.*?[_-].*?[_-](.*?)[_-]',
                'Cell':r'.*/.*?[_-].*?[_-].*?[_-](\d*?)\.'}


        
class compartment_treatment_fov_cell_parser(defaultparser):
    
    def init_patterns(self):
        self.regexpatterns = {
                'Compartment':r'.*/(.*?)/',
                'Treatment':r'.*/.*?[_-](.*?)[_-]',
                'FOV':r'.*/.*?[_-].*?[_-](.*?)[_-]',
                'Cell':r'.*/.*?[_-].*?[_-].*?[_-](\d*?)\.'}



class fov_treatment_cell_parser(defaultparser):
    
    def init_patterns(self):
        self.regexpatterns = {
                'FOV':r'.*/.*?[_-](.*?)[_-]',
                'Treatment':r'.*/.*?[_-].*?[_-](.*?)[_-]',
                'Cell':r'.*/.*?[_-].*?[_-].*?[_-](\d*?)\.'}
#                'FOV':r'[_-](.*?)[_-]',
#                'Treatment':r'[_-].*?[_-](.*?)[_-]',
#                'Cell':r'[_-].*?[_-].*?[_-](\d*?)\.'}


        
class treatment_fov_cell_parser(defaultparser):
        
    def init_patterns(self):
        self.regexpatterns = {
                'Treatment':r'.*/.*?[_-](.*?)[_-]',
                'FOV':r'.*/.*?[_-].*?[_-](.*?)[_-]',
                'Cell':r'.*/.*?[_-].*?[_-].*?[_-](\d*?)\.'}




#class hyphenparser(defaultparser):
#    
#    def init_patterns(self):
#        self.regexpatterns = {
#                'Treatment':r'[-](\d+?)',
#                'FOV':r'[-]\d*(\D+?)[_-]',
#                'Cell':r'[-].*?[_-].*?[_](\d*?)\.'}

