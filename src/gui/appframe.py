#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 21:00:30 2018

@author: khs3z
"""

import wx
import os
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
import itertools
import pandas as pd


import core.parser
import core.plots
import core.preprocessor
import gui.dialogs
from core.preprocessor import defaultpreprocessor
from core.importer import dataimporter
from core.filter import RangeFilter
from gui.delimpanel import DelimiterPanel
from gui.datapanel import PandasFrame
from gui.dicttablepanel import DictTable
from gui.listcontrol import AnalysisListCtrl, FilterListCtrl, EVT_FILTERUPDATED, EVT_ANALYSISUPDATED
from gui.mpanel import MatplotlibFrame
from gui.dialogs import ConfigureCategoriesDlg
from gui.events import DataUpdatedEvent, EVT_DATAUPDATED, EVT_DU_TYPE

CONFIG_DELIMITER = 'delimiter'
CONFIG_HEADERS = 'headers'
CONFIG_EXCLUDE_FILES = 'exclude files'
CONFIG_DROP_COLUMNS = 'drop columns'
CONFIG_CALC_COLUMNS = 'calculate columns'
CONFIG_FILTERS = 'filters'
CONFIG_PARSERCLASS = 'parser'
CONFIG_ANALYSIS = 'histograms'
CONFIG_CATEGORIES = 'categories'
CONFIG_SCATTER = 'scatter'

from wx.lib.newevent import NewEvent

ImportEvent, EVT_IMPORT = NewEvent()
ApplyFilterEvent, EVT_APPLYFILTER = NewEvent()
DataUpdateEvent, EVT_UPDATEDATA = NewEvent()


    
class TabImport(wx.Panel):
    
    def __init__(self, parent, pwindow, flimanalyzer, config):
        self.pwindow = pwindow
        self.flimanalyzer = flimanalyzer
        
        self.config = config
        self.delimiter = config[CONFIG_DELIMITER]
        self.parser = config[CONFIG_PARSERCLASS]
        self.drop_columns = config[CONFIG_DROP_COLUMNS]
        self.excluded_files = config[CONFIG_EXCLUDE_FILES]
        self.calc_columns = config[CONFIG_CALC_COLUMNS]
        self.filters = config[CONFIG_FILTERS]
        self.headers = config[CONFIG_HEADERS]
        self.rawdata = None
        super(TabImport,self).__init__(parent)
                
        delimiter_label = wx.StaticText(self, wx.ID_ANY, "Column Delimiter:")
        self.delimiter_panel = DelimiterPanel(self, self.delimiter)
        
        parser_label = wx.StaticText(self, wx.ID_ANY, "Filename Parser:")
        #self.parser_field = wx.TextCtrl(self, wx.ID_ANY, value=self.parser)
        self.avail_parsers = core.parser.get_available_parsers()
        sel_parser = self.avail_parsers.get(self.parser)
        if sel_parser is None:
            sel_parser = self.avail_parsers.keys()[0]
        self.parser_chooser = wx.ComboBox(self, -1, value=sel_parser, choices=sorted(self.avail_parsers.keys()), style=wx.CB_READONLY)

        self.load_button = wx.Button(self, wx.ID_ANY, "Load Config")
        self.load_button.Bind(wx.EVT_BUTTON, self.LoadConfig)

        self.save_button = wx.Button(self, wx.ID_ANY, "Save Config")
        self.save_button.Bind(wx.EVT_BUTTON, self.SaveConfig)

        self.sel_files_label = wx.StaticText(self, wx.ID_ANY, "Selected Files: %9d" % len(flimanalyzer.get_importer().get_files()), (20,20))    
        self.files_list = wx.ListBox(self, wx.ID_ANY, style=wx.LB_EXTENDED|wx.LB_HSCROLL|wx.LB_NEEDED_SB|wx.LB_SORT)

        exclude_label = wx.StaticText(self, wx.ID_ANY, "Exclude Files:")
        self.exclude_files_list = wx.TextCtrl(self, wx.ID_ANY, value="\n".join(self.excluded_files), style=wx.TE_MULTILINE|wx.EXPAND)
        
        rename_label = wx.StaticText(self, wx.ID_ANY, "Rename Columns:")
        self.rgrid = wx.grid.Grid(self, -1)#, size=(200, 100))
        self.rgrid.SetDefaultColSize(200,True)
        self.headertable = DictTable(self.headers, headers=['Original name', 'New name'])
        self.rgrid.SetTable(self.headertable,takeOwnership=True)
        self.rgrid.SetRowLabelSize(0)

        drop_label = wx.StaticText(self, wx.ID_ANY, "Drop Columns:")
        self.drop_col_list = wx.TextCtrl(self, wx.ID_ANY, size=(200, 100), value="\n".join(self.drop_columns), style=wx.TE_MULTILINE|wx.EXPAND)

        self.add_button = wx.Button(self, wx.ID_ANY, "Add Files")
        self.add_button.Bind(wx.EVT_BUTTON, self.AddFiles)

        self.remove_button = wx.Button(self, wx.ID_ANY, "Remove Files")
        self.remove_button.Bind(wx.EVT_BUTTON, self.RemoveFiles)

        self.reset_button = wx.Button(self, wx.ID_ANY, "Reset")
        self.reset_button.Bind(wx.EVT_BUTTON, self.Reset)

        self.preview_button = wx.Button(self, wx.ID_ANY, "Preview")
        self.preview_button.Bind(wx.EVT_BUTTON, self.Preview)

        self.import_button = wx.Button(self, wx.ID_ANY, "Import")
        self.import_button.Bind(wx.EVT_BUTTON, self.ImportFiles)


        configsizer = wx.FlexGridSizer(2,2,5,5)
        configsizer.AddGrowableCol(1, 1)
        colsizer = wx.FlexGridSizer(2,2,5,5)
        colsizer.AddGrowableCol(0, 2)
        colsizer.AddGrowableCol(1, 1)
        colsizer.AddGrowableRow(1, 1)
        cbuttonsizer = wx.BoxSizer(wx.VERTICAL)
        lbuttonsizer = wx.BoxSizer(wx.VERTICAL)
        filesizer = wx.FlexGridSizer(2,2,5,5)
        filesizer.AddGrowableCol(0,1)
        filesizer.AddGrowableCol(1,3)
        filesizer.AddGrowableRow(1,1)
        topleftsizer = wx.FlexGridSizer(2,1,5,5)
        topleftsizer.AddGrowableCol(0, 1)
        topleftsizer.AddGrowableRow(1, 1)
        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        bottomsizer = wx.BoxSizer(wx.HORIZONTAL)
        box = wx.BoxSizer(wx.VERTICAL)
        
        configsizer.Add(delimiter_label, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        configsizer.Add(self.delimiter_panel, 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        configsizer.Add(parser_label, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
#        configsizer.Add(self.parser_field, 1, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
        configsizer.Add(self.parser_chooser, 1, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
        
        colsizer.Add(rename_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        colsizer.Add(drop_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        colsizer.Add(self.rgrid, 2, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        colsizer.Add(self.drop_col_list, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        cbuttonsizer.Add(self.load_button, 1, wx.EXPAND|wx.ALL, 5)
        cbuttonsizer.Add(self.save_button, 1, wx.EXPAND|wx.ALL, 5)
        
        lbuttonsizer.Add(self.add_button, 1, wx.EXPAND|wx.ALL, 5)
        lbuttonsizer.Add(self.remove_button, 1, wx.EXPAND|wx.ALL, 5)
        lbuttonsizer.Add(self.reset_button, 1, wx.EXPAND|wx.ALL, 5)
        lbuttonsizer.Add(self.preview_button, 1, wx.EXPAND|wx.ALL, 5)
        lbuttonsizer.Add(self.import_button, 1, wx.EXPAND|wx.ALL, 5)

        filesizer.Add(exclude_label, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5)
        filesizer.Add(self.sel_files_label, 2, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5)
        filesizer.Add(self.exclude_files_list, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        filesizer.Add(self.files_list, 2, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        
        topleftsizer.Add(configsizer, 1, wx.EXPAND|wx.ALL, 5)
        topleftsizer.Add(colsizer, 1, wx.EXPAND|wx.ALL, 5)
        
        topsizer.Add(topleftsizer, 1, wx.EXPAND|wx.ALL, 5)
        topsizer.Add(cbuttonsizer, 0, wx.ALL, 5)
        
        bottomsizer.Add(filesizer, 1, wx.EXPAND|wx.ALL, 5)
        bottomsizer.Add(lbuttonsizer,0, wx.ALL, 5)
        
#        leftsizer.Add(configsizer, 0, wx.EXPAND, 0)
#        leftsizer.Add(colsizer, 0, wx.EXPAND, 0)
#        leftsizer.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)
#        leftsizer.Add(filesizer, 0, wx.EXPAND, 0)

#        topsizer.Add(cbuttonsizer, 0, wx.ALL, 5)

#        toptopsizer.Add(leftsizer)
#        toptopsizer.Add(cbuttonsizer)
        box.Add(topsizer, 1, wx.EXPAND|wx.ALL, 5)
        box.Add(wx.StaticLine(self), 0, wx.ALL|wx.EXPAND, 5)
        box.Add(bottomsizer, 1, wx.EXPAND|wx.ALL, 5)
#        box.Add(lbuttonsizer, 0, wx.ALL, 5)
        #self.SetBackgroundColour('green')
        
        self.SetSizerAndFit(box)
        
        self.update_files(0)
        
        self.rgrid.Bind(wx.EVT_SIZE, self.OnRGridSize)
        
    
    def OnRGridSize(self, event):
        self.rgrid.SetDefaultColSize(event.GetSize().GetWidth()/self.rgrid.GetTable().GetNumberCols(),True)
        self.rgrid.Refresh()
        
    
    def update_files(self, no_newfiles):
        importer = self.flimanalyzer.get_importer()
        files = importer.get_files()
        self.sel_files_label.SetLabel("Selected Files: %9d" % len(files))
        self.files_list.Set(files)
        
            
    def LoadConfig(self, event):
        print "load"


    def SaveConfig(self, event):
        print "save"
        
    
    def AddFiles(self, event):
        with wx.FileDialog(self, "Add Raw Data Results", wildcard="txt files (*.txt)|*.txt",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            # Proceed loading the file chosen by the user
            paths = fileDialog.GetPaths()
            importer = self.flimanalyzer.get_importer()
            filecount = len(importer.get_files())
            for path in paths:
                if os.path.isdir(path):
                    importer.add_files([path], exclude=[])
                else:
                    excluded = self.exclude_files_list.GetValue().encode('ascii','ignore').split('\n')              
                    importer.add_files([path], exclude=excluded)
            new_filecount = len(importer.get_files())
            self.update_files(new_filecount-filecount)
#            self.statusbar.SetStatusText("Added %d file(s)" % (new_filecount - filecount))
 
    
    def RemoveFiles(self, event):
        selected = self.files_list.GetSelections()
        if selected is not None and len(selected) > 0: 
            selectedfiles = [self.files_list.GetString(idx) for idx in selected]
            importer = self.flimanalyzer.get_importer()
            filecount = len(importer.get_files())
            importer.remove_files(selectedfiles)
            self.update_files(len(importer.get_files())-filecount)
 
    
    def Reset(self, event):
        importer = self.flimanalyzer.get_importer()
        filecount = len(importer.get_files())
        self.flimanalyzer.get_importer().remove_allfiles()
        self.update_files(len(importer.get_files())-filecount)
 
    
    def configure_importer(self, importer):
#        hparser = core.parser.instantiate_parser(self.parser_field.GetValue())
        parsername = self.parser_chooser.GetStringSelection()
        hparser = core.parser.instantiate_parser('core.parser.' + parsername)
        if hparser is None:
            print "COULD NOT INSTANTIATE PARSER:", parsername 
            return
        dropped = self.drop_col_list.GetValue().encode('ascii','ignore').split('\n')
        if len(dropped)==1 and dropped[0]=='':
            dropped = None

        preprocessor = defaultpreprocessor()
        preprocessor.set_replacementheaders(self.headertable.GetDict())
        preprocessor.set_dropcolumns(dropped)
        importer.set_parser(hparser)
        importer.set_preprocessor(preprocessor)

        
    def Preview(self, event):
        files = self.flimanalyzer.get_importer().get_files()
        if len(files) > 0:
            delimiter = self.delimiter_panel.get_delimiters()
            importer = dataimporter()
            self.configure_importer(importer)
            selected = self.files_list.GetSelections()
            if selected is None or len(selected)==0:
                importer.set_files([files[0]])
            else:
                print "PREVIEWING: delimiter=%s, %s" % (delimiter,self.files_list.GetString(selected[0]))
                importer.set_files([self.files_list.GetString(selected[0])])
            rawdata, readfiles, headers = importer.import_data(delimiter=delimiter)
            rawdata = self.calc_additional_columns(rawdata) 
#            rawdata = core.preprocessor.reorder_columns(rawdata,headers)
            rawdata = core.preprocessor.reorder_columns(rawdata)
            
            previewrows = 10
            if len(rawdata) < previewrows:
                previewrows = len(previewrows)
            frame = PandasFrame(self, "Import Preview (single file): showing %d of %d rows" %(previewrows,len(rawdata)), rawdata[:previewrows])
            frame.Show(True)
        
    
    def update_listlabel(self):
        label = "Selected Files: %9d" % len(self.flimanalyzer.get_importer().get_files())
        if self.rawdata is not None:
            label += "; imported %d rows, %d columns" % (self.rawdata.shape[0], self.rawdata.shape[1])
        self.sel_files_label.SetLabel(label)    


    def calc_additional_columns(self, data):
        analyzer = self.flimanalyzer.get_analyzer()
        analyzer.add_columns(self.calc_columns)
        data,_,_ = analyzer.calculate(data)
        return data
    
                    
    def ImportFiles(self, event):
        importer = self.flimanalyzer.get_importer()
        files = self.flimanalyzer.get_importer().get_files()
        if len(files) > 0:
            delimiter = self.delimiter_panel.get_delimiters()
    #        self.statusbar.SetStatusText("Importing raw data from %d file(s)..." % len(importer.get_files()))
            self.configure_importer(importer)
            importer.set_files(files)
            self.rawdata, readfiles, parsed_headers = importer.import_data(delimiter=delimiter)
            self.rawdata = self.calc_additional_columns(self.rawdata)    
#            self.rawdata = core.preprocessor.reorder_columns(self.rawdata,first=parsed_headers)            
            self.rawdata = core.preprocessor.reorder_columns(self.rawdata)            

            wx.PostEvent(self.pwindow, ImportEvent(rawdata=self.rawdata, importer=importer))
            
            self.update_listlabel()
            if len(files) > 1:
                with wx.FileDialog(self, "Save imported raw data", wildcard="txt files (*.txt)|*.txt", style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as fileDialog:    
                    fileDialog.SetFilename('Master.txt')
                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return
                    fname = fileDialog.GetPath()   
                    try:
                        self.rawdata.to_csv(fname, index=False, sep='\t')
                    except IOError:
                        wx.MessageBox('Error saving imported raw data file %s' % fname, 'Error', wx.OK | wx.ICON_INFORMATION)
#                    UpdateRawDataEvent, EVT_SOME_NEW_EVENT = wx.lib.newevent.NewEvent(self.rawdata)
 #                   evt = UpdateRawDataEvent(rawdata=self.rawdata)
 #                   wx.PostEvent(target, evt)
 
    
       
    
class TabFilter(wx.Panel):
    
    def __init__(self, parent, pwindow, flimanalyzer, config):
        self.flimanalyzer = flimanalyzer
        self.pwindow = pwindow
        self.config = config
        wx.Panel.__init__(self, parent)
        self.rawdata = None
        self.data = None
        self.summary_group = []
        
        self.rgrid_sel_cell = None

        self.rawdatainfo = wx.StaticText(self, -1, "No raw data", (20,20))
        self.datainfo = wx.StaticText(self, -1, "No filtered data", (20,20))
    
        self.selectall_button = wx.Button(self, wx.ID_ANY, "Select All")
        self.selectall_button.Bind(wx.EVT_BUTTON, self.SelectAll)
    
        self.deselectall_button = wx.Button(self, wx.ID_ANY, "Deselect All")
        self.deselectall_button.Bind(wx.EVT_BUTTON, self.DeselectAll)
    
        #self.filter_button = wx.Button(self, wx.ID_ANY, "Apply Filter")
        #self.filter_button.Bind(wx.EVT_BUTTON, self.OnApplyFilter)
    
        self.dropinfo_button = wx.Button(self, wx.ID_ANY, "Info on Drop")
        self.dropinfo_button.Bind(wx.EVT_BUTTON, self.DropInfo)
    
        self.rlabel = wx.StaticText(self, wx.ID_ANY, "Row Filters:")
        #self.init_filtergrid()
        self.init_filterlist()
#        self.filterlist.Bind(wx.EVT_LIST_END_LABEL_EDIT,pwindow.OnFilterUpdate)
                
        buttonsizer = wx.BoxSizer(wx.VERTICAL)
        buttonsizer.Add(self.selectall_button, 0, wx.EXPAND, 0)
        buttonsizer.Add(self.deselectall_button, 0, wx.EXPAND, 0)
        #buttonsizer.Add(self.filter_button, 0, wx.EXPAND, 0)
        buttonsizer.Add(self.dropinfo_button, 0, wx.EXPAND, 0)

        ssizer = wx.BoxSizer(wx.VERTICAL)
        ssizer.Add(wx.StaticText(self, -1, "ROI Count Filter"))

        fsizer = wx.BoxSizer(wx.HORIZONTAL)       
        fsizer.Add(self.filterlist, 3, wx.ALL|wx.EXPAND, 5)
        fsizer.Add(buttonsizer)
        fsizer.Add(ssizer, 1, wx.ALL|wx.EXPAND, 5)

        boxsizer = wx.BoxSizer(wx.VERTICAL) 
        boxsizer.Add(self.rawdatainfo)
        boxsizer.Add(self.datainfo)
        boxsizer.Add(self.rlabel)
        boxsizer.Add(fsizer, 1, wx.EXPAND, 0)
        
        boxsizer.SetSizeHints(self)
        self.SetSizerAndFit(boxsizer)


#    def get_summarygroups(self):
#        cats = self.flimanalyzer.get_importer().get_parser().get_regexpatterns()
#        return ['None', 'Treatment', 'FOV,Treatment', 'Treatment,FOV', 'FOV,Cell,Treatment','Treatment,FOV,Cell']
        
        
    def init_filterlist(self):
        self.filterlist = FilterListCtrl(self, style=wx.LC_REPORT)
        self.filterlist.InsertColumn(0, "Use")
        self.filterlist.InsertColumn(1, "Column")
        self.filterlist.InsertColumn(2, "Min", wx.LIST_FORMAT_RIGHT)
        self.filterlist.InsertColumn(3, "Max", wx.LIST_FORMAT_RIGHT)
        self.filterlist.InsertColumn(4, "Dropped", wx.LIST_FORMAT_RIGHT)
        self.filterlist.SetEditable([False, False, True, True, False])
        self.filterlist.Arrange()


    def SelectAll(self, event):
        self.filterlist.check_items(self.filterlist.GetData(),True)

        
    def DeselectAll(self, event):
        self.filterlist.check_items(self.filterlist.GetData(),False)


#    def init_filtergrid(self):
#        self.rgrid = wx.grid.Grid(self, -1)
#        self.filtertable = FilterTable(self.config[CONFIG_FILTERS])
#        self.rgrid.SetTable(self.filtertable,takeOwnership=True)
#        self.rgrid.SetCellAlignment(1,4,wx.ALIGN_RIGHT,wx.ALIGN_CENTRE,)
#        self.rgrid.SetRowLabelSize(0)
#        self.rgrid.SetColFormatBool(0)
#        self.rgrid.SetColFormatFloat(2,precision=3)
#        self.rgrid.SetColFormatFloat(3,precision=3)
#        self.rgrid.SetSelectionMode(wx.grid.Grid.wxGridSelectCells)
#        self.rgrid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.onSingleSelect)
#        self.rgrid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.onDragSelection)
               
        

#    def OnGroupChanged(self, event):
#        groupindex = event.GetSelection()
#        groupstr = self.get_summarygroups()[groupindex]
#        if groupstr == 'None':
#            self.summary_group = []
#        else:    
#            self.summary_group = groupstr.split(',')
#        print self.summary_group
        
        
#    def onSingleSelect(self, event):
#        """
#        Get the selection of a single cell by clicking or 
#        moving the selection with the arrow keys
#        """
#        self.rgrid_sel_cell = (event.GetRow(),event.GetCol())
#        event.Skip()
        
    
#    def onDragSelection(self, event):
#        """
#        Gets the cells that are selected by holding the left
#        mouse button down and dragging
#        """
#        if self.rgrid.GetSelectionBlockTopLeft():
#            self.rgrid_sel_cell = self.rgrid.GetSelectionBlockTopLeft()[0]
#            bottom_right = self.rgrid.GetSelectionBlockBottomRight()[0]
    
    def update_rawdata(self, rawdata, applyfilters=True):
        self.rawdata = rawdata
        label = "Raw Data:"
        if self.rawdata is not None:
            label += " %d rows, %d columns" % (self.rawdata.shape[0], self.rawdata.shape[1])
        self.rawdatainfo.SetLabel(label)
        self.update_data(None)
#        self.rgrid.GetTable().SetDroppedRows(None)
#        self.rgrid.Refresh()

        categories = list(self.rawdata.select_dtypes(['category']).columns.values)
        print 'COLUMNS WITH CATEGORY AS DTYPE', categories
        if 'Category' in categories:
            print 'CATEGORY VALUES:', sorted(self.rawdata['Category'].unique())
        self.set_filterlist()
        if applyfilters:
            rangefilters = self.filterlist.GetData()
            self.apply_filters(rangefilters)
        
#        self.optionlist.DeleteAllItems()
#        if self.rawdata is not None:
#            datacols =  self.rawdata.select_dtypes(include=[np.number])
#            for header in datacols.columns.values.tolist():
#                self.optionlist.Append([" ", header]) 
#        self.optionlist.SetColumnWidth(0, -2) # LIST_AUTOSIZE_USEHEADER)

         
    def update_data(self, data):
        self.data = data
        label = "Filtered Data:"
        if self.data is not None:
            label += " %d rows, %d columns" % (self.rawdata.shape[0] - len(self.filterlist.get_total_dropped_rows()), self.data.shape[1])
        self.datainfo.SetLabel(label)    

    
    def set_filterlist(self, dropped={}):
        data = self.rawdata
        if data is None:
            return
        datacols =  data.select_dtypes(include=[np.number])
        datacols.columns.values.tolist()
        for key in datacols.columns.values.tolist():
            hconfig = self.config[CONFIG_FILTERS].get(key)
            if hconfig is None:
                self.config[CONFIG_FILTERS][key] = RangeFilter(key,0,100, selected=False)
        self.filterlist.SetData(self.config[CONFIG_FILTERS], dropped, ['Use', 'Column', 'Min', 'Max', 'Dropped'])        


    def apply_filters(self, rangefilters, onlyselected=True, setall=False, dropsonly=False):
        if rangefilters is None:
            return
        analyzer = self.flimanalyzer.get_analyzer()
        analyzer.set_rangefilters(rangefilters)
        #self.data = self.rawdata.copy()
        data, usedfilters, skippedfilters, no_droppedrows = analyzer.apply_filter(self.rawdata,dropna=True,onlyselected=onlyselected,inplace=False, dropsonly=dropsonly)
        print "TabFilter.applyfilters, dropsonly=%s" % str(dropsonly)
        print "\trawdata: rawdata.shape[0]=%d, dropped overall %d rows" % (self.rawdata.shape[0],no_droppedrows)
        print "\tdata: data.shape[0]=%d" % (data.shape[0])
   
        droppedrows = {f[0]:f[2] for f in usedfilters}
        if setall:
            self.filterlist.SetDroppedRows(droppedrows)
        else:    
            self.filterlist.UpdateDroppedRows(droppedrows)
        self.update_data(data)
        if not dropsonly:
            wx.PostEvent(self.pwindow, ApplyFilterEvent(data=self.data))
        return droppedrows, self.filterlist.get_total_dropped_rows()
        
        
#    def OnApplyFilter(self,event):
#        if self.rawdata is None:
#            return
##        rangefilters = self.rgrid.GetTable().GetData()
#        rangefilters = self.filterlist.GetData()
#        self.apply_filters(rangefilters, onlyselected=True, setall=True, dropsonly=False)
        
    
    def DropInfo(self, event):
        if self.rawdata is None:
            return
#        if not self.rgrid.HasFocus or self.rgrid_sel_cell is None:
#            return
#        rowkey = self.rgrid.GetCellValue(self.rgrid_sel_cell[0],1).decode('ascii','ignore')
        selidx = self.filterlist.GetFirstSelected()    
        rowkey = self.filterlist.GetItem(selidx,self.filterlist.get_key_col()).GetText()    
#        rowkey = self.rgrid.GetCellValue(self.rgrid_sel_cell[0],1).decode('ascii','ignore')
        rows = self.filterlist.GetDroppedRows(rowkey)
        if rows is None:
            return
#        rows = self.rgrid.GetTable().GetDroppedRows(rowkey)
        rowdata = self.rawdata.iloc[rows]
#        rpatterns = self.flimanalyzer.get_importer().get_parser().get_regexpatterns()
        rpatterns = self.flimanalyzer.get_importer().get_reserved_categorycols()
        cols = [c for c in rpatterns if c in rowdata.columns.values]
        cols.extend(['Directory','File',rowkey])
        rowdata = core.preprocessor.reorder_columns(rowdata[cols])
        frame = PandasFrame(self, "%s, dropped rows: %d" % (rowkey, len(rows)), rowdata, showindex=False)
        frame.Show(True)
                                    

class TabAnalysis(wx.Panel):
    
    def __init__(self, parent, pwindow, flimanalyzer, config):
        self.flimanalyzer = flimanalyzer
        self.pwindow = pwindow
        self.config = config
        wx.Panel.__init__(self, parent)
        self.rawdata = None
        self.data = None
        self.sel_roigrouping = []
        self.roigroupings = ['None']
        self.pivot_level = 2
        self.category_colheader = 'Category'

        self.rawdatainfo = wx.StaticText(self, -1, "No raw data", (20,20))
        self.datainfo = wx.StaticText(self, -1, "No filtered data", (20,20))

        self.roigroup_combo = wx.ComboBox(self, -1, pos=(50, 170), size=(300, -1), value=self.roigroupings[0], choices=self.roigroupings, style=wx.CB_READONLY)
        self.roigroup_combo.Bind(wx.EVT_COMBOBOX, self.OnRoiGroupingChanged)

        self.analysistype_combo = wx.ComboBox(self, -1, pos=(50, 170), size=(150, -1), value=self.get_analysistypes()[0], choices=self.get_analysistypes(), style=wx.CB_READONLY)
        self.analysistype_combo.Bind(wx.EVT_COMBOBOX, self.OnAnalysisTypeChanged)

        self.datachoices_combo = wx.ComboBox(self, -1, pos=(50, 170), size=(150, -1), value=self.get_datachoices()[0], choices=self.get_datachoices(), style=wx.CB_READONLY)
        self.datachoices_combo.Bind(wx.EVT_COMBOBOX, self.OnDataChoiceChanged)

        self.ctrlgroup_label = wx.StaticText(self, -1, "Reference:")
        self.ctrlgroup_combo = wx.ComboBox(self, -1, pos=(50, 170), size=(150, -1), value='', choices=self.get_ctrlgroupchoices(), style=wx.CB_READONLY)
        self.ctrlgroup_combo.Bind(wx.EVT_COMBOBOX, self.OnCtrlSelChanged)

        self.selectall_button = wx.Button(self, wx.ID_ANY, "Select All")
        self.selectall_button.Bind(wx.EVT_BUTTON, self.SelectAll)
    
        self.deselectall_button = wx.Button(self, wx.ID_ANY, "Deselect All")
        self.deselectall_button.Bind(wx.EVT_BUTTON, self.DeselectAll)
    
        self.show_button = wx.Button(self, wx.ID_ANY, "Show Analysis")
        self.show_button.Bind(wx.EVT_BUTTON, self.ShowAnalysis)
    
        self.save_button = wx.Button(self, wx.ID_ANY, "Save Analysis")
        self.save_button.Bind(wx.EVT_BUTTON, self.SaveAnalysis)
    

        self.set_roigroupings(None)
        self.init_analysislist()
        
        optionsizer = wx.FlexGridSizer(2,4,1,1)
        optionsizer.Add(wx.StaticText(self, -1, "ROI Grouping"), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        optionsizer.Add(wx.StaticText(self, -1, "Analysis Type"), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        optionsizer.Add(wx.StaticText(self, -1, "Data"), 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        optionsizer.Add(self.ctrlgroup_label, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        optionsizer.Add(self.roigroup_combo, 2, wx.EXPAND|wx.ALL, 5)        
        optionsizer.Add(self.analysistype_combo, 1, wx.EXPAND|wx.ALL, 5)        
        optionsizer.Add(self.datachoices_combo, 1, wx.EXPAND|wx.ALL, 5)        
        optionsizer.Add(self.ctrlgroup_combo, 1, wx.EXPAND|wx.ALL, 5)        
        
        buttonsizer = wx.BoxSizer(wx.VERTICAL)
        buttonsizer.Add(self.selectall_button, 0, wx.EXPAND|wx.ALL, 5)
        buttonsizer.Add(self.deselectall_button, 0, wx.EXPAND|wx.ALL, 5)
        buttonsizer.Add(self.show_button, 0, wx.EXPAND|wx.ALL, 5)
        buttonsizer.Add(self.save_button, 0, wx.EXPAND|wx.ALL, 5)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(self.analysislist, 1, wx.EXPAND|wx.ALL, 5)
        hsizer.Add(buttonsizer, 0, wx.ALL, 5)
        
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(self.rawdatainfo, 0, wx.ALL, 5)
        mainsizer.Add(self.datainfo, 0, wx.ALL, 5)
        mainsizer.Add(optionsizer,0, wx.ALL, 5)        
        mainsizer.Add(hsizer, 1, wx.EXPAND|wx.ALL, 5) 
        
        self.SetSizer(mainsizer)
                
        #boxsizer.SetSizeHints(self)
        #self.SetSizerAndFit(boxsizer)
        


    def init_analysislist(self):
        self.analysislist = AnalysisListCtrl(self, style=wx.LC_REPORT)
        self.analysislist.InsertColumn(0, "Analyze")
        self.analysislist.InsertColumn(1, "Column")
        self.analysislist.InsertColumn(2, "Min",  wx.LIST_FORMAT_RIGHT)
        self.analysislist.InsertColumn(3, "Max",  wx.LIST_FORMAT_RIGHT)
        self.analysislist.InsertColumn(4, "Bins",  wx.LIST_FORMAT_RIGHT)
        self.analysislist.SetEditable([False, False, False, False, True])
        self.analysislist.Arrange()
        self.update_analysislist()
        
                    
    def OnRoiGroupingChanged(self, event):
        groupstr = self.roigroup_combo.GetStringSelection()
        print "OnRoiGroupingChanged.GROUPSTR=", groupstr
        if groupstr == 'None':
            self.sel_roigrouping = []
            self.ctrlgroup_label.SetLabelText('Reference: None')
        else:    
            self.sel_roigrouping = groupstr.split(', ')
            self.ctrlgroup_label.SetLabelText('Reference: %s' % self.sel_roigrouping[0])
        print self.sel_roigrouping
        self.update_sel_ctrlgroup()

        
    def OnAnalysisTypeChanged(self, event):
        groupindex = event.GetSelection()
        print "New Analysis Type Selection: %s " % self.get_analysistypes()[groupindex]

                
    def OnDataChoiceChanged(self, event):
        groupindex = event.GetSelection()
        print "New Data Choice Selection: %s " % self.get_datachoices()[groupindex]

                
    def OnCtrlSelChanged(self, event):
        groupindex = event.GetSelection()
        print "New Control  Group Selection: %s " % self.get_ctrlgroupchoices()[groupindex]

                
    def ShowAnalysis(self, event):
        atype = self.analysistype_combo.GetStringSelection()
        print 'TabAnalysis.ShowAnalysis: %s' % atype
        if atype == 'Summary Tables':
            self.show_summary()
        elif atype == 'Mean Bar Plots':
            if len(self.sel_roigrouping) < 4:
                self.show_meanplots()
        elif atype == 'Frequency Histograms':
            if len(self.sel_roigrouping) < 4:
                self.show_freqhisto()
        elif atype == 'Categorize':
            self.show_categorized_data()

        
    def SaveAnalysis(self, event):
        atype = self.analysistype_combo.GetStringSelection()
        print 'TabAnalysis.SaveAnalysis: %s' % atype
        if atype == 'Summary Tables':
            self.save_summary()
        elif atype == 'Mean Bar Plots':
            if len(self.sel_roigrouping) < 4:
                self.save_meanplots()
        elif atype == 'Frequency Histograms':
            if len(self.sel_roigrouping) < 4:
                self.save_freqhisto()
        elif atype == 'Categorize':
            self.save_categorized_data()

     
    def SelectAll(self, event):
        self.analysislist.Freeze()
        for idx in range(self.analysislist.GetItemCount()):
            self.analysislist.CheckItem(idx, True)
        self.analysislist.Thaw()

        
    def DeselectAll(self, event):
        self.analysislist.Freeze()
        for idx in range(self.analysislist.GetItemCount()):
            self.analysislist.CheckItem(idx, False)
        self.analysislist.Thaw()


    def get_currentdata(self):
        if self.datachoices_combo.GetStringSelection() == self.get_datachoices()[0] and self.rawdata is not None:
            return self.rawdata, self.get_datachoices()[0].split(" ")[0]
        elif self.datachoices_combo.GetStringSelection() == self.get_datachoices()[1] and self.data is not None:
            return self.data, self.get_datachoices()[1].split(" ")[0]
        else:
            return None, None


    def update_rangefilters(self, rfilters):
        print "AnalysisTab.update_rangefilters: %d filters to update" % len(rfilters)
        for key in rfilters:
            rfilter = rfilters[key]
            print "\trfilter.get_parameters:", rfilter.get_parameters()
            low = rfilter.get_rangelow()
            high = rfilter.get_rangehigh()
            aconfig = self.config[CONFIG_ANALYSIS].get(rfilter.get_name())
            if aconfig is None:
                print "\tnot found:", rfilter.get_name()
                self.config[CONFIG_ANALYSIS][rfilter.get_name()] = [low,high,100]
            else:                
                print "\told:", rfilter.get_name(), self.config[CONFIG_ANALYSIS][rfilter.get_name()]
                self.config[CONFIG_ANALYSIS][rfilter.get_name()][0] = low
                self.config[CONFIG_ANALYSIS][rfilter.get_name()][1] = high
            print "\tnew:", rfilter.get_name(), self.config[CONFIG_ANALYSIS][rfilter.get_name()]
            self.analysislist.SetRow(rfilter.get_name(),self.config[CONFIG_ANALYSIS][rfilter.get_name()])


    def update_analysislist(self):
        print "TabAnalysis.update_analysislist"
        data, label = self.get_currentdata()
        if data is None:
            return
        datacols =  data.select_dtypes(include=[np.number])
        datacols.columns.values.tolist()
        for header in datacols.columns.values.tolist():
            hconfig = self.config[CONFIG_ANALYSIS].get(header)
            if hconfig is None:
                self.config[CONFIG_ANALYSIS][header] = [0,1,100]
        self.analysislist.SetData(self.config[CONFIG_ANALYSIS], ['Analyze', 'Column', 'Min', 'Max', 'Bins'])        
        
        
    def update_rawdata(self, rawdata):
        print "TabAnalysis.update_rawdata"
        print "\trawdata: rows=%d, cols=%d" % (rawdata.shape[0], rawdata.shape[1])
        self.rawdata = rawdata
        label = "Raw Data:"
        if self.rawdata is not None:
            label += " %d rows, %d columns" % (self.rawdata.shape[0], self.rawdata.shape[1])
        self.rawdatainfo.SetLabel(label)
        self.update_analysislist()
        self.update_data(None)
        currentdata,_ = self.get_currentdata()
        self.set_roigroupings(list(currentdata.select_dtypes(['category']).columns.values))



    def update_data(self, data):
        print "TabAnalysis.update_data"
#        print "\traw data: rows=%d, cols=%d" % (self.rawdata.shape[0], self.rawdata.shape[1])
        self.data = data
        label = "Filtered Data:"
        if self.data is not None:
            print "\tdata: rows=%d, cols=%d" % (self.data.shape[0], self.data.shape[1])
            label += " %d rows, %d columns" % (self.data.shape[0], self.data.shape[1])
#            label += " %d rows, %d columns" % (self.rawdata.shape[0] - self.filterlist.get_total_dropped_rows(), self.data.shape[1])
        else:
            print "\tDATA IS NONE"
        self.datainfo.SetLabel(label)    


    def get_analysistypes(self):
        return ['Summary Tables', 'Mean Bar Plots', 'Frequency Histograms', 'Categorize']
    

    def get_datachoices(self):
        return ['Raw data', 'Filtered Data']
    

    def get_ctrlgroupchoices(self):
        data,label = self.get_currentdata()
        if data is not None and len(self.sel_roigrouping) > 0 and self.sel_roigrouping[0] != 'None':
            uniques = []
 #           col = self.sel_roigrouping[0]
#            for col in self.sel_roigrouping:
            uniques = [sorted(data[col].unique()) for col in self.sel_roigrouping[:self.pivot_level]]
            return [', '.join(item) for item in list(itertools.product(*uniques))]
        else:
            return [' ']
            
        
    def update_sel_ctrlgroup(self):
        if not self.ctrlgroup_combo:
            return
        current_sel = self.ctrlgroup_combo.GetStringSelection()
        choices = self.get_ctrlgroupchoices()
        self.ctrlgroup_combo.Clear()
        self.ctrlgroup_combo.AppendItems(choices)
        if current_sel != '' and current_sel in choices:
            self.ctrlgroup_combo.SetStringSelection(current_sel)
        else:
            self.ctrlgroup_combo.SetSelection(0)
            
        
    def set_roigroupings(self, categories):
        options = ['None']
#        groupings = self.flimanalyzer.get_importer().get_parser().get_regexpatterns()
#        categtories = parser().get_regexpatterns()
        currentdata,label = self.get_currentdata()
        if currentdata is not None and categories is not None:
            categories = [c for c in categories if c in list(currentdata.select_dtypes(['category']).columns.values)]
            for i in range(1,len(categories)+1):
                permlist = list(itertools.permutations(categories,i))
                for p in permlist:
                    options.append(', '.join(p))
        self.roigroupings = options
        current = self.roigroup_combo.GetStringSelection()
        self.roigroup_combo.Clear()
        self.roigroup_combo.AppendItems(self.roigroupings)
        if current in self.roigroupings:
            self.roigroup_combo.SetStringSelection(current)
        else:    
            self.roigroup_combo.SetSelection(0)
        self.OnRoiGroupingChanged(None)
                

    def get_checked_cols(self, data):
        if data is None:
            return None
        selcols = self.analysislist.get_checked_items()
        print "TabAnalysis.get_checked_cols: SELECTED %s" % str(selcols)
        return selcols
#        selindices = self.analysislist.get_checked_indices()
#        datacols =  data.select_dtypes(include=[np.number])
#        numcols = [datacols.columns.values.tolist()[index] for index in selindices]
#        return numcols
    
        
    def create_freq_histograms(self, data, groups):
        histos = {}
        if not gui.dialogs.check_data_msg(data):
            return {}
        cols = self.get_checked_cols(data)
        if cols is None or len(cols) == 0:
            wx.MessageBox('No Measurements selected.', 'Warning', wx.OK)
            return {}
        for header in sorted(cols):
            hconfig = cols[header]
#            hconfig = self.config[CONFIG_ANALYSIS].get(header)
            mrange = (data[header].min(), data[header].max())
            if hconfig is None:
                bins = 100
            else:
                if self.datachoices_combo.GetStringSelection() == self.get_datachoices()[1]:
                    mrange = (hconfig[0],hconfig[1])
                bins = hconfig[2]
            print "\tcreating frequency histogram plot for %s with %d bins" % (header, bins)     
            #categories = [col for col in self.flimanalyzer.get_importer().get_parser().get_regexpatterns()]
            fig, ax = plt.subplots()
            binvalues, binedges, groupnames, fig, ax = core.plots.histogram(ax, data, header, groups=groups, normalize=100, range=mrange, stacked=False, bins=bins, histtype='step')                
            histos[header] = (binvalues, binedges, groupnames, fig,ax)
        return histos

        
    def create_meanbarplots(self, data, groups):
        bars = {}
        if not gui.dialogs.check_data_msg(data):
            return {}
        cols = [c for c in self.get_checked_cols(data)]
        if cols is None or len(cols) == 0:
            wx.MessageBox('No measurements selected.', 'Warning', wx.OK)
            return {}
        for col in sorted(cols):
            print "\tcreating mean bar plot for %s" % (col)
            fig, ax = plt.subplots()
            fig, ax = core.plots.grouped_meanbarplot(ax, data, col, groups=groups)
            bars[col] = (fig,ax)
        return bars


    def create_summaries(self, data, titleprefix='Summary:'):
        if not gui.dialogs.check_data_msg(data):
            return {}
        cols = [c for c in self.get_checked_cols(data)]
        if cols is None or len(cols) == 0:
            wx.MessageBox('No Measurements selected.', 'Warning', wx.OK)
            return {}
            
        summaries = self.flimanalyzer.get_analyzer().summarize_data(titleprefix, data, cols, self.sel_roigrouping, )
        return summaries
        
    
    def create_categorized_data_global(self, data, col, bins=[-1, 1], labels='Cat 1', normalizeto='', grouping=[], binby='xfold'):
        if not grouping or len(grouping) == 0:
            return
        controldata = data[data[grouping[0]] == normalizeto]
        grouped = controldata.groupby(grouping[1:])
        categorydef = self.config[CONFIG_CATEGORIES].get(col)
        if not categorydef:
            print "Using default categories"
            bins = [1.0, 2.0]
            labels = ['cat 1']
        else:
            bins = categorydef[0]
            labels = categorydef[1]
        series = data[col]
        if normalizeto and len(normalizeto) > 0:
            median = grouped[col].median()
            print median.describe()
            median_of_median = median.median()
            print "MEDIAN_OF_MEDIAN: %s %f" % (col, median_of_median)
            xfold_series = series.apply(lambda x: x / median_of_median).rename('x-fold norm ' + col)
            plusminus_series = series.apply(lambda x: x - median_of_median).rename('+/- norm ' + col)
            all_catseries.append(xfold_series)
            all_catseries.append(plusminus_series)
            if binby == 'plusminus':
                catseries = pd.cut(plusminus_series, bins=bins, labels=labels).rename('cat %s (+/-)' % col)
            else:
                catseries = pd.cut(xfold_series, bins=bins, labels=labels).rename('cat %s (x-fold)' % col)
        else:
            catseries = pd.cut(series, bins=bins, labels=labels).rename('cat ' + col)            
        return catseries
    
    
    def save_summary(self):
        currentdata,label = self.get_currentdata()        
        summaries = self.create_summaries(currentdata)
#        summaries = self.flimanalyzer.get_analyzer().summarize_data(title, currentdata, self.sel_roigrouping, self.optionlist.get_checked_indices())
        if summaries is not None and len(summaries) > 0:
            for title in summaries:
                summary_df = summaries[title].reset_index()
                gui.dialogs.save_dataframe(self, "Save summary data", summary_df, '%s-%s.txt' % (title,label), saveindex=False)
       
        
    def show_summary(self):
        currentdata,label = self.get_currentdata()
        summaries = self.create_summaries(currentdata)
        for title in summaries:
            df = summaries[title]
            df = df.reset_index()
            frame = PandasFrame(self, "%s: %s %s" % (title, label, str(currentdata.shape)), df, showindex=False)
            frame.Show(True)


    def show_meanplots(self):
        currentdata, label = self.get_currentdata()
        bars = self.create_meanbarplots(currentdata,self.sel_roigrouping)
        for b in sorted(bars):
            fig,ax = bars[b]
            title = "%s %s" % (label, ax.get_title())
            fig.canvas.set_window_title(title)
            fig.show()
            #frame = MatplotlibFrame(self, title, fig, ax)
            #frame.Show()
        
        
    def save_meanplots(self):
        currentdata, label = self.get_currentdata()
        bars = self.create_meanbarplots(currentdata,self.sel_roigrouping)
        if len(bars) == 0:
            return
        for b in sorted(bars):
            fig,ax = bars[b]
            gui.dialogs.save_figure(self, 'Save Mean Bar Plot', fig, 'Bar-%s-%s.png' % (ax.get_title(), label), legend=ax.get_legend())
                
     
    def show_freqhisto(self):
        currentdata, label = self.get_currentdata()
        histos = self.create_freq_histograms(currentdata,self.sel_roigrouping)
        if histos is None:
            return
        for h in histos:
            binvalues, binedges, groupnames, fig, ax = histos[h]
            title = "%s %s" % (label, ax.get_title())
            fig.canvas.set_window_title(title)
            fig.show()
#            frame = MatplotlibFrame(self, title, fig, ax)
#            frame.Show()
        
        
    def save_freqhisto(self):
        currentdata, label = self.get_currentdata()
        histos = self.create_freq_histograms(currentdata,self.sel_roigrouping)
        if histos is None:
            return
        for h in histos:
            binvalues, binedges, groupnames, fig, ax = histos[h]
            gui.dialogs.save_figure(self, 'Save Frequency Histogram Figure', fig, 'Histo-%s-%s.png' % (ax.get_title(), label))
            bindata = core.plots.bindata(binvalues,binedges, groupnames)
            bindata = bindata.reset_index()
            gui.dialogs.save_dataframe(self, 'Save Frequency Histogram Data Table', bindata, 'Histo-%s-%s.txt' % (ax.get_title(), label), saveindex=False)
                
    
    def create_categorized_data(self,category_colheader='Category'):
        currentdata, label = self.get_currentdata()
        cols = self.get_checked_cols(currentdata)
        ctrl_label = self.ctrlgroup_combo.GetStringSelection()
        grouping = self.sel_roigrouping

        results = {}
        if not gui.dialogs.check_data_msg(currentdata):
            return results, currentdata, label
        if cols is None or len(cols) != 1:
            wx.MessageBox('A single measurement needs to be selected.', 'Warning', wx.OK)
            return results, currentdata, label 
        if  len(grouping) < 1 or ctrl_label == '':
            wx.MessageBox('A Roi grouping needs to be selected.', 'Warning', wx.OK)
            return results, currentdata, label             
        if 'Category' in grouping:
            wx.MessageBox('\'Category\' cannot be used in grouping for categorization analysis.', 'Warning', wx.OK)
            return results, currentdata, label
        if self.analysistype_combo.GetStringSelection == 'Categorize' and len(cols) != 1:
            wx.MessageBox('\'Categorization analysis requires selection of a single measurement.', 'Warning', wx.OK)
            return results, currentdata, label
        if len(self.sel_roigrouping) <= self.pivot_level:
            wx.MessageBox('\'The Roi grouping must include at least %d groups.' % (self.pivot_level + 1), 'Warning', wx.OK)
            return results, currentdata, label
        if len(self.sel_roigrouping[:self.pivot_level]) != len(ctrl_label.split(', ')):
            wx.MessageBox('\'Inconsistent pivot level and control group selection. Try to reset Roi grouping and control group selection.', 'Warning', wx.OK)
            return results, currentdata, label
        
        # example: normalizeto = {'Compartment':'Mito', 'Treatment':'Ctrl'}
        normalizeto = dict(zip(self.sel_roigrouping[:self.pivot_level], ctrl_label.split(', ')))
        
        col = sorted(cols)[0]
        categorydef = self.config[CONFIG_CATEGORIES].get(col)
        if not categorydef:
            bins = [0.0, 1.0, 2.0]
            labels = ['Cat 1', 'Cat 2']
        else:
            bins = categorydef[0]
            labels = categorydef[1]
        dlg = ConfigureCategoriesDlg(self, col, bins, labels) 
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        categorydef = dlg.get_config()
        dlg.Destroy()
        
        self.config[CONFIG_CATEGORIES][col]=[categorydef[0],categorydef[1]]
        cat_med,currentdata = self.flimanalyzer.get_analyzer().categorize_data(currentdata, col, bins=categorydef[0], labels=categorydef[1], normalizeto=normalizeto, grouping=grouping, category_colheader=category_colheader)

        mediansplits = {}
        catcol = 'Category'#currentdata.iloc[:,-1].name
        split_grouping = [catcol]
        split_grouping.extend(self.sel_roigrouping[:(self.pivot_level-1)])
        print "SPLIT GROUPING",split_grouping
        split_data = currentdata.reset_index().groupby(split_grouping)
        for split_name,group in split_data:
            mediansplit_df = group.groupby(grouping).median().dropna()#group.reset_index().groupby(grouping).median().dropna()
            mediansplits[split_name] = mediansplit_df.reset_index()

        if label.startswith('Raw'):
            self.update_rawdata(currentdata)
        elif label.startswith('Filtered'):
            self.update_data(currentdata)   
#        self.set_roigroupings(list(currentdata.select_dtypes(['category']).columns.values))
        event = DataUpdatedEvent(EVT_DU_TYPE, self.GetId())
        event.SetUpdatedData(currentdata, label)
        self.GetEventHandler().ProcessEvent(event)        
    
        return col, cat_med, mediansplits, currentdata, label
    

    def show_categorized_data(self):
        results = self.create_categorized_data(category_colheader=self.category_colheader)
        if results is None:
            return
        col, cat_med, mediansplits, joineddata, label = results
        frame = PandasFrame(self, "Categorized by %s: Median - %s" % (col,label), cat_med, showindex=False)
        frame.Show(True)
        for split_name in sorted(mediansplits):
            median_split = mediansplits[split_name]
            frame = PandasFrame(self, "Split: Medians - Cat %s: %s" % (' '.join(split_name), label), median_split, showindex=False)
            frame.Show(True)
                        
        
    def save_categorized_data(self):
        catcol = self.category_colheader
        results = self.create_categorized_data(category_colheader=catcol)
        if results is None:
            return
        col, cat_med, mediansplits, joineddata, label = results
        gui.dialogs.save_dataframe(self, "Save Master file with new categories", joineddata, "Master-allcategories-%s.txt" % label, saveindex=False)
        gui.dialogs.save_dataframe(self, "Save categorization summary", cat_med, "Categorized-%s-%s.txt" % (col,label), saveindex=False)
        for split_name in sorted(mediansplits):
            median_split = mediansplits[split_name]
            split_label = '-'.join(split_name)
            split_grouping = [catcol]
            split_grouping.extend(self.sel_roigrouping[:(self.pivot_level-1)])
            print "SPLITGROUPING", split_grouping, "SPLITNAME", split_name, "SPLITLABEL", split_label
            gui.dialogs.save_dataframe(self, "Save grouped medians for Cat %s: %s" % (split_label, label), median_split, "Grouped-Medians-Cat_%s-%s.txt" % (split_label,label), saveindex=False)
            
            master_split = joineddata.set_index(split_grouping).loc[split_name,:].reset_index()
            gui.dialogs.save_dataframe(self, "Save master data for Cat %s: %s" % (split_label, label), master_split, "Master-Cat_%s-%s.txt" % (split_label,label), saveindex=False)
                
                
    
class AppFrame(wx.Frame):
    
    def __init__(self, flimanalyzer):
        self.flimanalyzer = flimanalyzer
        self.rawdata = None
        self.data = None
        self.filtereddata = None
        
        super(AppFrame,self).__init__(None, wx.ID_ANY,title="FLIM Data Analyzer")#, size=(600, 500))
        
        self.setup_config()
        
        self.Bind(EVT_IMPORT, self.OnImport)
        self.Bind(EVT_DATAUPDATED, self.OnDataUpdated)
        self.Bind(EVT_APPLYFILTER, self.OnApplyFilter)
        self.Bind(EVT_FILTERUPDATED, self.OnRangeFilterUpdated)
        self.Bind(EVT_ANALYSISUPDATED, self.OnAnalysisUpdated)
 
        # Create a panel and notebook (tabs holder)
#        panel = wx.Panel(self)
#        nb = wx.Notebook(panel)
        nb = wx.Notebook(self)
 
        # Create the tab windows
        self.importtab = TabImport(nb, self, self.flimanalyzer, self.config)
        self.filtertab = TabFilter(nb, self, self.flimanalyzer, self.config)
        self.analysistab = TabAnalysis(nb, self, self.flimanalyzer, self.config)
 
        # Add the windows to tabs and name them.
        nb.AddPage(self.importtab, "Import")
        nb.AddPage(self.filtertab, "Filter")
        nb.AddPage(self.analysistab, "Analyze")
        
#        self.update_tabs()
 
        # Set noteboook in a sizer to create the layout
        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.EXPAND)
        
        sizer.SetSizeHints(self)
        self.SetSizerAndFit(sizer)
        

        self.Bind(EVT_IMPORT, self.OnImport)        
        
#        self.Layout()
#        p.SetSizerAndFit(sizer)
    
    def OnImport(self, event):
        self.rawdata = event.rawdata
        self.filtertab.update_rawdata(self.rawdata)        
        self.analysistab.update_rawdata(self.rawdata)
        print "IMPORT: datatypes\n",self.rawdata.dtypes
        # this should not be set based on current parsers regex pattern but based on columns with 'category' as dtype
#        self.analysistab.set_roigroupings(event.importer.get_parser().get_regexpatterns().keys())

    def OnDataUpdated(self, event):
        data,datatype = event.GetUpdatedData()
        print "appframe.OnDataUpdated - %s:" % (datatype)
#        if datatype == 'Raw':
#            self.rawdata = data
#            self.filtertab.update_rawdata(data, applyfilters=True)        
#            self.analysistab.update_rawdata(data)
#        else:
#            self.filtertab.update_data(data)        
#            self.analysistab.update_data(data)
                    

    def OnRangeFilterUpdated(self, event):
        rfilters = event.GetUpdatedItems()
        print "appframe.OnRangeFilterUpdated - %d Filters updated:" % len(rfilters)
        for key in rfilters:
            rfilter = rfilters[key]
            print "\t %s: %s" % (key, str(rfilter.get_parameters()))
        dropsbyfilter, totaldrops = self.filtertab.apply_filters(rfilters, dropsonly=True, onlyselected=False)
        self.analysistab.update_rangefilters(rfilters)
        self.data = self.rawdata.drop(totaldrops)
        self.analysistab.update_data(self.data)
        event.Skip()
        
        
    def OnAnalysisUpdated(self, event):
        updated = event.GetUpdatedItems()
        print "appframe.OnAnalysisUpdated - %d Analysis updated:" % len(updated)
        for key in updated:
            u = updated[key]
            print "\t %s: %s" % (key, str(u))

        
        
    def OnApplyFilter(self, event):
        print "AppFrame.OnApplyFilter"
        self.data = event.data
        self.analysistab.update_data(event.data)
        


    def setup_config(self):
        self.config = {
                CONFIG_EXCLUDE_FILES: [
                        ],
                CONFIG_DELIMITER:'\t',
                CONFIG_PARSERCLASS: 'core.parser.defaultparser',
                CONFIG_HEADERS: {
                    'Exc1_-Ch1-_':'trp ', 
                    'Exc1_-Ch2-_':'NAD(P)H ', 
                    'Exc2_-Ch3-_':'FAD '},
                CONFIG_DROP_COLUMNS: [
                    'Exc1_',
                    'Exc2_',
                    'Exc3_',],    
                CONFIG_CALC_COLUMNS: [
                    'NAD(P)H tm', 'NAD(P)H a2[%]/a1[%]', 
                    'NADPH %','NADPH/NADH', #'NAD(P)H %','NAD(P)H/NADH', 
                    'NADH %',  
                    'trp tm', 
                    'trp E%1', 'trp E%2', 'trp E%3', 
                    'trp r1', 'trp r2', 'trp r3', 
                    'trp a1[%]/a2[%]', 
                    'FAD tm', 'FAD a1[%]/a2[%]', 'FAD photons/NAD(P)H photons',
                    'NAD(P)H tm/FAD tm',
                    'FLIRR (NAD(P)H a2[%]/FAD a1[%])',
                    'NADPH a2/FAD a1'],
                CONFIG_ANALYSIS: {
                    'trp t1': [0,2500,81,['Treatment']],
                    'trp t2': [0,8000,81,['Treatment']],
                    'trp tm': [0,4000,81,['Treatment']],
                    'trp a1[%]': [0,100,21,['Treatment']],
                    'trp a2[%]': [0,100,21,['Treatment']],
                    'trp a1[%]/a2[%]': [0,2,81,['Treatment']],
                    'trp E%1': [0,100,21,['Treatment']],
                    'trp E%2': [0,100,21,['Treatment']],
                    'trp E%3': [0,100,21,['Treatment']],
                    'trp r1': [0,15,81,['Treatment']],
                    'trp r2': [0,3,81,['Treatment']],
                    'trp r3': [0,3,81,['Treatment']],
                    'trp chi': [0,4.7,81,['Treatment']],
                    'trp photons': [0,160,81,['Treatment']],
                    'NAD(P)H t1': [0,1000,81,['Treatment']],
                    'NAD(P)H t2': [0,8000,81,['Treatment']],
                    'NAD(P)H tm': [0,2000,81,['Treatment']],
                    'NAD(P)H photons': [0,2000,81,['Treatment']],
                    'NAD(P)H a2[%]': [0,100,51,['Treatment']],
#                    'NAD(P)H %': [0,99,34,['Treatment']],
                    'NADPH %': [0,99,34,['Treatment']],
                    'NADH %': [0,100,51,['Treatment']],
                    'NADPH/NADH': [0,3,31,['Treatment']],
                    'NAD(P)H chi': [0.7,4.7,81,['Treatment']],
                    'FAD t1': [0,1500,51,['Treatment']],
                    'FAD t2': [1000,8000,81,['Treatment']],
                    'FAD tm': [0,2500,81,['Treatment']],
                    'FAD a1[%]': [0,100,51,['Treatment']],
                    'FAD a2[%]': [0,100,21,['Treatment']],
                    'FAD a1[%]/a2[%]': [0,16,81,['Treatment']],
                    'FAD chi': [0.7,4.7,81,['Treatment']],
                    'FAD photons': [0,800,81,['Treatment']],
                    'FLIRR (NAD(P)H a2[%]/FAD a1[%])': [0,2.4,81,['Treatment']],
                    'NADPH a2/FAD a1': [0,10,101,['Treatment']],
                    'FAD photons/NAD(P)H photons': [0,2,81,['Treatment']],
                    },
                CONFIG_FILTERS: {
                    'trp t1': RangeFilter('trp t1',0,2500),
                    'trp t2': RangeFilter('trp t2',0,8000),
                    'trp tm': RangeFilter('trp tm',0,4000,selected=True),
                    'trp a1[%]': RangeFilter('trp a1[%]',0,100),
                    'trp a2[%]': RangeFilter('trp a2[%]',0,100),
                    'trp a1[%]/a2[%]': RangeFilter('trp a1[%]/a2[%]',0,2),
                    'trp E%1': RangeFilter('trp E%1',0,100),
                    'trp E%2': RangeFilter('trp E%2',0,100),
                    'trp E%3': RangeFilter('trp E%3',0,100),
                    'trp r1': RangeFilter('trp r1',0,15),
                    'trp r2': RangeFilter('trp r2',0,3),
                    'trp r3': RangeFilter('trp r3',0,3),
                    'trp chi': RangeFilter('trp chi',0,4.7),
                    'trp photons': RangeFilter('trp photons',0,160),
                    'NAD(P)H t1': RangeFilter('NAD(P)H t1',0,1000),
                    'NAD(P)H t2': RangeFilter('NAD(P)H t2',0,8000),
                    'NAD(P)H tm': RangeFilter('NAD(P)H tm',0,2000),
                    'NAD(P)H photons': RangeFilter('NAD(P)H photons',0,2000),
                    'NAD(P)H a2[%]': RangeFilter('NAD(P)H a2[%]',0,100),
#                    'NAD(P)H %': RangeFilter('NAD(P)H %',0,99),
                    'NADPH %': RangeFilter('NADPH %',0,99),
                    'NADH %': RangeFilter('NADH %',0,100),
                    'NADPH/NADH': RangeFilter('NADPH/NADH',0,3),
                    'NAD(P)H chi': RangeFilter('NAD(P)H chi',0.7,4.7),
                    'FAD t1': RangeFilter('FAD t1',0,1500),
                    'FAD t2': RangeFilter('FAD t2',1000,8000),
                    'FAD tm': RangeFilter('FAD tm',0,2500),
                    'FAD a1[%]': RangeFilter('FAD a1[%]',0,100),
                    'FAD a2[%]': RangeFilter('FAD a2[%]',0,100),
                    'FAD a1[%]/a2[%]': RangeFilter('FAD a1[%]/a2[%]',0,16),
                    'FLIRR (NAD(P)H a2[%]/FAD a1[%])': RangeFilter('FLIRR (NAD(P)H a2[%]/FAD a1[%])',0,2.4),
                    'FAD chi': RangeFilter('FAD chi',0.7,4.7),
                    'FAD photons': RangeFilter('FAD photons',0,800),
                    'FAD photons/NAD(P)H photons': RangeFilter('FAD photons/NAD(P)H photons',0,2),
                },
                CONFIG_CATEGORIES: {
                    'trp t1': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp t2': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp tm': [[0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 30], [str(i) for i in range(1,9)]],
                    'trp a1[%]': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp a2[%]': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp a1[%]/a2[%]': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp E%1': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp E%2': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp E%3': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp r1': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp r2': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp r3': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp chi': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'trp photons': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'NAD(P)H t1': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'NAD(P)H t2': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'NAD(P)H tm': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'NAD(P)H photons': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'NAD(P)H a2[%]': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
#                    'NAD(P)H %': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'NADPH %': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'NADH %': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'NADPH/NADH': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'NAD(P)H chi': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'FAD t1': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'FAD t2': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'FAD tm': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'FAD a1[%]': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'FAD a2[%]': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'FAD a1[%]/a2[%]': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'FLIRR (NAD(P)H a2[%]/FAD a1[%])': [[-300, -20, -10.0, 0, 10.0, 20, 300], [str(i) for i in range(1,7)]],
                    'FAD chi': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                    'FAD photons': [[1.0, 2.0, 3.0, 4.0], [str(i) for i in range(1,4)]],
                },}


        
            
    def rawdata_updated(self, event):
        print "rawdata_updated"
        self.rawdata = event.rawdata
        self.filtertab.update_datainfo(self.rawdata)
        self.analysistab.update(self.rawdata)
        

"""
class AppFrame(wx.Frame):
    
    def __init__(self, flimanalyzer):
        self.init_gui()
    
               
        
    def init_gui(self):
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        m_exit = menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.OnClose, m_exit)
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        
        self.statusbar = self.CreateStatusBar()
        
        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)
        box = wx.GridSizer(5, 2, 5, 5)
        
        self.m_text = wx.StaticText(panel, -1, "%d files selected" % len(self.flimanalyzer.get_importer().get_files()))
        self.m_text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.m_text.SetSize(self.m_text.GetBestSize())
        box.Add(self.m_text, 0, wx.ALL, 10)
        
        m_addfiles = wx.Button(panel, wx.ID_ANY, "Add Files")
        m_addfiles.Bind(wx.EVT_BUTTON, self.AddFiles)
        box.Add(m_addfiles, 0, wx.ALL, 10)


        import_panel = wx.Panel(self)
        import_panel.SetBackgroundColour(wx.GREEN)
        isizer = wx.BoxSizer(wx.VERTICAL)
        self.m_text = wx.StaticText(import_panel, -1, "1 Delimiter=%s" % self.flimanalyzer.get_importer().get_defaultdelimiter())
        self.m_text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.m_text.SetSize(self.m_text.GetBestSize())
        isizer.Add(self.m_text, 0, wx.EXPAND)
        self.m_text = wx.StaticText(import_panel, -1, "2 Delimiter=%s" % self.flimanalyzer.get_importer().get_defaultdelimiter())
        self.m_text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.m_text.SetSize(self.m_text.GetBestSize())
        isizer.Add(self.m_text, 0, wx.EXPAND)

        self.iedit_button = wx.Button(import_panel, wx.ID_ANY, "Edit")
        self.iedit_button.Bind(wx.EVT_BUTTON, self.EditImportCfg)
        isizer.Add(self.iedit_button, 0, wx.EXPAND)
        self.import_button = wx.Button(import_panel, wx.ID_ANY, "Import")
        self.import_button.Bind(wx.EVT_BUTTON, self.ImportFiles)
        isizer.Add(self.import_button, 0, wx.EXPAND)
        import_panel.SetSizer(isizer)
        import_panel.Layout()
        box.Add(isizer, 0, wx.EXPAND)

        
        preprocess_panel = wx.Panel(self)
        preprocess_panel.SetBackgroundColour(wx.RED)
        ppsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.m_text = wx.StaticText(preprocess_panel, -1, "1 New headers: %s" % self.flimanalyzer.get_preprocessor().get_replacementheaders)
        self.m_text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.m_text.SetSize(self.m_text.GetBestSize())
        ppsizer.Add(self.m_text, 1, wx.EXPAND)
        self.ipreprocess_button = wx.Button(preprocess_panel, wx.ID_ANY, "Edit")
        self.ipreprocess_button.Bind(wx.EVT_BUTTON, self.EditPreprocessCfg)
        ppsizer.Add(self.ipreprocess_button, 0, wx.EXPAND, 10)

        self.m_text = wx.StaticText(preprocess_panel, -1, "2 New headers: %s" % self.flimanalyzer.get_preprocessor().get_replacementheaders)
        self.m_text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.m_text.SetSize(self.m_text.GetBestSize())
        ppsizer.Add(self.m_text, 1, wx.EXPAND)
        self.preprocess_button = wx.Button(preprocess_panel, wx.ID_ANY, "Preprocess")
        self.preprocess_button.Bind(wx.EVT_BUTTON, self.PreprocessData)
        ppsizer.Add(self.preprocess_button, 0, wx.EXPAND)
        self.preprocess_button.Disable()
        preprocess_panel.SetSizer(isizer)
        preprocess_panel.Layout()
        box.Add(ppsizer, 0, wx.EXPAND)

        
        self.m_text = wx.StaticText(panel, -1, "Filter:")
        self.m_text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.m_text.SetSize(self.m_text.GetBestSize())
        box.Add(self.m_text, 0, wx.ALL, 10)

        self.filter_button = wx.Button(panel, wx.ID_ANY, "Filter")
        self.filter_button.Bind(wx.EVT_BUTTON, self.FilterData)
        box.Add(self.filter_button, 0, wx.ALL, 10)
        self.filter_button.Disable()


        self.m_text = wx.StaticText(panel, -1, "Preview")
        self.m_text.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.m_text.SetSize(self.m_text.GetBestSize())
        box.Add(self.m_text, 0, wx.ALL, 10)
        
        self.preview_button = wx.Button(panel, wx.ID_ANY, "Preview")
        self.preview_button.Bind(wx.EVT_BUTTON, self.PreviewData)
        box.Add(self.preview_button, 0, wx.ALL, 10)
        self.preview_button.Disable()
        
        self.update_buttons()
        panel.SetSizer(box)
        panel.Layout()
        
        
            
    def OnClose(self, event):
        self.Destroy()

        
    def AddFiles(self, event):
        with wx.FileDialog(self, "Add Raw Data Results", wildcard="txt files (*.txt)|*.txt",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            # Proceed loading the file chosen by the user
            paths = fileDialog.GetPaths()
            importer = self.flimanalyzer.get_importer()
            filecount = len(importer.get_files())
            for path in paths:
                if os.path.isdir(path):
                    importer.add_files([path])
                else:
                    importer.add_files([path], exclude=[])
            new_filecount = len(importer.get_files())
            self.update_buttons()
            self.m_text.SetLabel("%d file(s) selected" % new_filecount)
            self.statusbar.SetStatusText("Added %d file(s)" % (new_filecount - filecount))


    def EditImportCfg(self, event):
        print "EditImportCfg"


    def ImportFiles(self, event):
        importer = self.flimanalyzer.get_importer()
        self.statusbar.SetStatusText("Importing raw data from %d file(s)..." % len(importer.get_files()))
        self.rawdata, readfiles, headers = importer.import_data(delimiter=self.config[CONFIG_DELIMITER])
        self.data = None
        self.filtereddata = None
        self.update_buttons()
        self.statusbar.SetStatusText("Raw data contains %d rows, %d columns" % (self.rawdata.shape[0], self.rawdata.shape[1]))
        
    
    def EditPreprocessCfg(self, event):
        dframe = DictFrame(self, 'Replacement Headers', self.config[CONFIG_HEADERS], headers=['Original', 'New'])
        dframe.ShowModal()
        
        
    def PreprocessData(self, event):
        pp = self.flimanalyzer.get_preprocessor()
        pp.set_replacementheaders(self.config[CONFIG_HEADERS])
        self.data,ch = pp.rename_headers(self.rawdata)
        self.data,dc = pp.drop_columns(self.data, self.config[CONFIG_DROP_COLUMNS], func='startswith')
        self.filtereddata = None
        self.update_buttons()
        self.statusbar.SetStatusText("Renamed %d column header(s)" % len(ch))
        self.statusbar.SetStatusText("Dropped %d columns: data contains %d rows, %d columns" % (len(dc), self.data.shape[0], self.data.shape[1])) 
    

    def FilterData(self, event):
        analyzer = self.flimanalyzer.get_analyzer()
        analyzer.add_columns(self.config[CONFIG_CALC_COLUMNS])
        analyzer.set_rangefilters(self.config[CONFIG_FILTERS])

        self.statusbar.SetStatusText("Calculating values for added columns...") 
        self.data,capplied,cskipped = analyzer.calculate(self.data)
        self.statusbar.SetStatusText("Applied %d calculation functions, skipped %d: data contains %d rows, %d columns" % (len(capplied),len(cskipped), self.data.shape[0], self.data.shape[1]))
        for afunc in capplied:
            print "\tcalculated %s" % afunc 
        for sfunc in cskipped:
            print "\tskipped %s" % sfunc 
        dframe = DictFrame(self, 'Filters', analyzer.get_rangefilters(), headers=['Filter', 'Range'])
        dframe.Show()
    
        self.statusbar.SetStatusText("\nFiltering values...") 
        self.filtereddata,fapplied,fskipped, droppedrows = analyzer.apply_filter(self.data)
        self.update_buttons()
        self.statusbar.SetStatusText("Applied %d filters, skipped %d filters, dropped %d rows: data contains %d rows, %d columns" % (len(fapplied),len(fskipped), droppedrows, self.filtereddata.shape[0], self.filtereddata.shape[1]))
        
    
    def PreviewData(self, event):
        previewrows = 10
        if self.filtereddata is not None:
            data = self.filtereddata
        if self.data is not None:
            data = self.data
        elif self.rawdata is not None:
            data = self.rawdata
        else:
            return            
        frame = PandasFrame(self, "Raw data: %d of %d rows" %(previewrows,len(data)), data[:previewrows])
        frame.Show(True)
"""        