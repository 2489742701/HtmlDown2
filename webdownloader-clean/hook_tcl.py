import os
import sys

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    
    tcl_path = os.path.join(base_path, 'tcl8.6')
    tk_path = os.path.join(base_path, 'tk8.6')
    
    if os.path.exists(os.path.join(tcl_path, 'init.tcl')):
        os.environ['TCL_LIBRARY'] = tcl_path
    
    if os.path.exists(os.path.join(tk_path, 'tk.tcl')):
        os.environ['TK_LIBRARY'] = tk_path
