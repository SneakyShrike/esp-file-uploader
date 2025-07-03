import sys
import random
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QComboBox, QTextEdit, QLabel, QProgressBar, QFileDialog

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('ESP File Uploader')

        root_layout = QVBoxLayout()

        # TOP BEGINNING
        top_group = QGroupBox()
        top_group_layout = QVBoxLayout()

        detected_devices = QLabel('ESP Devices Detected:')
        device_list = QTextEdit()
   
        top_group_layout.addWidget(detected_devices)
        top_group_layout.addWidget(device_list)
      
        top_group.setLayout(top_group_layout)
   
        # TOP END

        # MIDDLE LEFT GROUP BEGINNING
        middle_left_group = QGroupBox()
        middle_left_group_layout = QVBoxLayout()

        device_chooser_label = QLabel('Choose Device:')
        self.device_chooser = QComboBox()
        self.device_chooser.addItems(['Deauther', 'Camera Detector'])
        self.device_chooser.activated.connect(self.set_file_chooser_label)
        self.file_chooser_label = QLabel()
        file_chooser_button = QPushButton('Browse')
        file_chooser_button.clicked.connect(self.open_file_browser)
        self.upload_button_label = QLabel()
        upload_button = QPushButton('Upload')
        
        middle_left_group_layout.addWidget(device_chooser_label)
        middle_left_group_layout.addWidget(self.device_chooser)
        middle_left_group_layout.addWidget(self.file_chooser_label)
        middle_left_group_layout.addWidget(file_chooser_button)
        middle_left_group_layout.addWidget(self.upload_button_label)
        middle_left_group_layout.addWidget(upload_button)
        
        middle_left_group.setLayout(middle_left_group_layout)
      
        # MIDDLE LEFT GROUP END

        # MIDDLE RIGHT GROUP BEGINNING
        middle_right_group = QGroupBox()
        middle_right_group_layout = QVBoxLayout()

        current_device = QLabel('ESP 1/2')
        upload_messages = QTextEdit()
   
        middle_right_group_layout.addWidget(current_device)
        middle_right_group_layout.addWidget(upload_messages)
    
        middle_right_group.setLayout(middle_right_group_layout)
        # MIDDLE RIGHT GROUP END

        # MIDDLE GROUPS BEGINNING
     
        middle_groups_layout = QHBoxLayout()

        middle_groups_layout.addWidget(middle_left_group)
        middle_groups_layout.addWidget(middle_right_group)

        # MIDDLE GROUPS END

        # BOTTOM GROUP BEGINNING
        bottom_group = QGroupBox()
        bottom_group_layout = QVBoxLayout()

        upload_progress_label = QLabel('Upload Progress')
        upload_progress = QProgressBar()

        bottom_group_layout.addWidget(upload_progress_label)
        bottom_group_layout.addWidget(upload_progress)

        bottom_group.setLayout(bottom_group_layout)
        # BOTTOM GROUP END
   
        root_layout.addWidget(top_group)
        root_layout.addLayout(middle_groups_layout)
        root_layout.addWidget(bottom_group)

        self.setLayout(root_layout)

    def set_file_chooser_label(self):
        text_file = ''
        if self.device_chooser.currentText() == 'Deauther':
            text_file = 'deauther_settings.txt'
        elif self.device_chooser.currentText() == 'Camera Detector':
            text_file = 'macs.txt'

        self.file_chooser_label.setText(f'Browse to {text_file}')
 
    def open_file_browser(self):
        file_browser = QFileDialog()
        file_browser.setFileMode(QFileDialog.ExistingFiles)
        file_browser.setNameFilter("Text Files (*.txt)")
        file_browser.setViewMode(QFileDialog.Detail)
        # file_paths, _ = file_browser.getOpenFileNames()
        if file_browser.exec():
            fileNames = file_browser.selectedFiles()
            self.upload_button_label.setText(str(fileNames))

    
    
    # @QtCore.Slot()
    # def magic(self):
    #     self.text.setText(random.choice(self.hello))

if __name__ == "__main__":
    app = QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())