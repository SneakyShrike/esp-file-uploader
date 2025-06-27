import sys
import random
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QComboBox, QTextEdit, QLabel, QProgressBar

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('ESP File Uploader')

        root_layout = QVBoxLayout()

        # TOP GROUP BEGINNING
        top_group = QGroupBox()
        top_group_layout = QHBoxLayout()

        device_chooser_label = QLabel('Device to Upload too:')
        device_chooser = QComboBox()
        device_chooser.addItems(['Deauther', 'Camera Dectector'])
        file_chooser_label = QLabel('Choose File To Upload:')
        file_chooser_button = QPushButton('Browse')
        upload_button_label = QLabel('Upload File:')
        upload_button = QPushButton('Upload')

        top_group_layout.addWidget(device_chooser_label)
        top_group_layout.addWidget(device_chooser)
        top_group_layout.addWidget(file_chooser_label)
        top_group_layout.addWidget(file_chooser_button)
        top_group_layout.addWidget(upload_button_label)
        top_group_layout.addWidget(upload_button)
        
        top_group.setLayout(top_group_layout)
        # TOP GROUP END

        # MIDDLE LEFT GROUP BEGINNING
        middle_left_group = QGroupBox()
        middle_left_group_layout = QVBoxLayout()

        device_list = QTextEdit()
   
        middle_left_group_layout.addWidget(device_list)
      
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
        middle_groups = QGroupBox()
        middle_groups_layout = QHBoxLayout()

        middle_groups_layout.addWidget(middle_left_group)
        middle_groups_layout.addWidget(middle_right_group)

        middle_groups.setLayout(middle_groups_layout)
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
        root_layout.addWidget(middle_groups)
        root_layout.addWidget(bottom_group)

        self.setLayout(root_layout)



        

        
   


       

    # @QtCore.Slot()
    # def magic(self):
    #     self.text.setText(random.choice(self.hello))

if __name__ == "__main__":
    app = QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())