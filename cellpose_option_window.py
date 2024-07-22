from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from cellpose import models
import numpy as np
import cv2

class CellposeOptionWindow(QMainWindow):
    cellpose_done_signal = pyqtSignal()

    def __init__(self, image_arr, marking_info):
        super(CellposeOptionWindow, self).__init__()
        self.setWindowTitle('Cellpose')
        self.build_gui()
        self.image_arr = image_arr
        self.marking_info = marking_info

    def build_gui(self):
        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)
        main_v_layout = QVBoxLayout()
        base_widget.setLayout(main_v_layout)

        model_type_h_layout = QHBoxLayout()
        self.model_type_text = QLabel("Model type")
        self.model_type_input = QLineEdit("cyto3")
        model_type_h_layout.addWidget(self.model_type_text)
        model_type_h_layout.addWidget(self.model_type_input)

        diameter_h_layout = QHBoxLayout()
        self.diameter_text = QLabel("Diameter")
        self.diameter_input = QLineEdit("160")
        diameter_h_layout.addWidget(self.diameter_text)
        diameter_h_layout.addWidget(self.diameter_input)

        flow_threshold_h_layout = QHBoxLayout()
        self.flow_threshold_text = QLabel("Flow threshold")
        self.flow_threshold_input = QLineEdit("0.4")
        flow_threshold_h_layout.addWidget(self.flow_threshold_text)
        flow_threshold_h_layout.addWidget(self.flow_threshold_input)

        self.do_3d_checkbox = QCheckBox("Perform 3D")
        self.do_3d_checkbox.setChecked(False)

        self.use_gpu_checkbox = QCheckBox("Use GPU")
        self.use_gpu_checkbox.setChecked(False)

        self.start_cellpose = QPushButton("Start Cellpose")
        self.start_cellpose.clicked.connect(self.generate_mask_with_cellpose)

        main_v_layout.addLayout(model_type_h_layout)
        main_v_layout.addLayout(diameter_h_layout)
        main_v_layout.addLayout(flow_threshold_h_layout)
        main_v_layout.addWidget(self.do_3d_checkbox)
        main_v_layout.addWidget(self.use_gpu_checkbox)
        main_v_layout.addWidget(self.start_cellpose)

    def generate_mask_with_cellpose(self):
        def is_float(string):
            try:
                float(string)
                return True
            except ValueError:
                return False
        image_arr = self.image_arr
        model_type = self.model_type_input.text()
        diameter = self.diameter_input.text()
        if is_float(diameter):
            diameter = float(diameter)
        else:
            diameter = None
        flow_threshold = self.flow_threshold_input.text()
        if is_float(flow_threshold):
            flow_threshold = float(flow_threshold)
        else:
            flow_threshold = 0.4;
        do_3D = self.do_3d_checkbox.isChecked()
        use_gpu = self.use_gpu_checkbox.isChecked()
        print(model_type, diameter, flow_threshold, do_3D, use_gpu)
        self._generate_mask_with_cellpose(image_arr, model_type, diameter, flow_threshold, do_3D, use_gpu)

    def _generate_mask_with_cellpose(self, image_arr, model_type, diameter, flow_threshold, do_3D, use_gpu):
        model = models.Cellpose(gpu=use_gpu, model_type=model_type)
        masks, _, _, _ = model.eval(image_arr, diameter=diameter, channels=[0, 0], flow_threshold=flow_threshold, do_3D=do_3D)
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
                self.marking_info.append(["Contour", "NO LABEL", coord_qpoint, True, True])
            except:
                print("Mask failure")
        self.cellpose_done_signal.emit()

# For testing only
if __name__ == '__main__':
    import sys
    import PyQt5
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    window = CellposeOptionWindow()
    window.show()
    sys.exit(app.exec_())

