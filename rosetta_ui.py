import sys
import os
import subprocess
import shutil
import uuid
import pandas as pd
from io import StringIO

from PyQt5 import QtWidgets, uic
from pymol.Qt import utils
from PyQt5.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTreeView, QFileDialog,
    QFileSystemModel, QGridLayout, QStackedWidget,
    QMainWindow,
)
from PyQt5.QtCore import QAbstractTableModel, Qt

from pymol import cmd
from pymol.plugins import addmenuitemqt


#Get the Python interpreter path
python_executable = sys.executable
download_button = None

def find_ui_file(filename):
    # Try to find the .ui file in the plugin directory, including all subdirectories
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = search_in_directory(plugin_dir, filename)
    if ui_path:
        return ui_path
    
    # If not found, try to find the .ui file in the current working directory, including all subdirectories
    current_working_dir = os.getcwd()
    ui_path = search_in_directory(current_working_dir, filename)
    if ui_path:
        return ui_path
    
    # If still not found, try to find the .ui file in the environment variable specified by the user
    env_path = os.getenv('PLUGIN_PATH')
    if env_path:
        ui_path = search_in_directory(env_path, filename)
        if ui_path:
            return ui_path
    
    # If all attempts fail, raise an exception
    raise FileNotFoundError(f"Unable to find the UI file: {filename}")

def search_in_directory(directory, filename):
    """Recursively search for files in the directory and its subdirectories"""
    for root, dirs, files in os.walk(directory):
        if filename in files:
            return os.path.join(root, filename)
    return None


# result_window window periodic control
def open_result_window(form, file_path, type, option_file2_path=None):
    window_id = uuid.uuid4().hex  # 生成一个唯一的ID
    new_window = ResultWindow(file_path, type, option_file2_path= option_file2_path,form=form)
    form.result_windows[window_id] = new_window
    new_window.show()
    return window_id




def run_plugin_gui():
    dialog = QtWidgets.QDialog()
    uifile = find_ui_file('rosetta.ui')

    form = uic.loadUi(uifile, dialog)
    form.result_windows = {}

    # diglog close event
    def close_event():
        clean_temp()
        dialog.close()

    dialog.rejected.connect(close_event)

    def select_file(button_name, line_edit_name):
        filename, _ = QFileDialog.getOpenFileName(dialog, "Select File")
        if filename:
            getattr(form, line_edit_name).setText(filename)

    def switch_to_page(page_index):
        form.stackedWidget.setCurrentIndex(page_index)

    dialog.show()

    form.stackedWidget.setCurrentIndex(0)
    # Page switching click event
    form.select_match.clicked.connect(lambda: switch_to_page(3))  # 
    form.select_design.clicked.connect(lambda: switch_to_page(1))  # 假设design页面是stackedWidget的第0页
    form.select_prepare.clicked.connect(lambda: switch_to_page(0))  
    form.select_mpnn.clicked.connect(lambda: switch_to_page(2))  
    
    # Connect button click events
    # prepare feature
    form.prepare_upload_pdb_2.clicked.connect(lambda: select_file('prepare_upload_pdb_2', 'prepare_show_cstpath'))
    form.prepare_upload_pdb_3.clicked.connect(lambda: select_file('prepare_upload_pdb_3', 'prepare_show_cleanpdb'))  
    form.prepare_upload_mol2.clicked.connect(lambda: select_file('prepare_upload_mol2', 'prepare_show_mol2path'))
    form.prepare_upload_pdbfile.clicked.connect(lambda: select_file('prepare_upload_pdbfile', 'prepare_show_pdbpath'))
    form.prepare_upload_ligandfile.clicked.connect(lambda: select_file('prepare_upload_ligandfile', 'prepare_show_ligandpath'))  

    form.prepare_get_pdbfile.clicked.connect(lambda: open_result_window(form,form.prepare_show_pdbname.text(),"get_pdb")) 
    form.prepare_genrate_cst.clicked.connect(lambda: open_result_window(form,form.prepare_show_cstpath.text(),"generate_cst"))
    form.prepare_generate_cleanpdb.clicked.connect(lambda: open_result_window(form,form.prepare_show_cleanpdb.text(),"clean_pdb"))
    form.prepare_generate_params.clicked.connect(lambda: open_result_window(form,form.prepare_show_mol2path.text(),"generate_params"))
    form.prepare_generate_posfile.clicked.connect(lambda: open_result_window(form,form.prepare_show_pdbpath.text(),"generate_posfile",option_file2_path=form.prepare_show_ligandpath.text()))
    form.prepare_get_cstfile.clicked.connect(lambda: open_result_window(form,form.prepare_show_pdbname_2.text(),"get_cstdatabasefile"))

    # match feature
    form.select_cst_params.clicked.connect(lambda: select_file('select_cst_params', 'cst_params_entry'))
    form.select_cst_file.clicked.connect(lambda: select_file('select_cst_file', 'cst_file_entry'))
    form.select_pos_file.clicked.connect(lambda: select_file('select_pos_file', 'pos_file_entry'))
    form.select_pdb_file.clicked.connect(lambda: select_file('select_pdb_file', 'pdb_file_entry'))


    # design feature
    form.select_cst_params_2.clicked.connect(lambda: select_file('select_cst_params_2', 'cst_params_entry_2'))
    form.select_cst_file_2.clicked.connect(lambda: select_file('select_cst_file_2', 'cst_file_entry_2'))
    form.select_design_pdb_file.clicked.connect(lambda: select_file('select_design_pdb_file', 'design_show_pdbpath'))


    form.design_upload_scfile.clicked.connect(lambda: select_file('design_upload_scfile','design_show_scfilepath_2'))
    form.design_start_scanalysis.clicked.connect(lambda: analysis_desing_view(form.design_show_scfilepath_2.text(),form))


    # mpnn feature
    form.select_checkpoint_file.clicked.connect(lambda: select_file('select_checkpoint_file', 'checkpoint_file_entry'))
    form.select_pdb_file_2.clicked.connect(lambda: select_file('select_pdb_file_2', 'pdb_file_entry_2'))
    form.select_model_type.currentIndexChanged.connect(lambda index: on_combobox_changed(form, index))
    form.model_type_entry.setText(f"default model type: ligand mpnn")

    form.select_score_button.clicked.connect(lambda: select_file('select_score_button','mpnn_show_scpath'))
    form.analysisscore.clicked.connect(lambda: analysis_mpnn_view(form.mpnn_show_scpath.text(),form))
    

    def run_command():
        # Get the values from UI controls
        ligand_params = form.cst_params_entry.text()
        cst_file = form.cst_file_entry.text()
        pos_file = form.pos_file_entry.text()
        pdb_file = form.pdb_file_entry.text()
        script_directory = os.path.dirname(os.path.abspath(__file__))

        ligand_name=ligand_params.split("/")[-1].split(".")[0]
        
        command = f"{script_directory}/rosettadesign_script/match.static.linuxgccrelease " \
                  f"-extra_res_fa {ligand_params} " \
                  f"-match:geometric_constraint_file {cst_file} " \
                  f"-match:scaffold_active_site_residues {pos_file} "\
                  f"-s {pdb_file} "\
                  f"-match:lig_name  {ligand_name} " \
                  "-in:ignore_unrecognized_res "\
                  "-ex1 -ex2 " \

        
        try:
            os.makedirs("./rosetta_ui_temp/match_results", exist_ok=True)
            os.chdir("./rosetta_ui_temp/match_results")
            process = subprocess.Popen(command, shell=True)
           
            os.chdir("../../")

        except Exception as e:
            print("match error!")
            
        browserpath = os.getcwd()+"/rosetta_ui_temp/match_results"
        update_file_browser(browserpath)
    
    def run_design_command():
        ligand_params = form.cst_params_entry_2.text()
        cst_file = form.cst_file_entry_2.text()
        design_pdb_file = form.design_show_pdbpath.text()

        script_directory = os.path.dirname(os.path.abspath(__file__))
        
        command = f"{script_directory}/rosettadesign_script/enzyme_design.static.linuxgccrelease -s {design_pdb_file} -enzdes::cstfile {cst_file} -extra_res_fa {ligand_params} " \
                "-run::preserve_header \
                -parser:protocol /home/bio/workshop/Zpinyang/app/rosetta_design/enzdes_new.xml \
                -database /usr/local/rosetta.binary.linux.release-371/main/database/ \
                -run::preserve_header \
                -enzdes::detect_design_interface \
                -enzdes::cut1 6.0 \
                -enzdes::cut2 8.0 \
                -enzdes::cut3 10.0 \
                -enzdes::cut4 12.0 \
                -mute core.io.database \
                -jd2::enzdes_out  \
                -nstruct 15 \
                -jd2:ntrials 1 \
                -out:file:o score.sc "

        try:
            os.makedirs("./rosetta_ui_temp/design_results", exist_ok=True)
            os.chdir("./rosetta_ui_temp/design_results")

            process = subprocess.Popen(command, shell=True)

            os.chdir("../../")

        except Exception as e:
            print("design error!")
            
        browserpath = os.getcwd()+"/rosetta_ui_temp/design_results"
        update_file_browser(browserpath)


    # mpnn 
    def on_combobox_changed(form):

        current_text = form.select_model_type.currentText()
        form.model_type_entry.setText(f"current select : {current_text}")

    def run_mpnn_command():
        script_directory = os.path.dirname(os.path.abspath(__file__))

        checkpoint_file = form.checkpoint_file_entry.text()
        pdb_file = form.pdb_file_entry_2.text()
        model_type = form.select_model_type.currentText()
        chain = form.mpnn_show_chain.text()
        # 构建命令
        command = f"/home/bio/workshop/Zpinyang/ligandmpnn/bin/python {script_directory}/mpnn_script/run.py " \
            f"--pdb_path {pdb_file} "\
            f"--checkpoint_ligand_mpnn {checkpoint_file} " \
            f"--model_type {model_type} " \
            "--seed 37 "\
            "--batch_size 5 "\
            "--temperature 0.05 "\
            "--save_stats 1 "\
            f'--chains_to_design {chain} '\
            "--out_folder ./rosetta_ui_temp/mpnn_results "
        print(command)

        try:
            process = subprocess.Popen(command, shell=True)
            print("mpnn start")

        except Exception as e:
            print("ligand error!")
     
        browserpath = os.getcwd()+"/rosetta_ui_temp/mpnn_results"
        update_file_browser(browserpath)
         
    form.run_button.clicked.connect(run_command)
    form.run_design_button.clicked.connect(run_design_command)
    form.run_button_2.clicked.connect(run_mpnn_command)


    def update_file_browser(reuslt_path):
        # Initialize the file system model and set the filter to display only PDB files
        file_system_model = QFileSystemModel()
        file_system_model.setRootPath(reuslt_path)  
        file_system_model.setNameFilters(['*.pdb'])  
        file_system_model.setNameFilterDisables(False) 

        # Set the file system model to the QTreeView control
        form.file_tree_view.setModel(file_system_model)
        form.file_tree_view.setRootIndex(file_system_model.index(reuslt_path)) #Show the directory where PDB files are saved
        form.file_tree_view.selectionModel().selectionChanged.connect(lambda selected, deselected: load_pdb_structure(file_system_model, selected))
    
        initialize_download_button(form, file_system_model)

def load_pdb_structure(model, selected):
    '''load selected pdb structure'''
    indexes = selected.indexes()
    if indexes:
        index = indexes[0]

        if model.isDir(index):
            return

        pdb_file_path = model.filePath(index)
        
        cmd.load(pdb_file_path)

        cmd.show('cartoon')
        cmd.color('auto')
        cmd.reset()
 

from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtWidgets import QFileSystemModel, QTreeView, QPushButton, QFileDialog, QMessageBox

def initialize_download_button(form, file_system_model):
    '''reusults for initialize download button'''
    global download_button
    if download_button:
        return
    else:
        download_button = QPushButton("Download File", form)
        download_button.clicked.connect(lambda: download_selected_file(file_system_model, form.file_tree_view))
        form.layout().addWidget(download_button)

def download_selected_file(file_system_model, file_tree_view):
    selected_indexes = file_tree_view.selectionModel().selectedIndexes()
    if not selected_indexes:
        QMessageBox.warning(None, "No file selected！", QMessageBox.Ok)
        return

    file_path = file_system_model.filePath(selected_indexes[0])

    if not os.path.exists(file_path):
        QMessageBox.warning(None, "error ", f"Invalid file path: {file_path} !", QMessageBox.Ok)
        return

    download_directory = QFileDialog.getExistingDirectory(None, "Select download directory", os.getcwd())

    if not download_directory:
        return

    file_name = os.path.basename(file_path)

    target_path = os.path.join(download_directory, file_name)

    try:
        shutil.copy(file_path, target_path)
        QMessageBox.information(None, "提示", f"文件已成功下载到 {target_path}", QMessageBox.Ok)
    except Exception as e:
        QMessageBox.critical(None, "错误", f"文件下载失败: {e}", QMessageBox.Ok)




import requests

def download_pdb(pdb_id):

    original_dir = os.getcwd()
    output_path = os.path.join(original_dir, "./rosetta_ui_temp/prepare/get_pdb")
    os.makedirs(output_path, exist_ok=True)
    os.chdir(output_path)


    pdb_url = f'https://files.rcsb.org/download/{pdb_id}.pdb'
    try:
        response = requests.get(pdb_url)
        output_file = f"{pdb_id}.pdb"
        with open(output_file, 'wb') as f:
            f.write(response.content)

        print(f"PDB file {pdb_id}.pdb downloaded to {output_path}")
    except:
        print(f"Unable to download PDB file {pdb_id}.pdb, status code:  {response.status_code}")
        return None
    
    finally:
        os.chdir(original_dir)

    return output_path

def generate_cst(input_file):
    script_directory = os.path.dirname(os.path.abspath(__file__))

    try:
        output_path = os.path.join(os.getcwd(),"./rosetta_ui_temp/prepare/generate_cst")
        subprocess.run([ python_executable,f'{script_directory}/generate_cst/generate_cst.py', "-i",input_file, "-o",output_path], check=True)


    except subprocess.CalledProcessError as e:
        print(f"Generate CST file : {e}")
        return None

    print(f"File generated to: {output_path}")
    return output_path


def clean_pdb(input_file):
    original_dir = os.getcwd()
    output_path = os.path.join(original_dir, "./rosetta_ui_temp/prepare/clean")
    os.makedirs(output_path, exist_ok=True)
    os.chdir(output_path)
    script_directory = os.path.dirname(os.path.abspath(__file__))
    try:
        subprocess.run([f'{script_directory}/prepare_script/clean_pdb.py', input_file , "A"], check=True)
        print(f"File generated to:  {output_path}")

    except subprocess.CalledProcessError as e:
        print(f"Clean PDB failed: {e}")
        return None
    
    finally:
        os.chdir(original_dir)


    return output_path   

def generate_params(input_file):

    original_dir = os.getcwd()
    output_path = os.path.join(original_dir, "./rosetta_ui_temp/prepare/generate_params")
    os.makedirs(output_path, exist_ok=True)
    os.chdir(output_path)
    script_directory = os.path.dirname(os.path.abspath(__file__))
    try:
        subprocess.run([f'{script_directory}/prepare_script/molfile_to_params.py', input_file ], check=True)
        print(f"File generated to:   {output_path}")

    except subprocess.CalledProcessError as e:
        print(f"Generate Params failed:  {e}")
        return None
    
    finally:
        os.chdir(original_dir)


    return output_path
    
def generate_posfile(input_file,input_file2):
    
    original_dir = os.getcwd()
    output_path = os.path.join(original_dir, "./rosetta_ui_temp/prepare/generate_posfile")
    os.makedirs(output_path, exist_ok=True)
    os.chdir(output_path)
    script_directory = os.path.dirname(os.path.abspath(__file__))

    try:
        shutil.copy(input_file, output_path)
        shutil.copy(input_file2, output_path)
        base_name = os.path.basename(input_file)
        base_name2 = os.path.basename(input_file2)

        subprocess.run([f'{script_directory}/prepare_script/gen_lig_grids.static.linuxgccrelease', "-s", base_name, base_name2], check=True)
        os.remove(base_name)
        os.remove(base_name2)
        print(f"File generated to: {output_path}")     


    except subprocess.CalledProcessError as e:
        print(f"Generate POS file failed: {e}")
        return None
    finally:
        os.chdir(original_dir)

    return output_path


import re
def get_cstdatabasefile(target_name):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    original_dir = os.getcwd()
    output_path = os.path.join(original_dir, "./rosetta_ui_temp/prepare/getcst")
    os.makedirs(output_path, exist_ok=True)  

    try:
        is_ec = False
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', target_name) or target_name.startswith('EC'):
            is_ec = True
        additional_arguments = []
        if is_ec:
            additional_arguments = ["-se", target_name]
        else:
            additional_arguments = ["-sp", target_name]

        command = [
            f'{script_directory}/prepare_script/ECNum_relate_PDBNum.py',
            "-i",
            f'{script_directory}/prepare_script/index.txt',
        ] + additional_arguments

        print("Running command:", ' '.join(command))
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )

        ec_paths = result.stdout.strip().splitlines()[1:]
        if not ec_paths:
            print("No EC paths found.")
            return None

        for path in ec_paths:
            dir_name = os.path.basename(path)
            output_add_dirname = os.path.join(output_path, dir_name)
            shutil.copytree(path, output_add_dirname, dirs_exist_ok=True)
        
        return output_path

    except FileNotFoundError:
        print(f"files does not exist.")
        return None
    except PermissionError:
        print(f"Permission denied when accessing .")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

class ResultWindow(QMainWindow):
    def __init__(self, file_path, type, option_file2_path=None, window_id=None, form=None):
        super().__init__()
        self.file_path = file_path
        self.type = type
        self.option_file2_path = option_file2_path
        self.window_id = window_id
        self.form = form 
        self.closeEvent = self._on_close

        uifile = find_ui_file('result_ui.ui')
        self.ui = uic.loadUi(uifile, self)  

        if type == "get_pdb":
            output_path = download_pdb(file_path)

        elif type == "generate_cst":
            output_path = generate_cst(file_path)
            
        elif type == "clean_pdb":
            output_path = clean_pdb(file_path)

        elif type == "generate_params":
            output_path = generate_params(file_path)

        elif type == "generate_posfile":
            output_path = generate_posfile(file_path,option_file2_path)

        elif type == "get_cstdatabasefile":
            output_path = get_cstdatabasefile(file_path)

        self.file_list = []
        for root, dirs, files in os.walk(output_path):
            for file in files:
                self.file_list.append(file)
        print(self.file_list,output_path)

        for file in self.file_list:
            self.ui.listWidget.addItem(file)
        
        self.ui.pushButton.clicked.connect(lambda: self.download_file(output_path))

    def _on_close(self, event):
        event.accept()
        if self.window_id in self.form.result_windows:
            del self.form.result_windows[self.window_id]       

    def download_file(self,output_path):

        selected_file =self.ui.listWidget.currentItem().text()
        current_file = os.path.join(output_path, selected_file)

        save_path, _ = QFileDialog.getSaveFileName(self, "Save file", selected_file)
        
        if save_path and os.path.exists(current_file):
            with open(current_file, 'rb') as f_in:
                with open(save_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            print(f"File saved to: {save_path}")



# analysis
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(section)
        return None

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        self._data = self._data.sort_values(self._data.columns[column], ascending=(order == Qt.AscendingOrder))
        self.layoutChanged.emit()

def analysis_desing_view(ligand_score_path,view):
    analysis_view_widget = view.design_show_scanalyresults
    read_and_display_designsc(ligand_score_path, analysis_view_widget)


def read_and_display_designsc(file_path, analysis_view_widget):

    data = []
    # Design SC format
    header_index = None
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("total_score"):
            header_index = i
            break
    if header_index is not None:
        table_data = lines[header_index:]
        df = pd.read_csv(StringIO(''.join(table_data)), sep='\s+')
        model = PandasModel(df)
        analysis_view_widget.setModel(model)
        analysis_view_widget.setSortingEnabled(True)
    else:
        print("Header row not found")



def analysis_mpnn_view(ligand_score_path,view):
    analysis_view_widget = view.analysis_view
    read_and_display_fq_info(ligand_score_path, analysis_view_widget)

def read_and_display_fq_info(file_path, view):

    data = []

    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('>'):
                parts = line[1:].strip().split(',')
                entry = {}
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        entry[key.strip()] = value.strip()
                    else:
                    
                        entry['pdb name'] = part.strip()
                data.append(entry)
    
    df = pd.DataFrame(data)
    # Create the model and set it to QTableView
    model = PandasModel(df)
    view.setModel(model)
    view.setSortingEnabled(True)


def clean_temp():
    '''Clean up temporary directories created during the run'''
    temp_dir = './rosetta_ui_temp'  
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            print(f"Successfully deleted temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Error deleting temporary directory: {e}")



