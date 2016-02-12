#!/usr/local/bin/python
#
# LSR2 quality control GUI
#
#     $Id: lsrQC.pyw,v 1.1.1.1 2008/03/10 18:48:55 kael Exp $    
#
# Kael Fischer - September, 2005
#
# Permission to use, modify and redistribute is allowed 
# only under the terms of the BSD license as specified 
# in the LICENSE file distributed with this file.
#
# Based on various protocols by John Newman
#
#
# apologies for the poor widget naming and commenting
# this is my first app with glade and WX - kf
#

import wx
import wx.grid
import FCS3
import os.path
import re
import shelve
from time import sleep

import matplotlib
matplotlib.use('WX')
from matplotlib.backends.backend_wxagg import Toolbar, FigureCanvasWxAgg,\
     FigureManager

from matplotlib.figure import Figure
from matplotlib.axes import Subplot
from matplotlib import dates
from dateutil.rrule import MO,TU,WE,TH,FR,SA,SU
from pylab import linspace, gcf, gca


#
# File names go here...
#
warningSettingsFileName = 'warning_settings'
cvHistoryFileName = 'cvhistory'
medianHistoryFileName = 'medianhistory'

# The title for a qc failure message dialog
failureTitle="QC Failed!"

cvHistories = shelve.open(cvHistoryFileName,writeback=True)
medianHistories = shelve.open(medianHistoryFileName,writeback=True)

def getHistory(param,shelveFile):

    dates = []
    cvs = []
    if param in shelveFile:
        history = shelveFile[param].items()
        history.sort()
        for date,cv in history:
            dates.append(date.toordinal())
            cvs.append(cv)

        return (dates,cvs)
    else:
        return None


class QC_Frame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.dirname = ''
        # begin wxGlade: QC_Frame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.notebook_1 = wx.Notebook(self.panel_1, -1, style=wx.NB_RIGHT)
        self.notebook_1_pane_3 = wx.Panel(self.notebook_1, -1)
        self.notebook_1_pane_2 = wx.Panel(self.notebook_1, -1)
        self.notebook_1_pane_1 = wx.Panel(self.notebook_1, -1)
        
        # Menu Bar
        self.QC_Frame_menubar = wx.MenuBar()
        self.SetMenuBar(self.QC_Frame_menubar)
        self.M_FILE = wx.Menu()
        self.M_FILE_OPEN = wx.MenuItem(self.M_FILE, wx.NewId(), "&Open", "", wx.ITEM_NORMAL)
        self.M_FILE.AppendItem(self.M_FILE_OPEN)
        self.M_FILE_EXIT = wx.MenuItem(self.M_FILE, wx.NewId(), "E&xit", "", wx.ITEM_NORMAL)
        self.M_FILE.AppendItem(self.M_FILE_EXIT)
        self.QC_Frame_menubar.Append(self.M_FILE, "&File")
        self.M_HELP = wx.Menu()
        self.M_HELP_ABOUT = wx.MenuItem(self.M_HELP, wx.NewId(), "&About", "", wx.ITEM_NORMAL)
        self.M_HELP.AppendItem(self.M_HELP_ABOUT)
        self.QC_Frame_menubar.Append(self.M_HELP, "&Help")
        # Menu Bar end
        self.QC_Frame_statusbar = self.CreateStatusBar(3, 0)
        self.grid_1 = wx.grid.Grid(self.panel_1, -1, size=(1, 1))
        self.window_1 = PlotPanel(self.notebook_1_pane_1)
        self.window_2 = PlotPanel(self.notebook_1_pane_2)
        self.window_3 = PlotPanel(self.notebook_1_pane_3)
        self.static_line_1 = wx.StaticLine(self.panel_1, -1)
        self.Page_Newman_Btn = wx.Button(self.panel_1, -1, "Page John Newman")
        self.exit_button = wx.Button(self.panel_1, -1, "Exit")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: QC_Frame.__set_properties
        self.SetTitle("LSR2 Quality Control")
        self.SetSize((865, 598))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.QC_Frame_statusbar.SetStatusWidths([-1, -1, -1])
        # statusbar fields
        QC_Frame_statusbar_fields = ["Flie", "Events", "Data Type"]
        for i in range(len(QC_Frame_statusbar_fields)):
            self.QC_Frame_statusbar.SetStatusText(QC_Frame_statusbar_fields[i], i)
        self.grid_1.CreateGrid(20, 3)
        self.grid_1.SetRowLabelSize(30)
        self.grid_1.SetColLabelSize(30)
        self.grid_1.EnableEditing(0)
        self.grid_1.SetColLabelValue(0, "Channel")
        self.grid_1.SetColSize(0, 130)
        self.grid_1.SetColLabelValue(1, "Median")
        self.grid_1.SetColSize(1, 50)
        self.grid_1.SetColLabelValue(2, "CV")
        self.grid_1.SetColSize(2, 50)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: QC_Frame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.GridSizer(3, 5, 0, 0)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(self.grid_1, 1, wx.SHAPED, 0)
        sizer_4.Add(self.window_1, 1, wx.EXPAND, 0)
        self.notebook_1_pane_1.SetAutoLayout(True)
        self.notebook_1_pane_1.SetSizer(sizer_4)
        sizer_4.Fit(self.notebook_1_pane_1)
        sizer_4.SetSizeHints(self.notebook_1_pane_1)
        sizer_5.Add(self.window_2, 1, wx.EXPAND, 0)
        self.notebook_1_pane_2.SetAutoLayout(True)
        self.notebook_1_pane_2.SetSizer(sizer_5)
        sizer_5.Fit(self.notebook_1_pane_2)
        sizer_5.SetSizeHints(self.notebook_1_pane_2)
        sizer_6.Add(self.window_3, 1, wx.EXPAND, 0)
        self.notebook_1_pane_3.SetAutoLayout(True)
        self.notebook_1_pane_3.SetSizer(sizer_6)
        sizer_6.Fit(self.notebook_1_pane_3)
        sizer_6.SetSizeHints(self.notebook_1_pane_3)
        self.notebook_1.AddPage(self.notebook_1_pane_1, "FSC / SSC")
        self.notebook_1.AddPage(self.notebook_1_pane_2, "CV History")
        self.notebook_1.AddPage(self.notebook_1_pane_3, "Median History")
        sizer_3.Add(self.notebook_1, 2, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 5, wx.EXPAND, 0)
        sizer_2.Add(self.static_line_1, 0, wx.EXPAND, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add(self.Page_Newman_Btn, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add(self.exit_button, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        grid_sizer_1.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        sizer_2.Add(grid_sizer_1, 1, wx.ADJUST_MINSIZE, 0)
        self.panel_1.SetAutoLayout(True)
        self.panel_1.SetSizer(sizer_2)
        sizer_2.Fit(self.panel_1)
        sizer_2.SetSizeHints(self.panel_1)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

        wx.EVT_MENU(self,self.M_FILE_OPEN.GetId(),self.onOpen)
        wx.EVT_MENU(self,self.M_FILE_EXIT.GetId(),self.onExit)
        wx.EVT_BUTTON(self,self.Page_Newman_Btn.GetId(),self.alertNewman)
        wx.EVT_BUTTON(self,self.exit_button.GetId(),self.onExit)

    def onOpen(self,event):
        """ Open a file"""

        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "",
                            "FCS Files (*.fcs;*.FCS)|*.fcs;*.FCS| All Files (*.*)|*.*", 
                            wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename=dlg.GetFilename()
            self.dirname=dlg.GetDirectory()
            filePath=os.path.join(self.dirname,self.filename)
            self.loadFile(filePath)
        dlg.Destroy()
        

    def loadFile(self,filePath):
        """parse FCS file and update data."""

        self.loadWarnings()

        self.areaCVs = {}
        self.areaMedians = {}
        
        self.fcs=FCS3.FCS()
        try:
            self.fcs.parseFCSfile(filePath)
        except:
            errDlg=wx.MessageDialog(self,"Unable to parse: %s"%filePath,
                                    "File Load Error",wx.ICON_ERROR)
            errDlg.ShowModal()
            errDlg.Destroy()
            raise 
            return False

        if '$DATE' not in self.fcs.text:
            errDlg=wx.MessageDialog(self,"FCS file (%s) has no $DATE data.  History plots won't work."%filePath,
                                    "File Load Error",wx.ICON_ERROR)
            errDlg.ShowModal()
            errDlg.Destroy()
            #raise FCS3.FCSParserError, "No $DATE in FCS file."
            #return False


        
        #
        # filtering Steps go here
        #

        # all events with min or max values
        self.fcs.filterZeros()
        self.fcs.filterPeggedValues()
        # a radial filter centered on mean
        (eventCount,center,radius2) = self.fcs.radialFilter('FSC-A', 'SSC-A',sigma=2)
        #self.fcs.filterOutliers(['FSC-A', 'SSC-A'],fraction=0.05)
        
        # Display summary on status bar
        QC_Frame_statusbar_fields = [os.path.split(filePath)[1],
                                     "%s/%s events" % (self.fcs.filteredEventCount,self.fcs.eventCount),
                                     self.fcs.dataTypeDescription()]

        for i in range(len(QC_Frame_statusbar_fields)):
            self.QC_Frame_statusbar.SetStatusText(QC_Frame_statusbar_fields[i], i)

        dlg = wx.MessageDialog(None, "File contains %s events.  The number of\nfiltered spots is shown in the status bar."  %self.fcs.eventCount ,
                               "FCS File Loaded",
                               wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()

        
        # Write stats to the grid
        gridRow = 0
        for param in self.fcs.parameters:
            # Show Area Parameters only
            if param[-2:] == '-A':
                # store cv's for later
                self.areaCVs[param] = self.fcs.cv(param)
                self.areaMedians[param] = self.fcs.median(param)
                
                self.grid_1.SetCellValue(gridRow,0,param)
                self.grid_1.SetCellValue(gridRow,1,
                                         "%7d"%(self.areaMedians[param],))
                self.grid_1.SetCellValue(gridRow,2,
                                         "%.2f"%(self.areaCVs[param],))
                
            
                gridRow += 1

        self.window_1.init_plot_data(self.fcs)
        self.window_2.init_subplots(self.fcs,self.fcs.cv,cvHistories)
        self.window_3.init_subplots(self.fcs,self.fcs.median,medianHistories,
                                    autoscale=True)

        # the data are ok unless any of the following tests fail
        self.dataOK = True
        
        if self.warnings['minTotalEvents'] is not None:
            if self.fcs.eventCount < self.warnings['minTotalEvents'][0]:
                self.dataOK=False
                warnDlg = wx.MessageDialog(None,self.warnings['minTotalEvents'][1],
                                           failureTitle,wx.OK|wx.ICON_ERROR)
                warnDlg.ShowModal()

        if self.warnings['minNetEvents'] is not None:
            if self.fcs.filteredEventCount < self.warnings['minNetEvents'][0]:
                self.dataOK=False
                warnDlg = wx.MessageDialog(None,self.warnings['minNetEvents'][1],
                                           failureTitle,wx.OK|wx.ICON_ERROR)
                warnDlg.ShowModal()

        if self.warnings['maxExcludedEvents'] is not None:
            if self.fcs.eventCount-self.fcs.filteredEventCount > self.warnings['maxExcludedEvents'][0]:
                self.dataOK=False
                warnDlg = wx.MessageDialog(None,self.warnings['maxExcludedEvents'][1],
                                           failureTitle,wx.OK|wx.ICON_ERROR)
                warnDlg.ShowModal()
                
        #check the CVs
        for param in self.fcs.parameters:
            if param[-2:] == '-A':
                key = 'maxCV.' + param
                if key in self.warnings and self.warnings[key] is not None:
                    if self.areaCVs[param] > self.warnings[key][0]:
                        self.dataOK = False
                        warnDlg = wx.MessageDialog(None,self.warnings[key][1],
                                                   failureTitle,wx.OK|wx.ICON_ERROR)
                        warnDlg.ShowModal()

        #check medians
        for param in self.fcs.parameters:
            if param[-2:] == '-A':
                maxKey = 'maxMedian.' + param
                minKey = 'minMedian.' + param
                if maxKey in self.warnings and self.warnings[maxKey] is not None:
                    if self.areaMedians[param] > self.warnings[maxKey][0]:
                        self.dataOK = False
                        warnDlg = wx.MessageDialog(None,self.warnings[maxKey][1],
                                                   failureTitle,wx.OK|wx.ICON_ERROR)
                        warnDlg.ShowModal()
                if minKey in self.warnings and self.warnings[minKey] is not None:
                    if self.areaMedians[param] < self.warnings[minKey][0]:
                        self.dataOK = False
                        warnDlg = wx.MessageDialog(None,self.warnings[minKey][1],
                                                   failureTitle,wx.OK|wx.ICON_ERROR)
                        warnDlg.ShowModal()
                

       
        

        # write the data to the history file
        try:
            dataDate = self.fcs.startTime()
        except:
            return
        
        if self.dataOK or True:

            for key,cv in self.areaCVs.items():
                if key not in cvHistories:
                    cvHistories[key] = { dataDate: cv }
                else:
                    if dataDate  not in cvHistories[key]:
                        newHistory =  cvHistories[key]
                        newHistory[dataDate] = cv
                        cvHistories[key] = newHistory
            
            for key,cv in self.areaMedians.items():
                if key not in medianHistories:
                    medianHistories[key] = { dataDate: cv }
                else:
                    if dataDate  not in medianHistories[key]:
                        newHistory =  medianHistories[key]
                        newHistory[dataDate] = cv
                        medianHistories[key] = newHistory

            self.Layout()

                    

    def onExit(self,event):
        """Exit the application"""
        cvHistories.close()
        medianHistories.close()
        self.Close(True)


    def alertNewman(self,event):
        dlg = wx.MessageDialog(None,"What do I look like?\nA cellphone?","Question",
                               wx.OK|wx.ICON_QUESTION)
        dlg.ShowModal()
        sleep(1)
        dlg = wx.MessageDialog(None,"John is very angry!","Start Running...",
                               wx.OK|wx.ICON_EXCLAMATION)
        dlg.ShowModal()


    def loadWarnings(self):

        self.warnings = { 'minTotalEvents':       None,
                          'minNetEvents':         None,
                          'maxExcludedEvents':    None,
                          'maxCV.FITC-A':         None,
                          'maxCV.PE-A':           None,
                          'maxCV.PerCP-Cy5-5-A':  None,
                          'maxCV.PE-Cy7-A':       None,
                          'maxCV.APC-A':          None,
                          'maxCV.APC-Cy7-A':      None,
                          'maxCV.Cascade Blue-A': None,
                          'maxCV.Alexa 430-A':    None,
                          'maxMedian.FITC-A':         None,
                          'maxMedian.PE-A':           None,
                          'maxMedian.PerCP-Cy5-5-A':  None,
                          'maxMedian.PE-Cy7-A':       None,
                          'maxMedian.APC-A':          None,
                          'maxMedian.APC-Cy7-A':      None,
                          'maxMedian.Cascade Blue-A': None,
                          'maxMedian.Alexa 430-A':    None,
                          'minMedian.FITC-A':         None,
                          'minMedian.PE-A':           None,
                          'minMedian.PerCP-Cy5-5-A':  None,
                          'minMedian.PE-Cy7-A':       None,
                          'minMedian.APC-A':          None,
                          'minMedian.APC-Cy7-A':      None,
                          'minMedian.Cascade Blue-A': None,
                          'minMedian.Alexa 430-A':    None }

        warnFile = file(warningSettingsFileName)
        for line in warnFile:
            if len(line) == 0 or line[0]=='#':
                continue
            (thing,limit,msg) = re.split('\t+',line)
            limit = float(limit)

            if thing in self.warnings:
                self.warnings[thing]= (limit,msg)
            else:
                # ignore if not in the dictionary
                pass
        warnFile.close()

# end of class QC_Frame

# Define File Drop Target class
class FileDropTarget(wx.FileDropTarget):
   """ This object implements Drop Target functionality for Files """
   def __init__(self, obj):
      """ Initialize the Drop Target, passing in the Object Reference to
          indicate what should receive the dropped files """
      # Initialize the wsFileDropTarget Object
      wx.FileDropTarget.__init__(self)
      # Store the Object Reference for dropped files
      self.obj = obj

   def OnDropFiles(self, x, y, filenames):
        """ Implement File Drop """
      
        self.obj.loadFile(filenames[0])
        self.dirname = os.path.split(filenames[0])[0]

class PlotPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        self.fig = Figure((5,5), 75)
        self.canvas = FigureCanvasWxAgg(self, -1, self.fig)
        #self.toolbar = Toolbar(self.canvas) #matplotlib toolbar
        #self.toolbar.Realize()
        #self.toolbar.set_active([0,1])

        # Now put all into a sizer
        sizer = wx.BoxSizer(wx.VERTICAL|wx.EXPAND)
        # This way of adding to sizer allows resizing
        sizer.Add(self.canvas, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        # Best to allow the toolbar to resize!
        #sizer.Add(self.toolbar, 0, wx.GROW)
        self.SetSizer(sizer)
        self.Fit()

    def init_plot_data(self,fcs):
        a = self.fig.add_subplot(111)

        
        a.set_xlabel('FSC-A')
        a.set_ylabel('SSC-A')
        a.plot(fcs.values('FSC-A'),fcs.values('SSC-A'),'.r',
               markersize=3, label='accepted')
        a.plot(fcs.excludedValues('FSC-A'),fcs.excludedValues('SSC-A'),'.b',
               markersize=3,label='excluded')
        
        a.legend(loc=4)
        self.Layout()

        #self.toolbar.update() # Not sure why this is needed - ADS


    def init_subplots(self,fcs,callback,historyShelve,autoscale=False):


        plotColumns = 2
        
        areas = []
        
        for param in fcs.parameters:
            # Show Area Parameters only
            if param[-2:] == '-A':
                areas.append(param)

        areas.remove('FSC-A')
        areas.remove('SSC-A')

        plotRows = len(areas)/plotColumns
        plotRows = plotRows + len(areas)%plotColumns


        for i in range(len(areas)):
            a = self.fig.add_subplot(plotRows,plotColumns,i+1)
            a.clear()
            a.set_title(areas[i])
            history = getHistory(areas[i],historyShelve)
            if history is not None:
                historyDates,historyCVs = history
                a.plot_date(historyDates,historyCVs,'-k')
                
            a.plot_date(([fcs.startTime().toordinal()]),[callback(areas[i])])
            a.xaxis.set_major_locator(dates.WeekdayLocator(byweekday=MO, interval=2))
            if not autoscale:
                a.set_yticks(linspace(0,a.get_ylim()[-1],4))
            
            
            #loc = WeekdayLocator(byweekday=MO, interval=2)
            
        self.fig.subplots_adjust(hspace=0.5,wspace=0.7)
        self.Layout()
            


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    QC_Frame = QC_Frame(None, -1, "")
    fDropTarget=FileDropTarget(QC_Frame)
    QC_Frame.SetDropTarget(fDropTarget)
    app.SetTopWindow(QC_Frame)
    QC_Frame.Show()
    app.MainLoop()
