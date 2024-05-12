'''
    12/20/2023  Initial version
    05/11/2024  Auto capture added
    
    Uisang Hwang
    
    Ref: https://stackoverflow.com/questions/63193311/
         detect-external-keyboard-events-in-pyqt5
'''
import sys
import os
import time
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QSize, QTimer              
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import ( 
        QApplication, QWidget    , QStyleFactory , 
        QPushButton , QLineEdit  , QPlainTextEdit, 
        QComboBox   , QGridLayout, QVBoxLayout   , 
        QHBoxLayout , QFormLayout, QFileDialog   , 
        QMessageBox , QLabel     , QCheckBox 
        )
import keyboard
import pygetwindow
import pyautogui
import PIL
from pathlib import Path
import msg

from icons import icon_folder_open, icon_refresh, icon_capture

hot_key_list = ['f2' , 'f3' , 'f3', 'f4', 
                'left', 'up', 'right', 'down']
file_template = "%s-%03d.png"              

class CaptureCallback(QObject):
    print_message  = pyqtSignal(str)
    number_changed = pyqtSignal(int)
    
    def __init__(self, title, hot_key, img_num, prefix, interval=0):
        super(CaptureCallback, self).__init__()
        self.title = title
        self.hot_key = hot_key
        self.image_number = img_num
        self.prefix  = prefix
        self.interval = interval
        self.timer = None
        
        if self.interval > 0:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.save)
           
    def save(self):
        try:
            win = pygetwindow.getWindowsWithTitle(self.title)[0]
            win.activate()
        
            left, top = win.topleft
            right, bottom = win.bottomright
        
            cwd = Path.cwd()
            pre = self.prefix
            
            temp_path = Path.joinpath(cwd, "%d-tmp.png"%self.image_number)
            pyautogui.screenshot(str(temp_path))
            
            im = PIL.Image.open(str(temp_path))
            file = file_template%(pre,self.image_number)
            path = Path.joinpath(cwd, file)
            
            im = im.crop((left, top, right, bottom))
            im.save(str(path))

            if isinstance(self.timer, QTimer):
                keyboard.send(self.hot_key)
            
        except Exception as e:
            self.print_message.emit(str(e))
            return
            
        self.print_message.emit("Save ... %s"%file)
        self.image_number += 1
        Path.unlink(temp_path)
        self.number_changed.emit(self.image_number)
        
    def keyboardEventReceived(self, event):
        if event.event_type == 'down':
            if event.name == self.hot_key:
                self.save()
                
    def start(self):
        # on_press returns a hook that can be used to "disconnect" the callback
        # function later, if required
        if isinstance(self.timer, QTimer):
            self.timer.start(self.interval)
        else:
            self.hook = keyboard.on_press(self.keyboardEventReceived)
        
    def stop(self):
        if isinstance(self.timer, QTimer):
            self.timer.stop()
            self.timer = None
        else:
            keyboard.unhook(self.hook)
        
class ScreenCapture(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.image_number = 0
        self.npage_auto_saved = 0
        
    def initUI(self):
        self.form_layout = QFormLayout()
        paper = QGridLayout()
        
        paper.addWidget(QLabel("Save"), 0,0)
        self.save_folder = QLineEdit(os.getcwd())
        paper.addWidget(self.save_folder, 0,1)
        
        self.save_folder_btn = QPushButton()
        self.save_folder_btn.setIcon(QIcon(QPixmap(icon_folder_open.table)))
        self.save_folder_btn.setIconSize(QSize(16,16))
        self.save_folder_btn.setToolTip("Change download folder")
        self.save_folder_btn.clicked.connect(self.get_new_save_folder)
        paper.addWidget(self.save_folder_btn, 0,2)
        
        paper.addWidget(QLabel("Prefix"), 1,0)
        self.prefix = QLineEdit("cap")
        paper.addWidget(self.prefix, 1, 1)
        
        paper.addWidget(QLabel("Start#"), 2,0)
        self.start_number = QLineEdit("0")
        paper.addWidget(self.start_number, 2,1)
        
        paper.addWidget(QLabel("Application"), 3, 0)
        self.application = QComboBox()
        self.application.setFixedWidth(150)
        self.refresh_applications()
        paper.addWidget(self.application, 3,1)
        
        self.refresh_app_list_btn = QPushButton()
        self.refresh_app_list_btn.setIcon(QIcon(QPixmap(icon_refresh.table)))
        self.refresh_app_list_btn.setIconSize(QSize(16,16))
        self.refresh_app_list_btn.setToolTip("Reread Appplications")
        self.refresh_app_list_btn.clicked.connect(self.refresh_applications)
        paper.addWidget(self.refresh_app_list_btn, 3,2)
        
        paper.addWidget(QLabel("Hot Key"), 4, 0)
        self.hot_key = QComboBox()
        self.hot_key.addItems(hot_key_list)
        paper.addWidget(self.hot_key, 4,1)
        
        paper.addWidget(QLabel("Auto Save"), 5, 0)
        self.auto_save = QCheckBox()
        paper.addWidget(self.auto_save, 5,1)
        self.auto_save.stateChanged.connect(self.autosave_state_changed)        
        paper.addWidget(QLabel("Interval(ms)"), 6, 0)
        self.interval = QLineEdit("0.0")
        self.interval.setEnabled(False)
        paper.addWidget(self.interval, 6, 1)
        
        paper.addWidget(QLabel("Num Pages"), 7, 0)
        self.npage_to_save = QLineEdit('0')
        self.npage_to_save.setEnabled(False)
        paper.addWidget(self.npage_to_save, 7, 1)
        
        bv = QHBoxLayout()
        
        self.start_capture_btn = QPushButton('Start')
        self.start_capture_btn.clicked.connect(self.start_capture)
        
        self.stop_capture_btn = QPushButton('Stop')
        self.stop_capture_btn.clicked.connect(self.stop_capture)

        bv.addWidget(self.start_capture_btn)
        bv.addWidget(self.stop_capture_btn)

        self.message = QPlainTextEdit()
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_message)
        
        self.form_layout.addRow(paper)
        self.form_layout.addRow(bv)
        self.form_layout.addWidget(self.message)
        self.form_layout.addWidget(self.clear_btn)
        
        self.setLayout(self.form_layout)
        self.setWindowTitle("Capture")
        self.setWindowIcon(QIcon(QPixmap(icon_capture.table)))
        self.show()

    def autosave_state_changed(self):
        if self.auto_save.isChecked():
            self.interval.setEnabled(True)
            self.npage_to_save.setEnabled(True)
        else:
            self.interval.setEnabled(False)
            self.npage_to_save.setEnabled(False)
        
    def refresh_applications(self):
        self.application.clear()
        app_list = pygetwindow.getAllTitles()
        app_list = [a for a in app_list if a != '']
        self.application.addItems(app_list)
        
    def clear_message(self):
        self.message.clear()
        
    def get_new_save_folder(self):
        startingDir = os.getcwd() 
        path = QFileDialog.getExistingDirectory(None, 'Save folder', startingDir, 
        QFileDialog.ShowDirsOnly)
        if not path: return
        self.save_folder.setText(path)
        os.chdir(path)

    def start_capture(self):
        self.npage_auto_saved = 0
        self.image_number = int(self.start_number.text())
        _interval = int(self.interval.text()) if self.auto_save.isChecked() else 0
        self.callback = CaptureCallback(
                            self.application.currentText(),
                            self.hot_key.currentText(),
                            self.image_number,
                            self.prefix.text(),
                            _interval
                        )

        self.callback.print_message.connect(self.print_concurrent_message)
        self.callback.number_changed.connect(self.set_image_number)
        self.start_capture_btn.setEnabled(False)
        self.callback.start()
        
    def stop_capture(self):
        if self.callback:
            self.callback.stop()
            self.callback = None
            self.start_capture_btn.setEnabled(True)
            self.message.appendPlainText("Done ...")
    
    def set_image_number(self, img_num):
        self.start_number.setText("%d"%img_num)
        self.npage_auto_saved += 1
        
        npage = int(self.npage_to_save.text())
        if npage > 0 and self.npage_auto_saved == npage:
            self.stop_capture()
        
    def print_concurrent_message(self, con_msg):
        self.message.appendPlainText(con_msg)
        
def run_screencapture():
    
    app = QApplication(sys.argv)

    # --- PyQt4 Only
    #app.setStyle(QStyleFactory.create(u'Motif'))
    #app.setStyle(QStyleFactory.create(u'CDE'))
    #app.setStyle(QStyleFactory.create(u'Plastique'))
    #app.setStyle(QStyleFactory.create(u'Cleanlooks'))
    # --- PyQt4 Only
    
    app.setStyle(QStyleFactory.create("Fusion"))
    ydl= ScreenCapture()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    run_screencapture()    
