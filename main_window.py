import copy
import cv2
import json
import numpy as np
import matplotlib.pyplot as plt
from cellpose import models
from PIL import Image, ImageQt
from PyQt5.QtCore import QEvent, QSize, Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QWidget, QFileDialog, QLabel, QGroupBox, QStatusBar, QTableWidget, QTableWidgetItem, QCheckBox, QLineEdit, QMenuBar, QMenu, QAction

# Custom modules
import main_display
import import_points_window
import export_option_window


class MainWindow(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        # Basic software information
        self.VERSION = "1.3"
        self.RELEASE_DATE = "18-Jul-2024"
        self.COMPOSER = "NGPF"

        self.orig_image = None
        self.orig_image_dir = None
        self.new_image = None
        self.new_image_dir = None

        self.setWindowTitle(f"AlphaSEG - V.{self.VERSION}")
        self.setFixedSize(QSize(1300, 1000))

        self.pixmap_display_size = (650, 650)

        # Menu Bar
        self.menu_bar = QMenuBar(self)
        self.file_menu = QMenu("&File", self)
        self.automation_menu = QMenu("&Automation", self)
        self.edit_menu = QMenu("&Edit", self)
        self.help_menu = QMenu("&Help", self)
        self.menu_bar.addMenu(self.file_menu)
        self.menu_bar.addMenu(self.automation_menu)
        self.menu_bar.addMenu(self.edit_menu)
        self.menu_bar.addMenu(self.help_menu)
        self.setMenuBar(self.menu_bar)
        self.open_action = QAction("&Open", self)
        self.open_action.triggered.connect(self.browse_image)
        self.file_menu.addAction(self.open_action)

        # Export
        self.export_function = QAction("Export")
        self.export_function.triggered.connect(self.export_with_option)
        self.file_menu.addAction(self.export_function)

        # Import
        self.import_action = QAction("&Import", self)
        self.import_action.triggered.connect(self.import_points_from_json)
        self.file_menu.addAction(self.import_action)

        # Automation - Cellpose
        self.cellpose_mask_function = QAction("&Cellpose", self)
        self.cellpose_mask_function.triggered.connect(self.generate_mask_with_cellpose)
        self.automation_menu.addAction(self.cellpose_mask_function)

        # Preference
        self.pref_action = QAction("&Preferences", self)
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
        tool_group_v_layout = QVBoxLayout()
        tool_group_v_layout.setAlignment(Qt.AlignTop)
        tool_group_h_layout = QHBoxLayout()
        tool_group_h_layout.setAlignment(Qt.AlignTop)
        tool_group_h_layout_2 = QHBoxLayout()
        tool_group_h_layout_2.setAlignment(Qt.AlignTop)
        # Free drawing (segmentation)
        self.draw_polygon_button = QPushButton("Create Mask")
        self.draw_polygon_button.setCheckable(True)
        self.draw_polygon_button.clicked.connect(self.enable_drawing)
        # Bounding box (object detection)
        self.draw_b_box_button = QPushButton("Create Bounding Box")
        self.draw_b_box_button.setCheckable(True)
        self.draw_b_box_button.clicked.connect(self.enable_bounding_box_drawing)
        tool_group_h_layout.addWidget(self.draw_polygon_button)
        tool_group_h_layout.addWidget(self.draw_b_box_button)
        # Zoom function
        self.magnify_zoom_button = QPushButton("Zoom In")
        self.magnify_zoom_button.setCheckable(True)
        self.magnify_zoom_button.clicked.connect(self.enable_zoom)
        # Zoom to origin function
        self.origin_zoom_button = QPushButton("Zoom to Origin")
        self.origin_zoom_button.setCheckable(False)
        self.origin_zoom_button.clicked.connect(self.zoom_to_origin)
        tool_group_h_layout_2.addWidget(self.magnify_zoom_button)
        tool_group_h_layout_2.addWidget(self.origin_zoom_button)
        tool_group_v_layout.addLayout(tool_group_h_layout)
        tool_group_v_layout.addLayout(tool_group_h_layout_2)
        tool_group.setLayout(tool_group_v_layout)

        left_image_v_layout.addWidget(image_info_group)
        left_image_v_layout.addWidget(view_group)
        left_image_v_layout.addWidget(tool_group)

        # Mask and label
        seg_label_list_group = QGroupBox("Mask and Label")
        seg_label_list_group.setMaximumWidth(400)
        seg_label_list_v_layout = QVBoxLayout()

        self.seg_label_list_table = QTableWidget()
        self.seg_label_list_table.setColumnCount(4)
        self.seg_label_list_table.setHorizontalHeaderLabels(["Select", "Show", "Type", "Label"])
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
            self.draw_b_box_button.setEnabled(False)
        else:
            self.old_image_pixmap.draw_lines = False
            self.draw_b_box_button.setEnabled(True)

    def enable_bounding_box_drawing(self):
        if self.draw_b_box_button.isChecked():
            self.old_image_pixmap.draw_b_box = True
            self.draw_polygon_button.setEnabled(False)
        else:
            self.old_image_pixmap.draw_b_box = False
            self.draw_polygon_button.setEnabled(True)

    def enable_zoom(self):
        if self.magnify_zoom_button.isChecked():
            self.old_image_pixmap.zoom = True
        #else:
        #    self.old_image_pixmap.zoom = False

    def zoom_to_origin(self):
        self.old_image_pixmap.replace_canvas_origin()
        self.old_image_pixmap.zoom = False

    def set_pixmap_from_array(self, image_arr):
        image_arr = image_arr[:, :, 0:3].astype('uint8')
        print(image_arr.shape)
        plt.imshow(image_arr)
        plt.show()
        qimage = QImage(image_arr, image_arr.shape[1], image_arr.shape[0], 3 * image_arr.shape[1], QImage.Format_RGB888)
        self.image_width_orig = image_arr.shape[1]
        self.image_height_orig = image_arr.shape[0]
        self.qpixmap = QPixmap.fromImage(qimage)
        self.qpixmap = self.qpixmap.scaled(self.pixmap_display_size[0], self.pixmap_display_size[1], Qt.KeepAspectRatio)
        self.qpixmap_orig = self.qpixmap.copy()
        self.image_width_scaled = self.qpixmap_orig.rect().width()
        self.image_height_scaled = self.qpixmap_orig.rect().height()
        self.old_image_pixmap.canvas_orig = self.qpixmap_orig
        self.old_image_pixmap.initiate_canvas_and_set_pixmap(self.qpixmap)
        self.old_image_pixmap.canvas_display_size = self.pixmap_display_size
        self.old_image_pixmap.canvas_orig_size = (self.image_width_orig, self.image_height_orig)
        self.old_image_pixmap.canvas_array = image_arr
        self.old_image_pixmap.canvas_scaling = self.image_width_orig / self.image_width_scaled
        self.old_image_pixmap.zoom_corner1 = QPoint(0, 0)
        self.old_image_pixmap.zoom_corner2 = QPoint(image_arr.shape[1], image_arr.shape[0])

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
        self.marking_info = self.old_image_pixmap.marking_info
        self.seg_label_list_table.clearContents()
        self.seg_label_list_table.setRowCount(0)

        for i in range(0, len(self.marking_info)):
            self.seg_label_list_table.insertRow(self.seg_label_list_table.rowCount())

            # Check box for selection
            table_select_check_box = QCheckBox()
            table_select_check_box.setChecked(False)
            # Check box for visualization option
            table_show_check_box = QCheckBox()
            table_show_check_box.setCheckState(self.marking_info[i][-1])
            table_show_check_box.clicked.connect(self.refresh_pixmap_with_visualization_option)
            # Labels for marking type (Contour/Bounding box)
            table_area_type_text = QLabel()  # Set as label because the user cannot change the type of the marking
            table_area_type_text.setText(str(self.marking_info[i][0]))
            # Labels for marked areas
            table_area_label_text = QLineEdit()  # Set as line edit because the label can be changed
            table_area_label_text.setText(str(self.marking_info[i][1]))
            table_area_label_text.textChanged.connect(self.refresh_area_labels)

            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 0, table_select_check_box)
            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 1, table_show_check_box)
            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 2, table_area_type_text)
            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 3, table_area_label_text)

    def refresh_pixmap_with_visualization_option(self):
        if self.seg_label_list_table.rowCount() == 0:
            pass
        else:
            for i in range(0, len(self.marking_info)):
                if self.seg_label_list_table.cellWidget(i, 1).checkState() == Qt.Checked:
                    self.marking_info[i][-1] = True
                    self.marking_info[i][3] = False
                elif self.seg_label_list_table.cellWidget(i, 1).checkState() == Qt.PartiallyChecked:
                    self.marking_info[i][-1] = True
                    self.marking_info[i][3] = True
                else:
                    self.marking_info[i][-1] = False
            self.old_image_pixmap.marking_info = self.marking_info
            self.old_image_pixmap.refresh_pixmap_acc_to_vis()

    def refresh_area_labels(self):
        if self.seg_label_list_table.rowCount() == 0:
            pass
        else:
            for i in range(0, self.marking_info):
                self.marking_info[i][1] = self.seg_label_list_table.cellWidget(i, 3).text()

    def reset_pixmap(self):
        self.old_image_pixmap.setPixmap(self.qpixmap_orig)
        self.old_image_pixmap.update()

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

    # Export Option ##########################################################
    def export_with_option(self):
        self.export_option_window = export_option_window.ExportOptionWindow(self.marking_info, (self.image_width_orig, self.image_height_orig), (self.image_width_scaled, self.image_height_scaled))
        self.export_option_window.show()

    ##########################################################################
    # Automation #############################################################
    ##########################################################################
    def generate_mask_with_cellpose(self):
        self._generate_mask_with_cellpose(image_arr=self.old_image_pixmap.canvas_array)

    def _generate_mask_with_cellpose(self, image_arr, model_type='cyto3', use_gpu=False):
        model = models.Cellpose(gpu=use_gpu, model_type=model_type)
        masks, _, _, _ = model.eval(image_arr, diameter=None, channels=[0, 0], flow_threshold=0.4, do_3D=False)
        num_masks = len(np.unique(masks))
        for i in range(1, num_masks):  # No need to consider "0" label
            mask_temp = np.zeros(masks.shape, dtype=np.uint8)
            mask_temp[masks == i] = 1
            try:
                contours = cv2.findContours(mask_temp, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
                coord = contours[0][0]
                coord_qpoint = []
                for j in range(0, coord.shape[0]):
                    coord_qpoint.append(QPoint(coord[j, :, 0][0], coord[j, :, 1][0]))
                self.old_image_pixmap.marking_info.append(["Contour", "NO LABEL", coord_qpoint, True, True])
            except:
                print("Mask failure")
        self.refresh_seg_label_list_table()
        self.old_image_pixmap.refresh_pixmap_acc_to_vis()
