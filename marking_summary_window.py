from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class MarkingSummaryWindow(QMainWindow):

    def __init__(self, marking_info):
        super(MarkingSummaryWindow, self).__init__()
        self.marking_info = marking_info
        self.label_summary_info = None
        self.setWindowTitle('Summary')
        self.build_gui()

    def build_gui(self):
        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)
        main_v_layout = QVBoxLayout()
        base_widget.setLayout(main_v_layout)

        # Initialize summary table
        self.label_summary_table = QTableWidget()
        self.label_summary_table.setColumnCount(2)
        self.label_summary_table.setHorizontalHeaderLabels(["Label", "Count"])
        self.label_summary_table.setWordWrap(True)
        self.label_summary_table.clearContents()
        self.label_summary_table.setRowCount(0)

        self.aggregate_statistics()
        self.populate_label_summary_table()
        main_v_layout.addWidget(self.label_summary_table)

    def aggregate_statistics(self):
        # self.marking_info = [TYPE, LABEL, [POINTS/CORNERS], VISUALIZATION]
        label_set = list(set([self.marking_info[i][1] for i in range(0, len(self.marking_info))]))
        self.label_summary_info = dict.fromkeys(label_set, 0)
        for i in range(0, len(self.marking_info)):
            self.label_summary_info[self.marking_info[i][1]] += 1

    def populate_label_summary_table(self):
        self.label_summary_table.clearContents()
        self.label_summary_table.setRowCount(0)
        for key in self.label_summary_info.keys():
            self.label_summary_table.insertRow(self.label_summary_table.rowCount())
            label_text = QLabel()
            label_text.setText(str(key))
            label_count_text = QLabel()
            label_count_text.setText(str(self.label_summary_info[key]))
            self.label_summary_table.setCellWidget(self.label_summary_table.rowCount() - 1, 0, label_text)
            self.label_summary_table.setCellWidget(self.label_summary_table.rowCount() - 1, 1, label_count_text)


# For testing only
if __name__ == '__main__':
    import sys
    import PyQt5
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    window = MarkingSummaryWindow(1)
    window.show()
    sys.exit(app.exec_())