import pandas as pd
import numpy as np

import wx
import wx.grid

EVEN_ROW_COLOUR = '#CCE6FF'
GRID_LINE_COLOUR = '#ccc'

class PandasTable(wx.grid.GridTableBase):
    def __init__(self, data=None, showindex=False):
        wx.grid.GridTableBase.__init__(self)
        self.headerRows = 1
        if data is None:
            data = pd.DataFrame()
        self.data = data
        self.showindex = showindex


    def GetNumberRows(self):
        return len(self.data)


    def GetNumberCols(self):
        if self.showindex:
            return len(self.data.columns) + 1
        else:
            return len(self.data.columns)


    def GetValue(self, row, col):
        if self.showindex:
            if col == 0:
                return self.data.index[row]
            return self.data.iloc[row, col - 1]
        else:
            return self.data.iloc[row, col]            


    def SetValue(self, row, col, value):
        if self.showindex:
            self.data.iloc[row, col - 1] = value
        else:
            self.data.iloc[row, col] = value
            

    def GetColLabelValue(self, col):
        if self.showindex:
            if col == 0:
                if self.data.index.name is None:
                    return 'Index'
                else:
                    return self.data.index.name
            return str(self.data.columns[col - 1])
        else:
            return str(self.data.columns[col])          


    def GetTypeName(self, row, col):
        return wx.grid.GRID_VALUE_STRING
    

#    def GetAttr(self, row, col, prop):
#        attr = wx.grid.GridCellAttr()
#        if row % 2 == 1:
#            attr.SetBackgroundColour(EVEN_ROW_COLOUR)
#        return attr


class PandasFrame(wx.Frame):
    """
    Frame that holds all other widgets
    """

    def __init__(self, parent, title, data=None, showindex=False):
        """Constructor"""
        super(PandasFrame, self).__init__(parent, wx.ID_ANY, title)
        self._init_gui(data, showindex)
        self.Layout()
        #self.Show()

    def _init_gui(self, data=None, showindex=False):
        if data is None:
            data = pd.DataFrame()
        table = PandasTable(data, showindex)

        grid = wx.grid.Grid(self, -1)
        grid.SetTable(table, takeOwnership=True)
        grid.EnableEditing(False)
        grid.AutoSizeColumns()
        grid.EnableDragColSize(True)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_CLOSE, self.exit)
        
#        sizer.SetSizeHints(self)
#        self.SetSizerAndFit(sizer)
        

    def exit(self, event):
        self.Destroy()



class TestApp(wx.App):
    
    def __init__(self, data):
        self.data = data
        super(TestApp,self).__init__()
        
    def OnInit(self):
        self.frame = PandasFrame(None, "Test", self.data)    ## add two lines here
        self.frame.Show(True)
        return True
    
if __name__ == "__main__":
    np.random.seed(0)
    df = pd.DataFrame(np.random.randn(8, 4),columns=['A', 'B', 'C', 'D'])
    app = TestApp(df)
    app.MainLoop()