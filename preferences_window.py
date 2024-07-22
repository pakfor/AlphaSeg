from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class PreferencesWindow(QMainWindow):

    def __init__(self):
        super(PreferencesWindow, self).__init__()
        self.setWindowTitle('Preferences')
        self.build_gui()

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
        self.label_drop_down_list_text = QLabel("Label")
        self.label_drop_down_list_input = QLineEdit()
        label_drop_down_list_layout.addWidget(self.label_drop_down_list_text)
        label_drop_down_list_layout.addWidget(self.label_drop_down_list_input)

        self.default_parameter_load = QPushButton("Load from file")

        preferences_tab_layout.addLayout(label_drop_down_list_layout)
        preferences_tab_layout.addWidget(self.default_parameter_load)

        control_h_layout = QHBoxLayout()
        control_h_layout.setAlignment(Qt.AlignRight)
        self.confirm_setting = QPushButton("Set")
        self.cancel_setting = QPushButton("Clear All")
        control_h_layout.addWidget(self.confirm_setting)
        control_h_layout.addWidget(self.cancel_setting)

        self.main_tab.addTab(self.preferences_tab_widget, "Preferences")

        base_v_layout.addLayout(control_h_layout)

# For testing only
if __name__ == '__main__':
    import sys
    import PyQt5
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    window = PreferencesWindow()
    window.show()
    sys.exit(app.exec_())