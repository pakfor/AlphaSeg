from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class ImportPointsWindow(QMainWindow):
    import_done_signal = pyqtSignal()
    
    def __init__(self):
        super(ImportPointsWindow, self).__init__()
        self.setWindowTitle('Import Points')
        self.build_gui()
        self.marking_info = []
        self.temp_area = []
        self.point = None

    def build_gui(self):
        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)
        main_v_layout = QVBoxLayout()
        base_widget.setLayout(main_v_layout)

        # Table for displaying information about the points to be imported
        self.points_info_table = QTableWidget()
        self.points_info_table.setColumnCount(3)
        self.points_info_table.setHorizontalHeaderLabels(["Select", "Label", "No. of Points"])
        self.points_info_table.setWordWrap(True)
        self.points_info_table.clearContents()
        self.points_info_table.setRowCount(0)

        # Button
        self.import_selected_button = QPushButton("Import Selected")
        self.import_selected_button.clicked.connect(self.process_dictionary)
        self.reset_button = QPushButton("Reset")
        self.cancel_button = QPushButton("Cancel")
        function_h_layout = QHBoxLayout()
        function_h_layout.addWidget(self.reset_button)
        function_h_layout.addWidget(self.import_selected_button)
        function_h_layout.addWidget(self.cancel_button)

        # Layout
        main_v_layout.addWidget(self.points_info_table)
        main_v_layout.addLayout(function_h_layout)

    def fill_table(self, points):
        self.point = points
        # Loop through labels
        for key in points.keys():
            for i in range(0, len(points[key])):
                # Information
                table_number_of_area_points = QLabel(str(len(points[key][i])))
                self.temp_area.append(points[key][i])
                table_select_check_box = QCheckBox()
                table_select_check_box.setChecked(True)
                table_area_label_text = QLineEdit()
                table_area_label_text.setText(str(key))

                # Fill table
                self.points_info_table.insertRow(self.points_info_table.rowCount())
                self.points_info_table.setCellWidget(self.points_info_table.rowCount() - 1, 0, table_select_check_box)
                self.points_info_table.setCellWidget(self.points_info_table.rowCount() - 1, 1, table_area_label_text)
                self.points_info_table.setCellWidget(self.points_info_table.rowCount() - 1, 2, table_number_of_area_points)
    
    def process_dictionary(self):
        for i in range(self.points_info_table.rowCount()):
            check_box = self.points_info_table.cellWidget(i, 0)
            no_points = len(self.temp_area[i])
            if no_points > 2:
                draw_type = "Contour"
            else:
                draw_type = "Bounding Box"
            if check_box.isChecked():
                cord_qt = []
                for j in range(no_points):
                    cord_qt.append(QPoint(self.temp_area[i][j][0], self.temp_area[i][j][1]))                    
                self.marking_info.append([draw_type,self.points_info_table.cellWidget(i,1).text(),cord_qt,True,True])
            else:
                pass
        self.import_done_signal.emit()

# For testing only
if __name__ == '__main__':
    import sys
    import PyQt5
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    window = ImportPointsWindow()
    window.show()
    sys.exit(app.exec_())