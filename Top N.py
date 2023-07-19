from PySide6 import QtWidgets, QtGui, QtCore
import os
import sys
import geopandas as gpd
from functools import partial

class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Shapefile Processor")
        self.setFixedSize(800, 600)

        layout = QtWidgets.QVBoxLayout(self)

        # Select input file
        self.input_path = QtWidgets.QLineEdit(self)
        self.input_path.setPlaceholderText("Path du fichier Shapefile")
        self.input_path_button = QtWidgets.QPushButton('Parcourir', self)
        self.input_path_button.clicked.connect(self.select_input_file)
        layout.addWidget(self.input_path)
        layout.addWidget(self.input_path_button)

        # Select output file
        self.output_path = QtWidgets.QLineEdit(self)
        self.output_path.setPlaceholderText("Path du dossier d'export")
        self.output_path_button = QtWidgets.QPushButton('Parcourir', self)
        self.output_path_button.clicked.connect(self.select_output_folder)
        layout.addWidget(self.output_path)
        layout.addWidget(self.output_path_button)

        # Select top N activities
        self.top_n = QtWidgets.QSpinBox(self)
        self.top_n.setRange(1, 10)
        self.top_n.setValue(3)
        layout.addWidget(QtWidgets.QLabel("Nombre d'activités top:"))
        layout.addWidget(self.top_n)

        # Attributes list (populated when file is selected)
        self.attributes_list = QtWidgets.QListWidget(self)
        self.attributes_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        layout.addWidget(QtWidgets.QLabel("Attributs:"))
        layout.addWidget(self.attributes_list)

        # Execute button
        self.run_button = QtWidgets.QPushButton('Exécuter', self)
        self.run_button.clicked.connect(self.run_script)
        layout.addWidget(self.run_button)

    def select_input_file(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Sélectionnez le fichier Shapefile", "", "Shapefiles (*.shp)")
        self.input_path.setText(filename)
        self.populate_attributes()

    def select_output_folder(self):
        foldername = QtWidgets.QFileDialog.getExistingDirectory(self, "Sélectionnez le dossier d'export")
        self.output_path.setText(foldername)

    def populate_attributes(self):
        df = gpd.read_file(self.input_path.text())
        self.attributes_list.addItems(df.columns.tolist())

    def run_script(self):
        activities = list(set([item.text() for item in self.attributes_list.selectedItems()]))  # Using set to remove duplicates
        n = self.top_n.value()

        df = gpd.read_file(self.input_path.text())
        df[f'Top_{n}_Activities'] = df[activities].apply(lambda row: row.nlargest(n).index.tolist(), axis=1)
        df[f'Top_{n}_ID'] = df[f'Top_{n}_Activities'].apply(lambda x: str(x)).astype('category').cat.codes
        df[f'Top_{n}_Activities'] = df[f'Top_{n}_Activities'].apply(lambda x: ','.join(x))

        grouped = df.groupby(f'Top_{n}_ID')

        for name, group in grouped:
            top_activities = group[f'Top_{n}_Activities'].str.split(',', expand=True).iloc[0].tolist()
            group_df = group[top_activities + [f'Top_{n}_Activities', f'Top_{n}_ID', 'geometry']]  # added 'geometry' as it is necessary for the shapefile

            if group_df[top_activities].sum().sum() != 0:
                # ensure no column names are duplicated
                group_df = group_df.loc[:,~group_df.columns.duplicated()]
                gpd.GeoDataFrame(group_df).to_file(os.path.join(self.output_path.text(), f"{name}_shapefile.shp"))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')

    # create the dark palette
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53,53,53))
    dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(15,15,15))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53,53,53))
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53,53,53))
    dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    
    # apply the dark palette
    app.setPalette(dark_palette)

    # define the font to be used
    font = QtGui.QFont()
    font.setFamily("Arial") # Change this to the font you want to use.
    font.setPointSize(12) # Adjust the point size to fit your needs.
    app.setFont(font) # set the defined font to be the application's font

    window = Window()
    window.show()

    sys.exit(app.exec())
