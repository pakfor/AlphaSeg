from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import main_window

class PreferencesWindow(QMainWindow):
    change_label_drop_down_list_signal = pyqtSignal()

    def __init__(self, label):
        super(PreferencesWindow, self).__init__()
        self.setWindowTitle('Preferences')
        self.label = label
        self.build_gui()
        self.gui = main_window.MainWindow()

    def build_gui(self):
        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)
        base_v_layout = QVBoxLayout()
        base_widget.setLayout(base_v_layout)

        self.main_tab = QTabWidget()
        base_v_layout.addWidget(self.main_tab)

        self.preferences_tab_widget = QWidget()
        preferences_tab_layout = QVBoxLayout()
        preferences_tab_layout.setAlignment(Qt.AlignTop)
        self.preferences_tab_widget.setLayout(preferences_tab_layout)

        label_drop_down_list_layout = QHBoxLayout()
        #self.label_drop_down_list_text = QLabel("Label")
        self.label_drop_down_list = QTableWidget()
        self.label_drop_down_list.setColumnCount(2)
        self.label_drop_down_list.setHorizontalHeaderLabels(["Labels", "Select"])
        self.label_drop_down_list.setRowCount(0)
        #label_drop_down_list_layout.addWidget(self.label_drop_down_list_text)
        label_drop_down_list_layout.addWidget(self.label_drop_down_list)
        self.refresh_drop_down_table()

        self.default_parameter_load = QPushButton("Load from file")

        preferences_tab_layout.addLayout(label_drop_down_list_layout)
        preferences_tab_layout.addWidget(self.default_parameter_load)

        control_h_layout = QHBoxLayout()
        control_h_layout.setAlignment(Qt.AlignRight)
        self.confirm_setting_button = QPushButton("Set")
        self.cancel_setting_button = QPushButton("Clear")
        control_h_layout.addWidget(self.confirm_setting_button)
        control_h_layout.addWidget(self.cancel_setting_button)
        self.confirm_setting_button.clicked.connect(self.add_label_list)
        self.cancel_setting_button.clicked.connect(self.remove_selected_label_list)

        self.main_tab.addTab(self.preferences_tab_widget, "Preferences")

        base_v_layout.addLayout(control_h_layout)
    
    def refresh_drop_down_table(self):
        self.label_drop_down_list.clearContents()
        self.label_drop_down_list.setRowCount(0)
        
        if len(self.label) == 0:
            self.label_drop_down_list.insertRow(self.label_drop_down_list.rowCount())
            label_drop_down_list_input = QLineEdit()
            label_select_initial = QCheckBox()
            label_select_initial.setChecked(False)
            self.label_drop_down_list.setCellWidget(self.label_drop_down_list.rowCount()-1, 0, label_drop_down_list_input)
            self.label_drop_down_list.setCellWidget(self.label_drop_down_list.rowCount()-1, 1, label_select_initial)
        else:
            for i in range(0, len(self.label)):
                self.label_drop_down_list.insertRow(self.label_drop_down_list.rowCount())
                label_drop_down_list_list = QLineEdit()
                label_drop_down_list_list.setText(str(self.label[i]))
                label_drop_down_list_list.textChanged.connect(self.refresh_label_list)
                label_select = QCheckBox()
                label_select.setChecked(False)
                self.label_drop_down_list.setCellWidget(self.label_drop_down_list.rowCount()-1, 0, label_drop_down_list_list)
                self.label_drop_down_list.setCellWidget(self.label_drop_down_list.rowCount()-1, 1, label_select)
            self.label_drop_down_list.insertRow(self.label_drop_down_list.rowCount())
            label_drop_down_list_extra = QLineEdit()
            label_select_extra = QCheckBox()
            label_select_extra.setChecked(False)
            self.label_drop_down_list.setCellWidget(self.label_drop_down_list.rowCount()-1, 0, label_drop_down_list_extra)
            self.label_drop_down_list.setCellWidget(self.label_drop_down_list.rowCount()-1, 1, label_select_extra)            
        
    def refresh_label_list(self):
        if len(self.label) == 0:
            pass
        else:
            for i in range(0, len(self.label)):
                self.label[i] = self.label_drop_down_list.cellWidget(i,0).text()
    
    def add_label_list(self):
        self.label.append(str(self.label_drop_down_list.cellWidget(self.label_drop_down_list.rowCount()-1,0).text()))
        self.change_label_drop_down_list_signal.emit()
        self.refresh_drop_down_table()
        
    def remove_selected_label_list(self):
        if len(self.label) == 0:
            pass
        else:
            check_list = []
            for i in range(0, self.label_drop_down_list.rowCount()):
                if self.label_drop_down_list.cellWidget(i,1).isChecked():
                    check_list.append(True)
                else:
                    check_list.append(False)
            self.label = [self.label[i] for i in range(len(self.label)) if not check_list[i]]
        self.refresh_drop_down_table()
        self.change_label_drop_down_list_signal.emit()
                 
        
# For testing only
if __name__ == '__main__':
    import sys
    import PyQt5
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    window = PreferencesWindow()
    window.show()
    sys.exit(app.exec_())