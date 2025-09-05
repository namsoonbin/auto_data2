# -*- coding: utf-8 -*-
"""
PyInstaller hook for qt-material-icons
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all submodules 
hiddenimports = collect_submodules('qt_material_icons')

# Collect data files (icon resources)
datas = collect_data_files('qt_material_icons')

# Add specific resources that might be missed
datas += collect_data_files('qt_material_icons.resources', include_py_files=True)