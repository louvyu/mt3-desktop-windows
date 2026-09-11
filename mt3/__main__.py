import pathlib
import sys
import os
import math
import re

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import pyqtSignal, QThread, Qt, QPoint, QSize, QTimer, QSettings, QObject, QRectF
from PyQt6.QtWidgets import (
    QApplication, QDialog, QPushButton, QHBoxLayout, QMessageBox, QFileDialog, QWidget, QLabel, QMainWindow,
    QVBoxLayout, QLineEdit, QTextEdit, QFrame, QProgressBar
)


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'mt3', relative_path)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


class StartupLoader(QThread):
    finished_loading = pyqtSignal()

    def run(self):
        import mt3.inference
        self.finished_loading.emit()


class DeviceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 220)
        self.choice = "CPU"

        self.setStyleSheet("""
            QLabel { color: rgba(112, 90, 74, 0.9); font-family: 'Segoe UI', 'PingFang SC', sans-serif; }
            QPushButton { 
                background-color: rgba(255, 255, 255, 0.6); 
                border: 1px solid rgba(255, 255, 255, 0.9); 
                border-radius: 8px; font-size: 14px; padding: 10px; 
                color: rgba(112, 90, 74, 0.95); font-weight: 600; 
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.9); }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("首次运行设置", self)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            "请选择核心计算模式：\n(如无 NVIDIA 高端显卡，请务必选择 CPU 模式。)\n首次使用GPU模式需要等待30分钟编译驱动才能开始转换",
            self)
        desc.setStyleSheet("font-size: 13px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addStretch(1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.btn_cpu = QPushButton("CPU", self)
        self.btn_cpu.clicked.connect(lambda: self.make_choice("CPU"))

        self.btn_gpu = QPushButton("GPU", self)
        self.btn_gpu.clicked.connect(lambda: self.make_choice("GPU"))

        btn_layout.addWidget(self.btn_cpu)
        btn_layout.addWidget(self.btn_gpu)
        layout.addLayout(btn_layout)

    def make_choice(self, mode):
        self.choice = mode
        self.accept()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        grad = QtGui.QLinearGradient(self.width(), self.height(), 0, 0)
        grad.setColorAt(0.0, QtGui.QColor(255, 245, 235, 200))
        grad.setColorAt(1.0, QtGui.QColor(255, 255, 255, 180))
        painter.setBrush(QtGui.QBrush(grad))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 240), 1.5))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 10, 10)


class JellySplashSpinner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(200, 120)
        self.phase = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)

    def update_animation(self):
        self.phase += 0.15
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2 + 10
        ball_radius = 12
        spacing = 35

        for i in range(3):
            y_offset = math.sin(self.phase + i * (math.pi * 2 / 3)) * 18
            x = center_x - spacing + (i * spacing)
            y = center_y + y_offset

            shadow_scale = 1.0 - (abs(y_offset) / 30.0)
            shadow_alpha = int(35 * shadow_scale)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QtGui.QColor(180, 80, 20, shadow_alpha))
            painter.drawEllipse(int(x - ball_radius * 0.8 - 3), int(center_y + 25 - 3), int(ball_radius * 1.6),
                                int(ball_radius * 0.6))

            draw_r = ball_radius * 1.25
            grad = QtGui.QRadialGradient(x, y, draw_r)
            grad.setColorAt(0.0, QtGui.QColor(228, 158, 142, 255))
            grad.setColorAt(0.5, QtGui.QColor(228, 158, 142, 240))
            grad.setColorAt(0.85, QtGui.QColor(230, 165, 150, 160))
            grad.setColorAt(1.0, QtGui.QColor(230, 165, 150, 0))

            painter.setBrush(QtGui.QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(x - draw_r), int(y - draw_r), int(draw_r * 2), int(draw_r * 2))



def create_liquid_icon(icon_type, scale=1.0):
    size = int(70 * scale)
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)


    painter.scale(scale, scale)

    base_color = QtGui.QColor("#e6caac")

    glass_grad = QtGui.QLinearGradient(65, 65, 5, 5)
    glass_grad.setColorAt(0.0, QtGui.QColor(250, 240, 230, 160))
    glass_grad.setColorAt(1.0, QtGui.QColor(255, 255, 255, 20))

    glass_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 200), 1.5)

    if icon_type == "plus":
        glass_path = QtGui.QPainterPath()
        glass_path.addRoundedRect(5, 5, 60, 60, 16, 16)
        painter.setBrush(QtGui.QBrush(glass_grad))
        painter.setPen(glass_pen)
        painter.drawPath(glass_path)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(base_color))
        path = QtGui.QPainterPath()
        path.addRoundedRect(31, 11, 8, 48, 3, 3)
        path.addRoundedRect(11, 31, 48, 8, 3, 3)
        painter.drawPath(path)

    else:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(base_color))

        if icon_type == "folder":
            path = QtGui.QPainterPath()
            path.addRoundedRect(10, 10, 50, 45, 6, 6)
            path.addRoundedRect(10, 5, 22, 15, 4, 4)
            painter.drawPath(path)
        elif icon_type == "play":
            path = QtGui.QPainterPath()
            path.moveTo(18, 12)
            path.lineTo(18, 58)
            path.lineTo(60, 35)
            path.closeSubpath()
            painter.drawPath(path)

        glass_path = QtGui.QPainterPath()
        if icon_type == "folder":
            glass_path.addRoundedRect(5, 28, 60, 35, 8, 8)
        elif icon_type == "play":
            glass_path.addRoundedRect(5, 5, 30, 60, 8, 8)

        painter.setBrush(QtGui.QBrush(glass_grad))
        painter.setPen(glass_pen)
        painter.drawPath(glass_path)

    painter.end()
    return QtGui.QIcon(pixmap)


def create_gear_icon():
    pixmap = QtGui.QPixmap(36, 28)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

    painter.translate(18, 14)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QtGui.QColor(112, 90, 74, 210))

    for i in range(8):
        painter.drawRoundedRect(QRectF(-1.5, -7.0, 3.0, 4.0), 1.0, 1.0)
        painter.rotate(45)

    path = QtGui.QPainterPath()
    path.addEllipse(QRectF(-5.5, -5.5, 11.0, 11.0))
    path.addEllipse(QRectF(-2.0, -2.0, 4.0, 4.0))
    path.setFillRule(Qt.FillRule.OddEvenFill)

    painter.drawPath(path)
    painter.end()
    return QtGui.QIcon(pixmap)


class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(38)
        self.start_pos = None
        self.setAutoFillBackground(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)

        settings = QSettings("MT3_Audio", "Converter")
        mode = settings.value("device_mode", "CPU")
        mode_tag = "GPU 加速" if mode == "GPU" else "CPU 模式"

        self.title_label = QLabel(f" MT3 Audio Converter  |  [{mode_tag}]", self)
        self.title_label.setStyleSheet("""
            color: rgba(112, 90, 74, 0.9); 
            font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            font-size: 13px; 
            font-weight: 600; 
            letter-spacing: 1.5px;
        """)
        layout.addWidget(self.title_label)
        layout.addStretch(1)

        self.btn_setting = QPushButton("", self)
        self.btn_setting.setIcon(create_gear_icon())
        self.btn_setting.setIconSize(QSize(36, 28))
        self.btn_setting.setFixedSize(36, 28)
        self.btn_setting.setToolTip("切换 CPU / GPU 模式")
        self.btn_setting.clicked.connect(self.parent.open_settings)

        self.btn_min = QPushButton("—", self)
        self.btn_min.setFixedSize(36, 28)
        self.btn_min.clicked.connect(self.parent.showMinimized)

        self.btn_close = QPushButton("✕", self)
        self.btn_close.setFixedSize(36, 28)
        self.btn_close.clicked.connect(self.parent.close)

        btn_style = """
            QPushButton { 
                background: transparent; 
                border: none; 
                color: rgba(112, 90, 74, 0.8); 
                font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
                font-size: 14px; 
                font-weight: 600; 
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.4); border-radius: 6px; color: rgba(112, 90, 74, 1.0); }
        """
        self.btn_setting.setStyleSheet(btn_style)
        self.btn_min.setStyleSheet(btn_style)
        self.btn_close.setStyleSheet(btn_style)

        layout.addWidget(self.btn_setting)
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_close)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2

        grad = QtGui.QRadialGradient(center_x, center_y, self.width() * 0.6)
        grad.setColorAt(0.0, QtGui.QColor(230, 170, 145, 240))
        grad.setColorAt(0.5, QtGui.QColor(235, 185, 165, 200))
        grad.setColorAt(1.0, QtGui.QColor(245, 210, 195, 160))

        path = QtGui.QPainterPath()
        path.addRoundedRect(1, 1, self.width() - 2, self.height() + 10, 9, 9)

        painter.setBrush(QtGui.QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

        grain_brush_light = QtGui.QBrush(QtGui.QColor(255, 255, 255, 80), Qt.BrushStyle.Dense5Pattern)
        painter.setBrush(grain_brush_light)
        painter.drawPath(path)

        grain_brush_dark = QtGui.QBrush(QtGui.QColor(0, 0, 0, 15), Qt.BrushStyle.Dense6Pattern)
        painter.setBrush(grain_brush_dark)
        painter.drawPath(path)

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 120), 1))
        painter.drawLine(1, self.height() - 1, self.width() - 1, self.height() - 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.start_pos is not None:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent.move(self.parent.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = None


class WaitDialog(QDialog):
    stop_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 320)

        self.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: 6px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(230, 170, 145, 0.9), 
                    stop:1 rgba(245, 210, 195, 0.9));
                border-radius: 5px;
            }
            QTextEdit { 
                background-color: rgba(255, 255, 255, 0.5); 
                border: 1px solid rgba(255, 255, 255, 0.9); 
                border-radius: 8px; 
                padding: 12px; 
                color: rgba(112, 90, 74, 0.9); 
                font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
                font-size: 13px; 
                font-weight: 500;
            }
            QPushButton { 
                background-color: rgba(255, 255, 255, 0.6); 
                border: 1px solid rgba(255, 255, 255, 0.9); 
                border-radius: 6px; 
                font-size: 14px; 
                padding: 8px 0; 
                color: rgba(112, 90, 74, 0.95); 
                font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
                font-weight: 600; 
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.9); }
            QPushButton:disabled { color: rgba(112, 90, 74, 0.4); }
        """)

        self.is_stopping = False
        self.can_close = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.button_stop = QPushButton('停止', self)
        self.button_stop.setFixedWidth(120)
        layout.addWidget(self.button_stop, alignment=Qt.AlignmentFlag.AlignCenter)
        self.button_stop.clicked.connect(self.stopProc)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        grad = QtGui.QLinearGradient(self.width(), self.height(), 0, 0)
        grad.setColorAt(0.0, QtGui.QColor(255, 245, 235, 200))
        grad.setColorAt(1.0, QtGui.QColor(255, 255, 255, 180))

        painter.setBrush(QtGui.QBrush(grad))
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 240), 1.5))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 10, 10)

    def stopProc(self):
        if not self.is_stopping:
            self.is_stopping = True
            self.button_stop.setText("正在停止...")
            self.button_stop.setEnabled(False)
            self.stop_clicked.emit()

    def accept(self):
        self.can_close = True
        super().accept()

    def reject(self):
        if self.can_close:
            super().reject()
        else:
            self.stopProc()

    def closeEvent(self, event):
        if self.can_close:
            event.accept()
        else:
            event.ignore()
            self.stopProc()


class DummyScrollBar:
    def setValue(self, val): pass

    def maximum(self): return 1000

    def minimum(self): return 0

    def value(self): return 1000


class LogProxy(QObject):
    append_signal = pyqtSignal(str)
    insert_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, text_edit, progress_bar):
        super().__init__()
        self.append_signal.connect(text_edit.append)
        self.insert_signal.connect(text_edit.insertPlainText)
        self.progress_bar = progress_bar

        self.progress_signal.connect(self._set_target_progress)
        self._dummy_scroll = DummyScrollBar()

        self.target_progress = 0
        self.current_progress = 0
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._animate_progress)
        self.anim_timer.start(16)

    def _set_target_progress(self, val):
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 1000)
        self.target_progress = val

    def _animate_progress(self):
        if self.current_progress != self.target_progress:
            diff = self.target_progress - self.current_progress
            step = int(diff * 0.05)
            if step == 0:
                step = 1 if diff > 0 else -1
            self.current_progress += step
            if (diff > 0 and self.current_progress > self.target_progress) or \
                    (diff < 0 and self.current_progress < self.target_progress):
                self.current_progress = self.target_progress
            self.progress_bar.setValue(self.current_progress)

    def write(self, text):
        text_str = str(text).strip()
        if not text_str:
            return
        self.append_signal.emit(text_str)
        self._check_progress(text_str)

    def insertPlainText(self, text):
        text_str = str(text)
        self.insert_signal.emit(text_str)
        self._check_progress(text_str)

    def _check_progress(self, text_str):
        match_step = re.search(r'(\d+)\s*/\s*(\d+)', text_str)
        if match_step:
            cur = float(match_step.group(1))
            tot = float(match_step.group(2))
            if tot > 0 and cur <= tot:
                val = (cur / tot) * 1000
                self.progress_signal.emit(int(val))
                return

        match_pct = re.search(r'(\d+\.?\d*)%', text_str)
        if match_pct:
            val = float(match_pct.group(1))
            self.progress_signal.emit(int(val * 10))

    def verticalScrollBar(self):
        return self._dummy_scroll

    def moveCursor(self, *args, **kwargs):
        pass

    def ensureCursorVisible(self, *args, **kwargs):
        pass

    def flush(self):
        pass

    def append(self, t):
        self.write(t)

    def setText(self, t):
        self.write(t)


class WorkerThread(QThread):
    finished_signal = pyqtSignal()
    result_signal = pyqtSignal(str)
    stopSignal = pyqtSignal()

    def __init__(self, file_path, folder_path, text_edit, progress_bar):
        super().__init__()
        self.file_path = file_path
        self.folder_path = folder_path
        self.proxy = LogProxy(text_edit, progress_bar)

        resource_path = get_resource_path('pretrained')
        from mt3.inference import InferenceHandler
        self.handler = InferenceHandler(resource_path)
        self.stopSignal.connect(self.handler.stopProc)

    def run(self):
        try:
            self.proxy.append("正在初始化核心引擎...")
            try:
                import tensorflow as tf
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    self.proxy.append("硬件就绪：已成功挂载 NVIDIA GPU 进行转换计算！")
                else:
                    self.proxy.append("显卡未响应或您选择了 CPU 模式，当前正在使用纯 CPU 进行计算...")
            except Exception:
                pass

            filename = os.path.basename(self.file_path).split('.')[0]
            outpath = os.path.join(self.folder_path, f'{filename}.mid')

            fin = self.handler.inference(self.file_path, outpath, text_edit=self.proxy)

            if fin != False:
                self.result_signal.emit('转换完成: \n' + outpath)
            else:
                self.result_signal.emit('转换已终止')
        except Exception as e:
            self.result_signal.emit(f'转换失败: \n{str(e)}')
        finally:
            self.finished_signal.emit()


class ClickDropZone(QFrame):
    fileSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("glassPanel")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(25)

        self.icon = QLabel()
        self.icon.setPixmap(create_liquid_icon("plus").pixmap(70, 70))

        self.label = QLabel("点击或拖拽导入音频", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label.setStyleSheet("""
            color: #968576; 
            font-family: '-apple-system', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            font-size: 16px; 
            font-weight: 500; 
            border: none; 
            background: transparent;
            letter-spacing: 2px;
        """)

        layout.addWidget(self.icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            self.set_file(filepath)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
            file_dialog.setDirectory(str(pathlib.Path.home()))
            file_names, _ = file_dialog.getOpenFileNames(self, '音频文件选择', '', 'All Files (*)')
            if file_names:
                self.set_file(file_names[0])

    def set_file(self, filepath):
        self.label.setText(f"{os.path.basename(filepath)}")
        self.fileSelected.emit(filepath)


class FileDialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.bg_pixmap = None
        self.initUI()

    def initUI(self):
        self.setFixedSize(900, 700)

        bg_path = get_resource_path('pretrained/bg.png')
        if os.path.exists(bg_path):
            raw_pixmap = QtGui.QPixmap(bg_path)
            self.bg_pixmap = raw_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                               Qt.TransformationMode.SmoothTransformation)

        glass_css = """
            QFrame#glassPanel, QPushButton {
                background: qlineargradient(x1:1, y1:1, x2:0, y2:0, 
                    stop:0 rgba(255, 245, 235, 0.30), 
                    stop:0.4 rgba(255, 255, 255, 0.12), 
                    stop:1 rgba(255, 255, 255, 0.02));
                border: 1.5px solid rgba(255, 255, 255, 140);
            }
            QFrame#glassPanel { border-radius: 20px; }
            QPushButton { border-radius: 26px; }

            QFrame#glassPanel:hover, QPushButton:hover {
                background: qlineargradient(x1:1, y1:1, x2:0, y2:0, 
                    stop:0 rgba(255, 245, 235, 0.45), 
                    stop:0.4 rgba(255, 255, 255, 0.20), 
                    stop:1 rgba(255, 255, 255, 0.05));
            }
            QPushButton:pressed {
                background: qlineargradient(x1:1, y1:1, x2:0, y2:0, 
                    stop:0 rgba(255, 245, 235, 0.15), 
                    stop:1 rgba(255, 255, 255, 0.02));
                border: 1.5px solid rgba(255, 255, 255, 80);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 50);
            }
        """
        self.setStyleSheet(glass_css)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        main_layout.addStretch(1)

        top_layout = QHBoxLayout()
        self.drop_zone = ClickDropZone(self)
        self.drop_zone.setFixedSize(760, 360)
        self.drop_zone.fileSelected.connect(self.on_file_selected)

        drop_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        drop_shadow.setBlurRadius(25)
        drop_shadow.setColor(QtGui.QColor(120, 90, 60, 45))
        drop_shadow.setOffset(-4, -4)
        self.drop_zone.setGraphicsEffect(drop_shadow)

        top_layout.addStretch(1)
        top_layout.addWidget(self.drop_zone, alignment=Qt.AlignmentFlag.AlignCenter)
        top_layout.addStretch(1)
        main_layout.addLayout(top_layout)

        main_layout.addSpacing(35)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(35)

        self.export_button = QPushButton(self)
        self.export_button.setFixedSize(110, 110)
        self.export_button.setIcon(create_liquid_icon("folder"))
        self.export_button.setIconSize(QSize(70, 70))
        self.export_button.setToolTip("设置输出目录")
        self.export_button.clicked.connect(self.showFolderDialog)

        export_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        export_shadow.setBlurRadius(20)
        export_shadow.setColor(QtGui.QColor(120, 90, 60, 40))
        export_shadow.setOffset(-3, -3)
        self.export_button.setGraphicsEffect(export_shadow)

        self.convert_button = QPushButton(self)
        self.convert_button.setFixedSize(160, 110)
        self.convert_button.setIcon(create_liquid_icon("play"))
        self.convert_button.setIconSize(QSize(70, 70))
        self.convert_button.setToolTip("开始转换")
        self.convert_button.clicked.connect(self.convert)

        convert_shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        convert_shadow.setBlurRadius(20)
        convert_shadow.setColor(QtGui.QColor(120, 90, 60, 40))
        convert_shadow.setOffset(-3, -3)
        self.convert_button.setGraphicsEffect(convert_shadow)

        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.export_button)
        bottom_layout.addWidget(self.convert_button)
        bottom_layout.addStretch(1)

        main_layout.addLayout(bottom_layout)
        main_layout.addStretch(1)

        self.selected_file_edit = QLineEdit(self)
        self.selected_file_edit.hide()
        self.selected_folder_edit = QLineEdit(self)
        self.selected_folder_edit.hide()


        settings = QSettings("MT3_Audio", "Converter")
        last_export_dir = settings.value("last_export_dir", "")
        if last_export_dir and os.path.exists(last_export_dir):
            self.selected_folder_edit.setText(last_export_dir)
            self.export_button.setToolTip(f"输出目录: {last_export_dir}")

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        path = QtGui.QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        painter.setClipPath(path)

        if self.bg_pixmap:
            x_offset = (self.width() - self.bg_pixmap.width()) // 2
            y_offset = (self.height() - self.bg_pixmap.height()) // 2
            painter.drawPixmap(x_offset, y_offset, self.bg_pixmap)
        else:
            painter.fillRect(self.rect(), QtGui.QColor("#F4F2F0"))

        painter.setClipping(False)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 120), 1))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 10, 10)

    def open_settings(self):
        dialog = DeviceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            settings = QSettings("MT3_Audio", "Converter")
            settings.setValue("device_mode", dialog.choice)
            QMessageBox.information(self, "设置已保存", "设置已更新，将在下次重启软件时生效。")

    def on_file_selected(self, filepath):
        self.selected_file_edit.setText(filepath)

    def showFolderDialog(self):
        current_dir = self.selected_folder_edit.text()
        if not current_dir or not os.path.exists(current_dir):
            current_dir = str(pathlib.Path.home())

        folder_path = QFileDialog.getExistingDirectory(self, '设置输出目录', current_dir)
        if folder_path:
            self.selected_folder_edit.setText(folder_path)
            self.export_button.setToolTip(f"输出目录: {folder_path}")

            settings = QSettings("MT3_Audio", "Converter")
            settings.setValue("last_export_dir", folder_path)

    def convert(self):
        filepath = self.selected_file_edit.text()
        folder_path = self.selected_folder_edit.text()

        if not filepath:
            QMessageBox.warning(self, "提示", "请先导入音频文件！")
            return

        if not folder_path:
            QMessageBox.warning(self, "提示", "请先设置输出目录！")
            return

        valid_exts = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma']
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in valid_exts:
            QMessageBox.warning(self, "格式错误", f"导入的音频不受支持！\n\n支持的文件类型: {', '.join(valid_exts)}")
            return

        self.convert_button.setEnabled(False)

        wait_dialog = WaitDialog(self)
        self.worker_thread = WorkerThread(filepath, folder_path, wait_dialog.text_edit, wait_dialog.progress_bar)

        wait_dialog.stop_clicked.connect(self.worker_thread.stopSignal.emit)

        self.conversion_result = ""

        def save_result(res):
            self.conversion_result = res

        self.worker_thread.result_signal.connect(save_result)

        self.worker_thread.finished_signal.connect(wait_dialog.accept)

        self.worker_thread.start()
        wait_dialog.setModal(True)
        wait_dialog.exec()

        self.convert_button.setEnabled(True)
        if self.conversion_result:
            QMessageBox.information(self, "转换结果", self.conversion_result)


fdialog = None


def main():
    import ctypes
    os.environ["PATH"] += os.pathsep + get_resource_path('pretrained')

    if os.name == 'nt':
        try:
            myappid = 'my_mt3_project.v12.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    resource_path = get_resource_path('pretrained')
    QApplication.setWindowIcon(QtGui.QIcon(resource_path + '/logo.png'))

    settings = QSettings("MT3_Audio", "Converter")
    device_mode = settings.value("device_mode", None)

    if device_mode is None:
        dialog = DeviceDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            device_mode = dialog.choice
            settings.setValue("device_mode", device_mode)
            QMessageBox.information(None, "设置已保存", "您的选择已保存。\n随时可点击右上角齿轮图标重新修改。")
        else:
            device_mode = "CPU"
            settings.setValue("device_mode", device_mode)

    if device_mode == "CPU":
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    else:

        os.environ['CUDA_VISIBLE_DEVICES'] = '0'

    splash = JellySplashSpinner()
    splash.show()
    app.processEvents()

    loader = StartupLoader()

    def on_loading_finished():
        global fdialog
        fdialog = FileDialog()
        fdialog.setWindowIcon(QtGui.QIcon(resource_path + '/logo.png'))
        splash.close()
        fdialog.show()

    loader.finished_loading.connect(on_loading_finished)
    loader.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()