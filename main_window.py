import sys
import copy
import cv2
import json
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageQt
from PyQt5.QtCore import QEvent, QSize, Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QWidget, QFileDialog, QLabel, QGroupBox, QStatusBar, QTableWidget, QTableWidgetItem, QCheckBox, QLineEdit, QMenuBar, QMenu, QAction

# Custom modules
import main_display
import import_points_window


class MainWindow(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        # Basic software information
        self.VERSION = "1.1"
        self.RELEASE_DATE = "22-Jun-2024"
        self.COMPOSER = "NGPF"

        self.orig_image = None
        self.orig_image_dir = None
        self.new_image = None
        self.new_image_dir = None

        self.setWindowTitle(f"AlphaSEG - V.{self.VERSION}")
        self.setFixedSize(QSize(1300, 1000))

        # Menu Bar
        self.menu_bar = QMenuBar(self)
        self.file_menu = QMenu("&File", self)
        self.edit_menu = QMenu("&Edit", self)
        self.help_menu = QMenu("&Help", self)
        self.menu_bar.addMenu(self.file_menu)
        self.menu_bar.addMenu(self.edit_menu)
        self.menu_bar.addMenu(self.help_menu)
        self.setMenuBar(self.menu_bar)
        self.open_action = QAction("&Open", self)
        self.open_action.triggered.connect(self.browse_image)
        self.file_menu.addAction(self.open_action)
        # Export
        self.export_mask_action = QAction("&Export Masks", self)
        self.export_mask_action.triggered.connect(self.export_mask)
        self.file_menu.addAction(self.export_mask_action)
        self.export_points_action = QAction("&Export Points", self)
        self.export_points_action.triggered.connect(self.export_points)
        self.file_menu.addAction(self.export_points_action)
        self.export_vis_action = QAction("&Export Visualizations", self)
        self.export_vis_action.triggered.connect(self.export_vis)
        self.file_menu.addAction(self.export_vis_action)
        # Import
        self.import_action = QAction("&Import", self)
        self.import_action.triggered.connect(self.import_points_from_json)
        self.file_menu.addAction(self.import_action)
        self.pref_action = QAction("&Preferences", self)
        #self.pref_action.triggered.connect(self.open_pref_window)
        self.edit_menu.addAction(self.pref_action)

        # Status bar
        self.base_status_bar = QStatusBar()
        self.setStatusBar(self.base_status_bar)
        status_base_info = QLabel()
        status_base_info.setText(f"Version: {self.VERSION}    Release Date: {self.RELEASE_DATE}    Composer: {self.COMPOSER}")
        self.base_status_bar.addPermanentWidget(status_base_info)

        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)

        # Main
        main_h_layout = QHBoxLayout()

        # Leftmost image column
        left_image_v_layout = QVBoxLayout()

        # Image information
        image_info_group = QGroupBox("Information")
        image_info_v_layout = QVBoxLayout()
        image_info_v_layout.setAlignment(Qt.AlignTop)
        self.old_image_size_label = QLabel()
        self.old_image_dir_label = QLabel()
        image_info_v_layout.addWidget(self.old_image_size_label)
        image_info_v_layout.addWidget(self.old_image_dir_label)
        image_info_group.setLayout(image_info_v_layout)
        # Main display
        view_group = QGroupBox("Image")
        view_group_h_layout = QHBoxLayout()
        view_group_h_layout.setAlignment(Qt.AlignTop)
        self.old_image_pixmap = main_display.QLabelCanvas()
        self.old_image_pixmap.installEventFilter(self.old_image_pixmap)
        self.old_image_pixmap.table_refresh_signal.connect(self.refresh_seg_label_list_table)
        view_group_h_layout.addWidget(self.old_image_pixmap)
        view_group.setLayout(view_group_h_layout)
        view_group.setMinimumHeight(700)
        # Tool
        tool_group = QGroupBox("Tool")
        tool_group_h_layout = QHBoxLayout()
        tool_group_h_layout.setAlignment(Qt.AlignTop)
        self.draw_polygon_button = QPushButton("Create Mask")
        self.draw_polygon_button.setCheckable(True)
        self.draw_polygon_button.clicked.connect(self.enable_drawing)
        tool_group_h_layout.addWidget(self.draw_polygon_button)
        tool_group.setLayout(tool_group_h_layout)

        left_image_v_layout.addWidget(image_info_group)
        left_image_v_layout.addWidget(view_group)
        left_image_v_layout.addWidget(tool_group)

        # Mask and label
        seg_label_list_group = QGroupBox("Mask and Label")
        seg_label_list_group.setMaximumWidth(400)
        seg_label_list_v_layout = QVBoxLayout()

        self.seg_label_list_table = QTableWidget()
        self.seg_label_list_table.setColumnCount(4)
        self.seg_label_list_table.setHorizontalHeaderLabels(["Select", "Show", "Label", "No. of Points"])
        self.seg_label_list_table.setWordWrap(True)
        self.seg_label_list_table.clearContents()
        self.seg_label_list_table.setRowCount(0)

        seg_label_list_function_h_layout = QHBoxLayout()
        self.remove_mask_button = QPushButton("Remove Selected")
        self.remove_mask_button.clicked.connect(self.remove_selected)
        seg_label_list_function_h_layout.addWidget(self.remove_mask_button)

        seg_label_list_function_h_layout_2 = QHBoxLayout()
        self.remove_all_mask_button = QPushButton("Remove All")
        self.remove_all_mask_button.clicked.connect(self.old_image_pixmap.clear_all_markings)
        seg_label_list_function_h_layout_2.addWidget(self.remove_all_mask_button)

        seg_label_list_v_layout.addWidget(self.seg_label_list_table)
        seg_label_list_v_layout.addLayout(seg_label_list_function_h_layout)
        seg_label_list_v_layout.addLayout(seg_label_list_function_h_layout_2)
        seg_label_list_group.setLayout(seg_label_list_v_layout)

        main_h_layout.addLayout(left_image_v_layout)
        main_h_layout.addWidget(seg_label_list_group)
        base_widget.setLayout(main_h_layout)

        # Other sub windows
        self.import_points_json_window = None

    def enable_drawing(self):
        if self.draw_polygon_button.isChecked():
            self.old_image_pixmap.draw_lines = True
        else:
            self.old_image_pixmap.draw_lines = False

    def set_pixmap_from_array(self, image_arr):
        qimage = QImage(image_arr, image_arr.shape[1], image_arr.shape[0], QImage.Format_RGB888)
        self.image_width_orig = image_arr.shape[1]
        self.image_height_orig = image_arr.shape[0]
        self.qpixmap = QPixmap.fromImage(qimage)
        self.qpixmap = self.qpixmap.scaled(650, 650, Qt.KeepAspectRatio)
        self.qpixmap_orig = self.qpixmap.copy()
        self.image_width_scaled = self.qpixmap_orig.rect().width()
        self.image_height_scaled = self.qpixmap_orig.rect().height()
        self.old_image_pixmap.canvas_orig = self.qpixmap_orig
        self.old_image_pixmap.initiate_canvas_and_set_pixmap(self.qpixmap)

    def process_tif(self, tif_image):
        def normalize_image(image):
            imin, imax = np.min(image), np.max(image)
            irange = abs(imax - imin)
            if irange == 0:
                return image
            else:
                return (image - imin) / irange
        tif_red = tif_image[:, :, 2]
        tif_green = tif_image[:, :, 1]
        tif_blue = tif_image[:, :, 0]
        tif_image = (normalize_image(np.stack((tif_red, tif_green, tif_blue), axis=2)) * 255.0).astype('uint8')
        return tif_image

    def browse_image(self):
        support_file_format = ["png", "PNG", "jpg", "JPG", "tif", "TIF", "tiff", "TIFF"]
        open_file = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;PNG (*.png;*.PNG);;JPEG (*.jpg;*.JPG);;TIFF (*.tif;*.TIF;*.tiff;*.TIFF")[0]
        if open_file[-3:] in support_file_format:
            self.orig_image_dir = open_file
            self.orig_image = self.image_loader(self.orig_image_dir)
            self.set_pixmap_from_array(self.orig_image)
            self.old_image_size_label.setText(f"Size: {self.orig_image.shape[1]} x {self.orig_image.shape[0]}")
            self.old_image_dir_label.setText(f"Directory: {self.orig_image_dir}")
        elif open_file == "":
            pass
        else:
            return

    def save_image(self):
        save_file = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;PNG (*.png;*.PNG);;JPEG (*.jpg;*.JPG)")[0]
        self.new_image_dir = save_file
        image_to_save = copy.deepcopy(self.new_image)
        image_to_save = image_to_save.astype(np.uint8)
        image_to_save_pil = Image.fromarray(image_to_save)
        image_to_save_pil.save(self.new_image_dir)

    def image_loader(self, image_dir):
        if image_dir.split(".")[-1] in ["tif", "TIF", "tiff", "TIFF"]:
            return self.process_tif(cv2.imread(image_dir, -1))
        return np.array(Image.open(image_dir))

    def refresh_seg_label_list_table(self):
        self.areas = self.old_image_pixmap.areas
        self.area_labels = self.old_image_pixmap.area_labels
        self.area_visible = self.old_image_pixmap.area_visible
        self.seg_label_list_table.clearContents()
        self.seg_label_list_table.setRowCount(0)

        for i in range(0, len(self.areas)):
            self.seg_label_list_table.insertRow(self.seg_label_list_table.rowCount())

            # Check box for selection
            table_select_check_box = QCheckBox()
            table_select_check_box.setCheckState(False)

            # Check box for visualization option
            table_show_check_box = QCheckBox()
            table_show_check_box.setCheckState(self.area_visible[i])
            table_show_check_box.clicked.connect(self.refresh_pixmap_with_visualization_option)

            # Labels for marked areas
            table_area_label_text = QLineEdit()
            table_area_label_text.setText(str(self.area_labels[i]))
            table_area_label_text.textChanged.connect(self.refresh_area_labels)

            # Labels for number of marked points that define the areas
            table_number_of_area_points = QLabel(str(len(self.areas[i])))

            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 0, table_select_check_box)
            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 1, table_show_check_box)
            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 2, table_area_label_text)
            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 3, table_number_of_area_points)

    def refresh_pixmap_with_visualization_option(self):
        if self.seg_label_list_table.rowCount() == 0:
            pass
        else:
            checked_list = []
            for i in range(0, self.seg_label_list_table.rowCount()):
                if self.seg_label_list_table.cellWidget(i, 1).isChecked():
                    checked_list.append(True)
                else:
                    checked_list.append(False)
            self.old_image_pixmap.area_visible = checked_list
            self.old_image_pixmap.refresh_pixmap_acc_to_check_box(self.areas, checked_list)

    def refresh_area_labels(self):
        if self.seg_label_list_table.rowCount() == 0:
            pass
        else:
            area_label_list = []
            for i in range(0, self.seg_label_list_table.rowCount()):
                area_label_list.append(self.seg_label_list_table.cellWidget(i, 2).text())
            self.old_image_pixmap.area_labels = area_label_list

    def reset_pixmap(self):
        self.old_image_pixmap.setPixmap(self.qpixmap_orig)
        self.old_image_pixmap.update()

    def export_mask(self):
        self.export_areas(None, "mask", None)

    def export_points(self):
        self.export_areas(None, "points", None)

    def export_vis(self):
        self.export_areas(None, "vis", None)

    def export_areas(self, areas, mode, save_dir):
        if mode == "mask":
            save_file_as_npy_dir = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;NPY (*.npy)")[0]
            # Assumed the image is scaled with the same ratio along its width and height
            image_scaled_ratio = int(self.image_height_orig) / int(self.image_height_scaled)
            area_labels_set = list(set(self.old_image_pixmap.area_labels))
            area_labels = self.old_image_pixmap.area_labels
            points = self.old_image_pixmap.areas
            number_of_classes = len(area_labels_set)
            mask_npy = np.zeros((int(self.image_height_orig), int(self.image_width_orig), number_of_classes))
            for i in range(0, len(points)):
                points_ready = []
                for j in range(0, len(points[i])):
                    points_ready.append([min([int(points[i][j].x() * image_scaled_ratio), int(self.image_width_orig) - 1]),
                                         min([int(points[i][j].y() * image_scaled_ratio), int(self.image_height_orig) - 1])])
                points_ready = np.array(points_ready)
                point_specific_label = area_labels[i]
                index = area_labels_set.index(point_specific_label)
                mask_temp = mask_npy[:, :, index]
                cv2.fillPoly(mask_temp, [points_ready], (1))
                plt.imshow(mask_temp)
                plt.show()
                mask_npy[:, :, index] = mask_temp
            np.save(save_file_as_npy_dir, mask_npy)
        elif mode == "points":
            save_file_as_json_dir = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;JSON (*.json)")[0]
            image_scaled_ratio = int(self.image_height_orig) / int(self.image_height_scaled)
            area_labels = self.old_image_pixmap.area_labels
            points = self.old_image_pixmap.areas
            point_label_pair_dict = {}
            for i in range(0, len(points)):
                points_ready = []
                for j in range(0, len(points[i])):
                    points_ready.append([min([int(points[i][j].x() * image_scaled_ratio), int(self.image_width_orig) - 1]),
                                         min([int(points[i][j].y() * image_scaled_ratio), int(self.image_height_orig) - 1])])
                point_specific_label = area_labels[i]
                if point_specific_label not in point_label_pair_dict.keys():
                    point_label_pair_dict[point_specific_label] = [points_ready]
                else:
                    point_label_pair_dict[point_specific_label].append(points_ready)
            #point_label_pair_json = json.dumps(point_label_pair_dict, indent = 4)
            save_as_json = open(save_file_as_json_dir, "w")
            json.dump(point_label_pair_dict, save_as_json, indent=4)
            save_as_json.close()
        elif mode == "vis":
            save_file_as_vis_dir = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;PNG (*.png)")[0]
            # Assumed the image is scaled with the same ratio along its width and height
            image_scaled_ratio = int(self.image_height_orig) / int(self.image_height_scaled)
            area_labels_set = list(set(self.old_image_pixmap.area_labels))
            area_labels = self.old_image_pixmap.area_labels
            points = self.old_image_pixmap.areas
            number_of_classes = len(area_labels_set)
            mask_npy = np.zeros((int(self.image_height_orig), int(self.image_width_orig), number_of_classes))
            for i in range(0, len(points)):
                points_ready = []
                for j in range(0, len(points[i])):
                    points_ready.append([min([int(points[i][j].x() * image_scaled_ratio), int(self.image_width_orig) - 1]),
                                         min([int(points[i][j].y() * image_scaled_ratio), int(self.image_height_orig) - 1])])
                points_ready = np.array(points_ready)
                point_specific_label = area_labels[i]
                index = area_labels_set.index(point_specific_label)
                mask_temp = mask_npy[:, :, index]
                cv2.fillPoly(mask_temp, [points_ready], (1))
                #plt.imshow(mask_temp)
                #plt.show()
                mask_npy[:, :, index] = mask_temp
            for i in range(0, len(area_labels_set)):
                label_mask = mask_npy[:, :, i]
                label_specific_save_dir = save_file_as_vis_dir.replace("." + save_file_as_vis_dir.split(".")[-1], "_" + area_labels_set[i] + "." + save_file_as_vis_dir.split(".")[-1])
                plt.imsave(label_specific_save_dir, self.image_mask_overlay(self.orig_image, label_mask), vmin=0.0, vmax=255.0)
        else:
            pass

    # Remove Markings ########################################################
    def remove_selected(self):
        if self.seg_label_list_table.rowCount() == 0:
            pass
        else:
            checked_list = []
            for i in range(0, self.seg_label_list_table.rowCount()):
                if self.seg_label_list_table.cellWidget(i, 0).isChecked():
                    checked_list.append(True)
                else:
                    checked_list.append(False)
            self.old_image_pixmap.clear_selected_markings(checked_list)

    # Visualization ##########################################################
    def image_mask_overlay(self, image_orig, mask):
        print(np.max(image_orig), np.min(image_orig))
        image_orig[:, :, 0][mask!=0] = 240
        return image_orig

    # Import Points ##########################################################
    def import_points_from_json(self):
        support_file_format = ["JSON", "json"]
        open_file = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;JSON (*.json;*.JSON);;")[0]
        if open_file[-4:] in support_file_format:
            with open(open_file) as json_points:
                data = json.load(json_points) # as dictionary
            self.import_points_json_window = import_points_window.ImportPointsWindow()
            self.import_points_json_window.fill_table(data)
            self.import_points_json_window.show()
        elif open_file == "":
            pass
        else:
            return
