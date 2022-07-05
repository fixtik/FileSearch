import os
import sys

from PySide6 import QtCore, QtWidgets, QtGui

from ui.search_form import Ui_MainWindow

class Form_backend(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.initUi()
        self.initThreads()

    def initUi(self):
        self.ui.stopSearchpushButton.setEnabled(False)
        self.ui.tableView.setModel(self.createQStandardItemModel()) # добавление заголовков таблицы
        self.ui.tableView.setVisible(False)

        # установка параметров для treeView
        model = QtWidgets.QFileSystemModel()
        model.setRootPath(QtCore.QDir.currentPath())
        self.ui.treeView.setModel(model)
        self.ui.treeView.clicked.connect(self.changeDir)


        # заполнение entringStringLabel и lineEdit
        self.changeText()

        #слоты
        self.ui.chooseSettingComboBox.currentTextChanged.connect(self.changeText)
        self.ui.startSearchpushButton.clicked.connect(self.startSearchButtonClick)
        self.ui.stopSearchpushButton.clicked.connect(self.stopSearchButtonClick)

    def changeText(self):
        """устанавливает текст entringStringLabel и lineEdit в зависимости от chooseSettingComboBox"""
        start_text = 'Введите данные для поиска '
        self.ui.entringStringLabel.setText(start_text+self.ui.chooseSettingComboBox.currentText())
        if str.find(self.ui.entringStringLabel.text(), 'расширению') != -1:
            self.ui.entringStringlineEdit.setPlaceholderText('*.*')
        elif str.find(self.ui.entringStringLabel.text(), 'сигнатурам') != -1:
            self.ui.entringStringlineEdit.setPlaceholderText('1000100110')
        else:
            self.ui.entringStringlineEdit.setPlaceholderText('ключевое слово')

    def changeDir(self):
        """получение пути к выбранному в treeview каталогу"""
        model = self.ui.treeView.model()
        dir = QtWidgets.QFileSystemModel(model).filePath(self.ui.treeView.selectedIndexes()[0])
        if os.path.isfile(dir):
            dir = os.path.dirname(dir)
        self.ui.selectedDir_lineEdit.setText(str(dir))

    def setValuesForFindeFileThread(self):
        """установка начальных значений для потока"""
        self.findfileThread.ext = self.ui.entringStringlineEdit.text().split()
        self.findfileThread.recursion = self.ui.recursionSearchcheckBox.checkState()
        self.findfileThread.startDir = self.ui.selectedDir_lineEdit.text()

    def initThreads(self):
        self.findfileThread = TFindFileThread()
        self.findfileThread.infoSignal.connect(self.addItemToResultTable)

    def startSearchButtonClick(self):
        """изменяет состояние визуальных элементов и запускает поток"""
        self.ui.startSearchpushButton.setEnabled(False)
        self.ui.stopSearchpushButton.setEnabled(True)
        self.ui.chooseSettingComboBox.setEnabled(False)
        self.ui.entringStringlineEdit.setEnabled(False)
        self.ui.recursionSearchcheckBox.setEnabled(False)
        self.setValuesForFindeFileThread()
        self.findfileThread.start()
        self.ui.tableView.setVisible(True)

    def stopSearchButtonClick(self):
        """изменяет состояние визуальных элементов и останавливает поток"""
        self.ui.startSearchpushButton.setEnabled(True)
        self.ui.stopSearchpushButton.setEnabled(False)
        self.ui.chooseSettingComboBox.setEnabled(True)
        self.ui.entringStringlineEdit.setEnabled(True)
        self.ui.recursionSearchcheckBox.setEnabled(True)
        self.findfileThread.Flag = False


    def createQStandardItemModel(self) -> QtGui.QStandardItemModel:
        sim = QtGui.QStandardItemModel()
        sim.setHorizontalHeaderLabels(["№ п/п", "Путь", "Имя файла", "Размер"])

        return sim

    def addItemToResultTable(self, info: list):
        """добавляет в таблицу информацию о найденных файлах"""
        if info.count()>0:
            sim = QtGui.QStandardItemModel()
            item = QtGui.QStandardItem((info[0]))



class TFindFileThread(QtCore.QThread):
    infoSignal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.Flag = None
        self.startDir = None
        self.ext = None
        self.recursion = False


    def run(self) -> None:
        if self.Flag is None:
            self.Flag = True
        if self.startDir is None:
            self.startDir = QtCore.QDir.currentPath()
        if self.ext is None:
            self.ext = ['.*']
        self.run_fast_scandir(self.startDir, self.ext)

    def run_fast_scandir(self, dir, ext) -> list:  # dir: str, ext: list
        subfolders, files = [], []

        for f in os.scandir(dir):
            if f.is_dir():
                subfolders.append(f.path)
            if f.is_file():
                if os.path.splitext(f.name)[1].lower() in ext:
                    self.infoSignal.emit(f.path)
                    files.append(f.path)
            if not (self.Flag):
                os.scandir().close()
                break
        if self.recursion:
            for dir in list(subfolders):
                sf, f = self.run_fast_scandir(dir, ext)
                subfolders.extend(sf)
                files.extend(f)
        return [subfolders, files]


if __name__ == "__main__":
    app = QtWidgets.QApplication()  # Создаем  объект приложения
    # app = QtWidgets.QApplication(sys.argv)  # Если PyQt

    myWindow = Form_backend()  # Создаём объект окна
    myWindow.show()  # Показываем окно

    sys.exit(app.exec_())  # Если exit, то код дальше не исполняется