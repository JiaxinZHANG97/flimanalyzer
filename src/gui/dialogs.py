#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 12 13:35:51 2018

@author: khs3z
"""

import wx

def check_data_msg(data):
    ok = data is not None and len(data) > 0
    if not ok:    
        wx.MessageBox('No data loaded. Import data first.', 'Warning', wx.OK)
    return ok


def fix_filename(fname):
    if fname is None:
        return None
    else:
        fname = fname.replace(' ','')
        fname = fname.replace(',','_')
        fname = fname.replace(':','-')
        fname = fname.replace('\\','_')
        fname = fname.replace('/','_')
        fname = fname.replace('[','')
        fname = fname.replace(']','')
        fname = fname.replace('(','')
        fname = fname.replace(')','')
        fname = fname.replace('%','perc')
        fname = fname.replace('--','-')
        return fname
    
        
def save_dataframe(parent, title, data, filename, wildcard="txt files (*.txt)|*.txt", saveindex=True):
    with wx.FileDialog(parent, title, wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as fileDialog:    
        fileDialog.SetFilename(fix_filename(filename))
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return False
        fname = fileDialog.GetPath()                
        try:
            data.reset_index()
            data.to_csv(fname, index=saveindex, sep='\t')
        except IOError:
            wx.MessageBox('Error saving data in file %s' % fname, 'Error', wx.OK)
            return False
        return True    
            
        

def save_figure(parent, title, fig, filename, wildcard="all files (*.*)|*.*", dpi=300, legend=None):
    with wx.FileDialog(parent, title, wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as fileDialog:    
        fileDialog.SetFilename(fix_filename(filename))
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return False
        fname = fileDialog.GetPath()                
        try:
            if legend is not None:
                fig.savefig(fname, dpi=dpi, bbox_extra_artists=(legend,), bbox_inches='tight')            
            else:                
                fig.savefig(fname, dpi=dpi, bbox_inches='tight')            
        except IOError:
            wx.MessageBox('Error saving figure in file %s' % fname, 'Error', wx.OK)
            return False
        return True    
            
        
class ConfigureCategoriesDlg(wx.Dialog):
    def __init__(self, parent, title='', bins=[], labels=[]):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Category configuration: %s" % title, size= (650,220))
#        self.bins = None
#        self.labels = None
        self.panel = wx.Panel(self,wx.ID_ANY)

        self.bin = wx.StaticText(self.panel, label="Category bins", pos=(20,20))
        self.bin_field = wx.TextCtrl(self.panel, value=','.join([str(b) for b in bins]), pos=(110,20), size=(500,-1))
        self.label = wx.StaticText(self.panel, label="Category labels", pos=(20,60))
        self.label_field = wx.TextCtrl(self.panel, value=','.join(labels), pos=(110,60), size=(500,-1))
        self.okButton = wx.Button(self.panel, label="OK", pos=(110,160))
        self.okButton.Bind(wx.EVT_BUTTON, self.OnSave)
        self.cancelButton = wx.Button(self.panel, label="Cancel", pos=(210,160))
        self.cancelButton.Bind(wx.EVT_BUTTON, self.OnQuit)
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.Show()

    def OnQuit(self, event):
        self.bins = None
        self.labels = None
        self.EndModal(wx.ID_CANCEL)

    def get_config(self):
        if  self.bins:
            return self.bins,self.labels
        else:  
            return None
    
    def OnSave(self, event):
        self.bins = [float(f) for f in self.bin_field.GetValue().split(',')]
        self.labels = self.label_field.GetValue().encode('ascii','ignore').split(',')
        self.EndModal(wx.ID_OK)
