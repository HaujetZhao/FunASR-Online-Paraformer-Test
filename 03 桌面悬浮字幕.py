import sys, os
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtNetwork import QUdpSocket
from rich import inspect


# 窗体属性参考：https://doc.qt.io/qt-6/qt.html#WindowType-enum
# 控件属性参考：https://doc.qt.io/qt-6/qt.html#WidgetAttribute-enum
# 样式表参考：https://doc.qt.io/qt-5/stylesheet-syntax.html
#            https://doc.qt.io/qt-5/stylesheet-reference.html

# 通过 udp 端口接收文字，并更新显示
udp_port = 6009

class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen) #   
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(self.get_style())
        

        # 设置窗口大小和位置
        self.setGeometry(400, 400, 400, 100)

        # 创建主窗口的 central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # 创建垂直布局
        layout = QVBoxLayout(central_widget)

        # 创建标签
        self.label = QLabel(f'端口：{udp_port}    外观：style.css', self)

        # 将标签添加到布局中
        layout.addWidget(self.label)

        # 添加系统托盘
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("assets/icon.ico"))  # 托盘图标路径
        self.tray_icon.setVisible(True) 
        self.tray_icon.setToolTip("悬浮窗口")
        self.tray_icon.activated.connect(self.tray_trigger)

        # 绑定 udp 端口
        self.udp_socket = QUdpSocket(self)
        self.udp_socket.bind(udp_port)
        self.udp_socket.readyRead.connect(self.receive_data)

        # 创建右键菜单
        self.create_context_menu()

    def change_port(self):
        self.udp_socket.close()
        self.udp_socket.bind(udp_port) 

    def receive_data(self):
        while self.udp_socket.hasPendingDatagrams():
            size = self.udp_socket.pendingDatagramSize()
            data, host, port = self.udp_socket.readDatagram(size)

            # 将接收到的数据转换为字符串并更新标签内容
            try:
                message = data.decode("utf-8")
                if message:
                    self.label.setText(f"{message}")
            except Exception as e:
                print(e)

    def create_context_menu(self):
        self.menu = QMenu(self)
        switch_transparency_action = QAction("更新外观", self)
        switch_transparency_action.triggered.connect(self.update_style)
        self.menu.addAction(switch_transparency_action)

        self.hide_show_action = QAction("隐藏", self)
        self.hide_show_action.triggered.connect(self.hide_show)
        self.menu.addAction(self.hide_show_action)

        self.lock_unlock_action = QAction("锁定", self)
        self.lock_unlock_action.triggered.connect(self.lock_unlock)
        self.menu.addAction(self.lock_unlock_action)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        self.menu.addAction(quit_action)

        self.tray_icon.setContextMenu(self.menu)

    def update_style(self):
        self.setStyleSheet(self.get_style())    # 更新 style
        self.resize(self.label.sizeHint())      # 更新窗体大小
        self.update()
    
    def get_style(self):
        style = "QLabel { color: green; background-color: rgba(0, 0, 0, 0%); }"
        style_path = Path('style.css')
        if style_path.exists:
            with open (style_path, 'r', encoding='utf-8') as f: style = f.read()
        else:
            with open (style_path, 'w', encoding='utf-8') as f: f.write(style)
        return style

    def quit_application(self):
        self.tray_icon.hide()
        QApplication.quit()

    def tray_trigger(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            # 单击系统托盘图标时显示或隐藏窗口
            self.hide_show()
                
    def hide_show(self):
        if self.isVisible():
            self.hide_show_action.setText('显示')
            self.hide()
        else:
            self.hide_show_action.setText('隐藏')
            self.show()

    def lock_unlock(self, reason):
        lock_state = not (self.windowFlags() & Qt.WindowTransparentForInput)
        if lock_state: self.lock_unlock_action.setText('解锁')
        else: self.lock_unlock_action.setText('锁定')
        self.setWindowFlag(Qt.WindowTransparentForInput, lock_state)
        self.hide_show()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()

    sys.exit(app.exec_())
