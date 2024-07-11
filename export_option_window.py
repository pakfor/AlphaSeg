from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import json
import cv2
import numpy as np
import matplotlib.pyplot as plt

class ExportOptionWindow(QMainWindow):
    def __init__(self, marking_info, orig_dim, display_dim):
        super(ExportOptionWindow, self).__init__()
        self.marking_info = marking_info
        self.orig_dim = orig_dim  # (Width, Height)
        self.display_dim = display_dim  # (Width, Height)
        self.image_scaled_ratio = self.orig_dim[0] / self.display_dim[0]
        self.setWindowTitle("Export")
        self.build_gui()

    def build_gui(self):
        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)
        main_v_layout = QVBoxLayout()
        main_h_layout = QHBoxLayout()
        base_widget.setLayout(main_v_layout)

        self.marking_info_table = QTableWidget()
        self.marking_info_table.setFixedWidth(600)
        self.marking_info_table.setFixedHeight(600)
        self.marking_info_table.setColumnCount(2)
        self.marking_info_table.setHorizontalHeaderLabels(["Type", "Label"])
        self.marking_info_table.setWordWrap(True)
        self.marking_info_table.clearContents()
        self.marking_info_table.setRowCount(0)
        self.fill_table()
        main_h_layout.addWidget(self.marking_info_table)

        export_option_v_layout = QVBoxLayout()
        export_option_v_layout.setAlignment(Qt.AlignTop)

        contour_export_option_group = QGroupBox("Contour")
        contour_export_option_group.setFixedWidth(320)
        contour_export_option_v_layout = QVBoxLayout()
        self.contour_export_points_checkbox = QCheckBox("Export Points (.XML)")
        self.contour_export_mask_checkbox = QCheckBox("Export Mask (.NPY)")
        contour_export_option_v_layout.addWidget(self.contour_export_points_checkbox)
        contour_export_option_v_layout.addWidget(self.contour_export_mask_checkbox)
        contour_export_option_group.setLayout(contour_export_option_v_layout)

        b_box_export_option_group = QGroupBox("Bounding Box")
        b_box_export_option_v_layout = QVBoxLayout()
        self.b_box_export_exact_corners = QCheckBox("Export Corners (.XML)")
        self.b_box_export_yolo_format = QCheckBox("Export as YOLO format (.TXT)")
        self.b_box_export_mask = QCheckBox("Export Mask (.NPY)")
        b_box_export_option_v_layout.addWidget(self.b_box_export_exact_corners)
        b_box_export_option_v_layout.addWidget(self.b_box_export_yolo_format)
        b_box_export_option_v_layout.addWidget(self.b_box_export_mask)
        b_box_export_option_group.setLayout(b_box_export_option_v_layout)

        other_export_option_group = QGroupBox("Other")

        export_option_v_layout.addWidget(contour_export_option_group)
        export_option_v_layout.addWidget(b_box_export_option_group)
        export_option_v_layout.addWidget(other_export_option_group)
        main_h_layout.addLayout(export_option_v_layout)

        # Directory
        directory_h_layout = QHBoxLayout()
        self.export_directory = QLabel()
        self.export_directory.setText("Export to Directory: Not Set")
        self.browse_directory = QPushButton()
        self.browse_directory.setText("Browse")
        self.browse_directory.setFixedWidth(150)
        self.browse_directory.clicked.connect(self.select_export_directory)
        directory_h_layout.addWidget(self.export_directory)
        directory_h_layout.addWidget(self.browse_directory)

        # Buttons
        button_h_layout = QHBoxLayout()
        button_h_layout.setAlignment(Qt.AlignRight)
        self.export_button = QPushButton("Export")
        self.export_button.setFixedWidth(150)
        self.export_button.clicked.connect(self.export_with_option)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(150)
        button_h_layout.addWidget(self.export_button)
        button_h_layout.addWidget(self.cancel_button)

        main_v_layout.addLayout(main_h_layout)
        main_v_layout.addLayout(directory_h_layout)
        main_v_layout.addLayout(button_h_layout)

    def fill_table(self):
        for i in range(0, len(self.marking_info)):
            marking_type = QLabel()
            marking_type.setText(str(self.marking_info[i][0]))
            marking_label = QLineEdit()
            marking_label.setText(str(self.marking_info[i][1]))

            self.marking_info_table.insertRow(self.marking_info_table.rowCount())
            self.marking_info_table.setCellWidget(self.marking_info_table.rowCount() - 1, 0, marking_type)
            self.marking_info_table.setCellWidget(self.marking_info_table.rowCount() - 1, 1, marking_label)

    def select_export_directory(self):
        dialog = QFileDialog()
        self.export_directory_path = dialog.getExistingDirectory(None, "Select Folder")
        self.export_directory.setText(f"Export to Directory: {self.export_directory_path}")

    def export_with_option(self):
        if self.contour_export_points_checkbox:
            self.export_contour_as_point()
        if self.contour_export_mask_checkbox:
            self.export_contour_as_mask()
        if self.b_box_export_exact_corners:
            pass
        if self.b_box_export_yolo_format:
            self.export_b_box_in_yolo_format()
        if self.b_box_export_mask:
            pass

    def export_b_box_in_yolo_format(self):
        # Input: [[TYPE, LABEL, [CORNER1, CORNER2]], ...]
        # Output (YOLO): LABEL X_CENTER_NORM Y_CENTER_NORM WIDTH_NORM HEIGHT_NORM
        output_string = ""
        for i in range(0, len(self.marking_info)):
            if self.marking_info[i][0] == "Bounding Box":
                label = self.marking_info[i][1]
                corner1 = self.marking_info[i][2][0]
                corner2 = self.marking_info[i][2][1]
                corner1_x = corner1.x()
                corner1_y = corner1.y()
                corner2_x = corner2.x()
                corner2_y = corner2.y()
                x_center_norm = ((corner1_x + corner2_x) / 2) / self.orig_dim[0]
                y_center_norm = ((corner1_y + corner2_y) / 2) / self.orig_dim[1]
                width_norm = (corner2_x - corner1_x) / self.orig_dim[0]
                height_norm = (corner2_y - corner1_y) / self.orig_dim[1]
                output_string += f"{label} {x_center_norm} {y_center_norm} {width_norm} {height_norm}\n"
            else:
                pass
        if output_string != "":
            output_string = output_string[:-1]  # For removing the \n at the end of the string
            with open(f"{self.export_directory_path}/TEST_B_BOX_YOLO.txt", "w") as text_file:
                text_file.write(output_string)

    def export_contour_as_point(self):
        #label_set = list(set([self.marking_info[i][1] for i in range(0, len(self.marking_info)) if self.marking_info[i][0] == "Contour"]))
        point_label_pair_dict = {}
        for i in range(0, len(self.marking_info)):
            if self.marking_info[i][0] == "Contour":
                points_ready = []
                for j in range(0, len(self.marking_info[i][2])):
                    points_ready.append([min([int(self.marking_info[i][2][j].x()), int(self.orig_dim[0]) - 1]),
                                         min([int(self.marking_info[i][2][j].y()), int(self.orig_dim[1]) - 1])])
                if self.marking_info[i][1] not in point_label_pair_dict.keys():
                    point_label_pair_dict[self.marking_info[i][1]] = [points_ready]
                else:
                    point_label_pair_dict[self.marking_info[i][1]].append(points_ready)
        save_as_json = open(f"{self.export_directory_path}/TEST_CONTOUR_POINTS.txt", "w")
        json.dump(point_label_pair_dict, save_as_json, indent=4)
        save_as_json.close()

    def export_contour_as_mask(self):
        # Input: [[TYPE, LABEL, [POINT1, POINT2, POINT3, ...]], ...]
        # Output: numpy.ndarray(Number of classes/labels, Mask)
        label_set = list(set([self.marking_info[i][1] for i in range(0, len(self.marking_info)) if self.marking_info[i][0] == "Contour"]))
        num_labels = len(label_set)
        mask_npy = np.zeros((int(self.orig_dim[1]), int(self.orig_dim[0]), num_labels))
        for i in range(0, len(self.marking_info)):
            if self.marking_info[i][0] == "Contour":
                points_ready = []
                for j in range(0, len(self.marking_info[i][2])):
                    points_ready.append([min([int(self.marking_info[i][2][j].x()), int(self.orig_dim[0]) - 1]),
                                         min([int(self.marking_info[i][2][j].y()), int(self.orig_dim[1]) - 1])])
                points_ready = np.array(points_ready)
                point_specific_label = self.marking_info[i][1]
                index = label_set.index(point_specific_label)
                mask_temp = mask_npy[:, :, index]
                cv2.fillPoly(mask_temp, [points_ready], (1))
                plt.imshow(mask_temp)
                plt.show()
                mask_npy[:, :, index] = mask_temp
            else:
                pass
        np.save(f"{self.export_directory_path}/TEST_CONTOUR_MASK.npy", mask_npy)

# For testing only
if __name__ == '__main__':
    import sys
    import PyQt5
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    window = ExportOptionWindow([["Contour", "LABEL1"], ["Bounding Box", "LABEL2"]], (700, 700), (700, 700))
    window.show()
    sys.exit(app.exec_())