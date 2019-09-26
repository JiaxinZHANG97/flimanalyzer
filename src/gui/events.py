#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 18 13:39:22 2018

@author: khs3z
"""

import wx

EVT_DU_TYPE = wx.NewEventType()
EVT_DATAUPDATED = wx.PyEventBinder(EVT_DU_TYPE, 1)

class DataUpdatedEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.data = None
        self.datatype = None

    def SetUpdatedData(self, data, dtype):
        self.data = data
        self.datatype = dtype
        
    def GetUpdatedData(self):
        return self.data, self.datatype
    
