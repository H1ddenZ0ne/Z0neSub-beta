#H1ddenZ0ne

import sys
import pytesseract
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from mss import mss
import numpy as np
import cv2
from googletrans import Translator
import threading
from queue import Queue
#H1ddenZ0ne


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#H1ddenZ0ne

class ResizableOverlay(QWidget):
    HANDLE_SIZE = 12
    def __init__(self, color, default_text, w=800, h=80, y_offset=100):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  
        screen = QApplication.primaryScreen().availableGeometry()
        x, y = (screen.width() - w)//2, screen.height() - h - y_offset
        self.setGeometry(x, y, w, h)

        self.rect = QRect(0, 0, w, h)
        self.dragging = False
        self.resizing = False
        self.resizing_handle = None
        self.drag_start = QPoint()
        self.rect_start = QRect()


        self.label = QLabel(default_text, self)
        font = QFont('Tahoma', 16)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setStyleSheet(f"color: white; background-color: rgba(0,0,0,30); padding: 4px;")
        self.label.setWordWrap(True)
        self.label.resize(self.rect.width(), self.rect.height())
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  
        self.color = color
        self.show()

        self.handles = []
        for corner in [self.rect.topLeft(), self.rect.topRight(), self.rect.bottomLeft(), self.rect.bottomRight()]:
            handle = QWidget(self)
            handle.setGeometry(corner.x()-self.HANDLE_SIZE//2, corner.y()-self.HANDLE_SIZE//2,
                               self.HANDLE_SIZE, self.HANDLE_SIZE)
            handle.setStyleSheet("background-color: rgba(255,0,0,120);")
            handle.setAttribute(Qt.WA_TransparentForMouseEvents, False)  
            self.handles.append(handle)


    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(self.color), 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect)

    def mousePressEvent(self, event):
        pos = event.pos()
        for i, handle in enumerate(self.handles):
            if handle.geometry().contains(pos):
                self.resizing = True
                self.resizing_handle = i
                self.drag_start = pos
                self.rect_start = QRect(self.rect)
                return


        if self.rect.contains(pos):
            self.dragging = True
            self.drag_start = event.globalPos()
            self.rect_start = QRect(self.rect)
#H1ddenZ0ne

    def mouseMoveEvent(self, event):
        if self.resizing:
            pos = event.pos()
            dx = pos.x() - self.drag_start.x()
            dy = pos.y() - self.drag_start.y()
            r = QRect(self.rect_start)
            if self.resizing_handle == 0:
                r.setTopLeft(r.topLeft() + QPoint(dx, dy))
            elif self.resizing_handle == 1:
                r.setTopRight(r.topRight() + QPoint(dx, dy))
            elif self.resizing_handle == 2:
                r.setBottomLeft(r.bottomLeft() + QPoint(dx, dy))
            elif self.resizing_handle == 3:
                r.setBottomRight(r.bottomRight() + QPoint(dx, dy))
            self.rect = r.normalized()
            self.label.resize(self.rect.width(), self.rect.height())
#H1ddenZ0ne

            self.update_handles()
            self.update()
        elif self.dragging:
            diff = event.globalPos() - self.drag_start
            self.move(self.pos() + diff)
            self.drag_start = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.resizing_handle = None

    def update_handles(self):
        corners = [self.rect.topLeft(), self.rect.topRight(), self.rect.bottomLeft(), self.rect.bottomRight()]
        for handle, corner in zip(self.handles, corners):
            handle.setGeometry(corner.x()-self.HANDLE_SIZE//2, corner.y()-self.HANDLE_SIZE//2,
                               self.HANDLE_SIZE, self.HANDLE_SIZE)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ورود به H1ddenZ0ne")
        self.setGeometry(600, 300, 400, 150)
        layout = QVBoxLayout()

        self.label = QLabel("رمز را وارد کنید:", self)
        layout.addWidget(self.label)

        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_btn = QPushButton("ورود", self)
        self.login_btn.clicked.connect(self.check_password)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)
        self.show()

    def check_password(self):
        if self.password_input.text() == "H1ddenZ0ne":
            self.close()
            self.start_translator_app()
        else:
            QMessageBox.warning(self, "خطا", "رمز اشتباه است!")

    def start_translator_app(self):
        self.translator_app = TranslatorApp()


class TranslatorApp:
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)

        self.red_frame = ResizableOverlay("red", "متن انگلیسی", w=800, h=150, y_offset=200)
        self.green_frame = ResizableOverlay("green", "ترجمه فارسی", w=800, h=150, y_offset=50)


        self.start_btn = QPushButton("شروع ترجمه")
        self.start_btn.setFixedSize(200,50)
        self.start_btn.move(50,50)
        self.start_btn.show()
        self.start_btn.clicked.connect(self.start_translation)


        self.translator = Translator()
        self.sct = mss()
        self.last_text = ""
        self.queue = Queue()
        self.timer = QTimer()
        self.translate_thread = threading.Thread(target=self.process_queue, daemon=True)

    def start_translation(self):
        self.start_btn.hide()

        self.red_frame.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.green_frame.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.timer.timeout.connect(self.capture_text)
        self.timer.start(300)
        self.translate_thread.start()
#H1ddenZ0ne
    def capture_text(self):
        try:
            monitor = {
                "top": self.red_frame.y() + self.red_frame.rect.y(),
                "left": self.red_frame.x() + self.red_frame.rect.x(),
                "width": self.red_frame.rect.width(),
                "height": self.red_frame.rect.height()
            }
            screenshot = self.sct.grab(monitor)
            img = np.array(screenshot)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            text = pytesseract.image_to_string(gray, lang='eng').strip()
            if text and text != self.last_text:
                self.last_text = text
                self.queue.put(text)
        except Exception as e:
            print("Error:", e)

    def process_queue(self):
        while True:
            text = self.queue.get()
            try:
                translated_text = self.translator.translate(text, src='en', dest='fa').text
                self.green_frame.label.setText(translated_text)
            except Exception as e:
                print("Translation Error:", e)
            self.queue.task_done()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    sys.exit(app.exec_())

