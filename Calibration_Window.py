#import calibration files
from Calibration import Detector_Calibration as cali
#prefined imports
import sys
from PyQt5.QtWidgets import (QApplication, QPushButton,QWidget,QGridLayout,
                             QSizePolicy,QLineEdit,
                             QMainWindow,QAction,QVBoxLayout
                             ,QDockWidget,QListView,QInputDialog,
                             QAbstractItemView,QLabel,QFileDialog)
from PyQt5.QtGui import (QFont,QStandardItemModel,QStandardItem)
from PyQt5.QtCore import Qt,QModelIndex

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import matplotlib.pyplot as plt

class Calibration_Window(QMainWindow):
    '''Open a calibration window that allows the user to select the calibration
    style. Allows the user to click on location in graph to select the 
    channels to calibrate and gets the required energy at that point
    '''
    counts=[]
    channels=[]
    calibration_lines=[]
    energies={}
    def __init__(self):
        super().__init__()
        self.font=QFont()
        self.font.setPointSize(12)
        self.size_policy=QSizePolicy.Expanding
        self.setWindowTitle('Energy Calibration')
        self.menu()
        self.geometry()
        self.mouse_tracking()
        self.showMaximized()
        self.show()
        
    def menu(self):
        self.menuFile=self.menuBar().addMenu('&File')
        self.load_new=QAction('&Load New Spectrum')
        self.load_new.triggered.connect(self.new_spectrum)
        self.load_new.setShortcut('Ctrl+O')
        self.load_new.setToolTip('Load a raw spectrum')
        
        self.calibrateAction=QAction('&Calibrate')
        self.calibrateAction.triggered.connect(self.calibration)
        self.calibrateAction.setShortcut('Ctrl+C')
        self.calibrateAction.setDisabled(True)
        
        self.save=QAction('&Save Calibration')
        self.save.triggered.connect(self.save_)
        self.save.setShortcut('Ctrl+S')
        self.save.setDisabled(True)
        self.menuFile.addActions([self.load_new,self.calibrateAction,
                                  self.save])
    
    def geometry(self):
        '''Setup the geometry
        '''
        self.added_values=QListView(self)
        self.added_values.setFont(self.font)
        self.added_values.setSizePolicy(self.size_policy,self.size_policy)
        self.added_values.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.added_=QDockWidget('Calibration Values')
        self.added_.setWidget(self.added_values)
        self.addDockWidget(Qt.LeftDockWidgetArea,self.added_)
        
        self.loaded=QStandardItemModel()
        self.added_values.setModel(self.loaded)
        self.added_values.doubleClicked[QModelIndex].connect(self.update)
        
        self.calibrate=QPushButton('Calibrate')
        self.calibrate.setFont(self.font)
        self.calibrate.setSizePolicy(self.size_policy,self.size_policy)
        self.calibrate.clicked.connect(self.calibration)
        
        self.plot=QWidget()
        layout=QVBoxLayout()
        self.figure=Figure()
        self.canvas=FigureCanvas(self.figure)
        self.toolbar=NavigationToolbar(self.canvas,self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.plot.setLayout(layout)
        self.setCentralWidget(self.plot)
        
        self.ax=self.canvas.figure.subplots()
        self.ax.set_yscale('log')
        self.ax.set_xlabel('Channel')
        self.ax.set_ylabel('Counts')
    
    def mouse_tracking(self):
        self.lx=self.ax.axvline(color='k',linestyle='--')
        self.txt=self.ax.text(0.8,0.9,"",transform=self.ax.transAxes)
        self.figure.canvas.mpl_connect('motion_notify_event',self.mouse_move)
        
    def mouse_move(self,event):
        if not event.inaxes:
            return
        x=event.xdata
        self.lx.set_xdata(x)
        self.txt.set_text('Channel: {:.2f}'.format(x))
        self.canvas.draw()        
        
    def mouse_click(self,event):
        if not event.inaxes:
            return
        if event.dblclick:
            if event.button==3:
                e,ok=QInputDialog.getDouble(self, 'Energy','Energy:(MeV)',
                                            10,0,15,10)
                if ok:
                    self.calibration_lines.append(round(event.xdata,2))
                    self.energies['{:.2f}'.format(event.xdata)]='{:.4f}'.format(e)
                    self.loaded.appendRow(QStandardItem(
                            'Ch: {:.2f}->Energy: {:.4f} MeV'.format(
                                    event.xdata,e)))
                    if len(self.calibration_lines)>=2:
                        self.calibrateAction.setEnabled(True)
                self.replot()
        
    def new_spectrum(self):
        #load the file from a text or csv file
        fileName=QFileDialog.getOpenFileName(self,'Raw Spectrum','',
                             'Text File (*.txt);;Comma Seperate File (*.csv)')
        if fileName:
            #clear the list view to start calibrating again
            self.loaded.removeRows(0,self.loaded.rowCount())
            
            self.energies={}
            self.calibration_lines=[]
            self.counts=[]
            self.channels=[]
            f=open(fileName[0],'r')
            f_data=f.readlines()
            f.close()
            
            for i in range(len(f_data)):
                try:                    
                    self.counts.append(float(f_data[i].split(sep=',')[0]))
                    self.channels.append(i)
                except:
                    a=True
            self.replot(left_lim=0,right_lim=len(self.channels))
            
    def replot(self,left_lim=None,right_lim=None):
        l,r=self.ax.get_xlim()
        self.ax.clear()
        self.mouse_tracking()
        self.figure.canvas.mpl_connect('button_press_event',
                                       self.mouse_click)
        self.ax.set_yscale('log')
        self.ax.set_xlabel('Channel')
        self.ax.set_ylabel('Counts')
        
        self.ax.plot(self.channels,self.counts)
        if left_lim!=None and right_lim!=None:    
            self.ax.set_xlim(left_lim,right_lim)
        else:
            self.ax.set_xlim(l,r)
        for i in self.calibration_lines:
            self.ax.axvline(x=i,color='k',linestyle='--')
        self.canvas.draw()
        
    def calibration(self):
        channels=list(self.energies.keys())
        energies=list(self.energies.values())
        channels=[float(i) for i in channels]
        energies=[float(j) for j in energies]
        
        #can be changed at a later point to direct linear or deviation 
        #pairs dependent on the best method determined
        self.cal_values=cali(self.channels).segmented_linear_least_squares(
                channels,energies)
        
        plt.figure(1,figsize=(5,5))
        plt.plot(self.channels,self.cal_values)
        plt.figure(2,figsize=(5,5))
        plt.plot(self.cal_values,self.counts)
        plt.xlabel('Energy [MeV]')
        plt.ylabel('Counts')
        plt.title('Energy Calibrated Spectrum')
        plt.yscale('log')
        plt.xlim(0,14)
        plt.show()
        self.save.setEnabled(True)
        
    def save_(self):
        name=QFileDialog.getSaveFileName(self,'Calibration Data','',
                         'Text File (*.txt);; Comma Seperated File (*.csv)')
        if name:
            f=open(name[0],'w')
            for i in self.cal_values:
                f.write('{:.8f}\n'.format(i))
    
    def update(self,index):
        item=self.loaded.itemFromIndex(index)
        val=item.text()
        ch=val.split(sep='->')[0].split(sep=': ')[1]
        self.energies.pop(ch)
        self.calibration_lines.remove(float(ch))
        self.loaded.removeRows(0,self.loaded.rowCount())
        for i in self.calibration_lines:
            self.loaded.appendRow(
                    QStandardItem(
                            'Ch: {:.2f}->Energy: {} MeV'.format(
                                    i,self.energies[str(i)])))
        self.replot()
        
if __name__=="__main__":
    app=QApplication(sys.argv)
    ex=Calibration_Window()
    sys.exit(app.exec_())
        