import os
import sys

import geopandas as gpd
from PySide6 import QtCore, QtGui, QtWidgets


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Shapefile Processor')
        self.setFixedSize(800, 600)

        layout = QtWidgets.QVBoxLayout(self)

        # Input path
        self.input_path = QtWidgets.QLineEdit(self)
        self.input_path.setPlaceholderText('Chemin du fichier Shapefile')
        self.input_path_button = QtWidgets.QPushButton('Parcourir', self)
        self.input_path_button.clicked.connect(self.select_input_file)
        layout.addWidget(self.input_path)
        layout.addWidget(self.input_path_button)

        # Output folder
        self.output_path = QtWidgets.QLineEdit(self)
        self.output_path.setPlaceholderText("Chemin du dossier d'export")
        self.output_path_button = QtWidgets.QPushButton('Parcourir', self)
        self.output_path_button.clicked.connect(self.select_output_folder)
        layout.addWidget(self.output_path)
        layout.addWidget(self.output_path_button)

        # Activity count
        self.top_n = QtWidgets.QSpinBox(self)
        self.top_n.setRange(1, 10)
        self.top_n.setValue(3)
        layout.addWidget(QtWidgets.QLabel("Nombre d'activites top:"))
        layout.addWidget(self.top_n)

        # Field selector
        self.attributes_list = QtWidgets.QListWidget(self)
        self.attributes_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        layout.addWidget(QtWidgets.QLabel('Attributs:'))
        layout.addWidget(self.attributes_list)

        # Run button
        self.run_button = QtWidgets.QPushButton('Executer', self)
        self.run_button.clicked.connect(self.run_script)
        layout.addWidget(self.run_button)

    def select_input_file(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Selectionnez le fichier Shapefile',
            '',
            'Shapefiles (*.shp)',
        )
        if not filename:
            return
        self.input_path.setText(filename)
        self.populate_attributes()

    def select_output_folder(self):
        foldername = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Selectionnez le dossier d'export",
        )
        if foldername:
            self.output_path.setText(foldername)

    def populate_attributes(self):
        src = self.input_path.text().strip()
        if not src:
            return
        try:
            df = gpd.read_file(src, rows=0)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self,
                'Erreur',
                f"Top_N: schema read failed for '{src}': {exc}",
            )
            return
        self.attributes_list.clear()
        cols = [c for c in df.columns if c != 'geometry']
        self.attributes_list.addItems(cols)

    def run_script(self):
        src = self.input_path.text().strip()
        out_dir = self.output_path.text().strip()
        activities = list(
            dict.fromkeys(
                item.text() for item in self.attributes_list.selectedItems()
            )
        )
        if not src or not out_dir or not activities:
            return

        n = min(self.top_n.value(), len(activities))
        try:
            df = gpd.read_file(src)
            top_col = f'Top_{n}_Activities'
            id_col = f'Top_{n}_ID'
            df[top_col] = df[activities].apply(
                lambda row: row.nlargest(n).index.tolist(),
                axis=1,
            )
            df[id_col] = (
                df[top_col].apply(str).astype('category').cat.codes
            )
            df[top_col] = df[top_col].apply(','.join)

            for name, group in df.groupby(id_col):
                top_cols = group[top_col].iloc[0].split(',')
                keep = top_cols + [top_col, id_col, 'geometry']
                group_df = group[keep]
                if group_df[top_cols].sum().sum() != 0:
                    group_df = group_df.loc[:, ~group_df.columns.duplicated()]
                    out_file = os.path.join(out_dir, f'{name}_shapefile.shp')
                    gpd.GeoDataFrame(group_df, crs=df.crs).to_file(out_file)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self,
                'Erreur',
                f"Top_N: export failed for '{src}' -> '{out_dir}': {exc}",
            )


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')

    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(15, 15, 15))
    dark_palette.setColor(
        QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53)
    )
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(
        QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218)
    )
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    app.setPalette(dark_palette)

    font = QtGui.QFont('Arial', 12)
    app.setFont(font)

    window = Window()
    window.show()
    sys.exit(app.exec())
