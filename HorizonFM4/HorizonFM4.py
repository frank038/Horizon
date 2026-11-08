#!/usr/bin/env python3

VERSION = "0.9.6 beta"
FMNAME = "Horizon"
FMSITE = "https://github.com/frank038/Horizon"

import sys,os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk,Gdk,Gio,GObject,Pango,GLib,Graphene,Gsk
gi.require_version('GUdev', '1.0')
from gi.repository import GUdev
from urllib.parse import unquote, quote
import stat,shutil
from threading import Thread, Event
import subprocess
from pathlib import Path
import datetime
import json
import locale

gi.require_version('UDisks', '2.0') 
from gi.repository import UDisks

app = None
_curr_dir = os.getcwd()
_HOME = os.path.expanduser("~")

locale.setlocale(locale.LC_ALL, '')
DECIMAL_SEP = locale.localeconv()["decimal_point"]

# the directory settings and options
if not os.access(_curr_dir, os.W_OK):
    HOME_CONFIG = os.path.join(_HOME,".config","HorizonFM4")
    try:
        if not os.path.exists(HOME_CONFIG):
            os.mkdir(HOME_CONFIG, mode=0o770)
    except:
        HOME_CONFIG = _curr_dir
    if HOME_CONFIG != _curr_dir:
        try:
            shutil.copytree("/usr/share/HorizonFM4/configs", os.path.join(HOME_CONFIG, "configs"))
            shutil.copytree("/usr/share/HorizonFM4/icons", os.path.join(HOME_CONFIG, "icons"))
            shutil.copytree("/usr/share/HorizonFM4/langs", os.path.join(HOME_CONFIG, "langs"))
            shutil.copytree("/usr/share/HorizonFM4/scripts", os.path.join(HOME_CONFIG, "scripts"))
        except Exception as E:
            HOME_CONFIG = _curr_dir
else:
    HOME_CONFIG = _curr_dir

BOOKMARK_FILE = os.path.join(HOME_CONFIG,"configs/bookmarks") # TO DO

TRASHCAN_FILES_DIR = os.path.join(_HOME, ".local/share/Trash/files")
TRASHCAN_FILES_INFO = os.path.join(_HOME, ".local/share/Trash/info")
TRASHCAN_FILES_EXPUNGED = os.path.join(_HOME, ".local/share/Trash/expunged")

SCRIPTS_DIRECTORY = os.path.join(HOME_CONFIG, "scripts")

PANEL_STYLE_CSS = os.path.join(HOME_CONFIG, "configs/windowstyle.css")

## language
# os.environ["LANGUAGE"] = "en"
sys.path.append(os.path.join(HOME_CONFIG, "langs"))
_lang_names = GLib.get_language_names()
_langs_application = os.listdir(os.path.join(HOME_CONFIG, "langs"))
for l_lang in _lang_names:
    if l_lang+".py" in _langs_application:
        _lang = __import__(l_lang)
        break
else:
    _lang = __import__("en")

config_file = os.path.join(HOME_CONFIG, "configs/config.json")
config_conf_start = { 
"wwidth": 880, 
"wheight": 620, 
"panel_lateral_width": 300, 
"dwidth": 600, 
"dheight": 400, 
"pwidth": 600, 
"use_rubberband": 1, 
"icon_size": 96, 
"service_icon_size": 24, 
"drag_icon_size": 48, 
"box_size_w": 80, 
"box_size_h": 40, 
"box_internal_spacing": 4, 
"link_icon_size": 24, 
"panel_icon_size": 24, 
"trashview_icon_size": 24, 
"terminal": "lxterminal", 
"terminal_args": "--working-directory=", 
"can_thumb": 1, 
"can_thumb_everywhere": 0, 
"thumbnail_size": 1, 
"media_skip": "/dev/sda;/dev/sda1;/dev/sda2;/dev/sda3" 
}
if not os.path.exists(config_file):
    try:
        _data_json = config_conf_start
        _ff =  open(config_file, "w")
        json.dump(_data_json, _ff, indent = 4)
        _ff.close()
        config_conf = config_conf_start
    except:
        sys.exit()
else:
    try:
        _ff = open(config_file, "r")
        config_conf = json.load(_ff)
        _ff.close()
    except:
        sys.exit()

######### CONFIGURATION
WWIDTH =  config_conf["wwidth"] # this program width
WHEIGHT = config_conf["wheight"] # this program height
LATERAL_PANEL_WIDTH = config_conf["panel_lateral_width"] # left panel width
DWIDTH = config_conf["dwidth"] # dialog width
DHEIGHT = config_conf["dheight"] # dialog height
PDWIDTH = config_conf["pwidth"] # property dialog width
USE_RUBBERBAND = config_conf["use_rubberband"] # enable the rubberband
SERVICE_ICON_SIZE = config_conf["service_icon_size"] # icons in the switcher and others
DRAG_ICON_SIZE = config_conf["drag_icon_size"] # the size of the icon while dragging
ICON_SIZE = config_conf["icon_size"] # item icon size
BOX_SIZE_W = ICON_SIZE+config_conf["box_size_w"] # each item width
BOX_SIZE_H = ICON_SIZE+config_conf["box_size_h"] # each item height
BOX_INTERNAL_SPACING = config_conf["box_internal_spacing"] # each surrounding item spacing
LINK_ICON_SIZE = config_conf["link_icon_size"] # link icon size
PANEL_ICON_SIZE = config_conf["panel_icon_size"] # lateral panel icon size
TRASH_ICON_SIZE = config_conf["trashview_icon_size"] # trashcan view
TERMINAL = config_conf["terminal"] # the terminal name
TERMINAL_ARG = config_conf["terminal_args"] # the terminal argument(s)
CAN_THUMB = config_conf["can_thumb"] # use the thumbnailers
CAN_THUMB_EVERYWHERE = config_conf["can_thumb_everywhere"] # use the thumbnailers not only for home
# 0 normal - 1 large - 2 x-large - 3 xx-large
THUMBNAIL_SIZE = config_conf["thumbnail_size"] # thumbnail pictures size to store
MEDIA_SKIP_TMP = config_conf["media_skip"] # storage devices to not to show in the view
#########
MEDIA_SKIP = MEDIA_SKIP_TMP.split(";")

if CAN_THUMB == 1:
    try:
        gi.require_version('GnomeDesktop', '4.0')
        from gi.repository import GnomeDesktop
    except:
        CAN_THUMB = 0

icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
clipboard = Gdk.Display.get_default().get_clipboard()
self_main = None

MENU_XML="""
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <item>
        <attribute name="action">win.hidden</attribute>
        <attribute name="label" translatable="yes">{0}</attribute>
      </item>
      <item>
        <attribute name="action">win.settings</attribute>
        <attribute name="label" translatable="yes">{1}</attribute>
      </item>
      <item>
        <attribute name="action">win.about</attribute>
        <attribute name="label" translatable="yes">{2}</attribute>
      </item>
      <item>
        <attribute name="action">win.quit</attribute>
        <attribute name="label" translatable="yes">{3}</attribute>
        <attribute name="accel">&lt;Primary&gt;Q</attribute>
    </item>
    </section>
  </menu>
</interface>
""".format(_lang.SHOWHIDE,_lang.SETTINGS,_lang.ABOUT,_lang.QUIT)

# convert the size into readable string
def convert_size(fsize2):
    if fsize2 == 0 or fsize2 == 1:
        sfsize = str(fsize2)+" byte"
    elif fsize2//1024 == 0:
        sfsize = str(fsize2)+" bytes"
    elif fsize2//1048576 == 0:
        sfsize = str(round(fsize2/1024, 3))+" KB"
    elif fsize2//1073741824 == 0:
        sfsize = str(round(fsize2/1048576, 3))+" MB"
    elif fsize2//1099511627776 == 0:
        sfsize = str(round(fsize2/1073741824, 3))+" GiB"
    else:
        sfsize = str(round(fsize2/1099511627776, 3))+" GiB"
    return sfsize.replace(".", DECIMAL_SEP or ".")

############# copy/cut section
_errors = ""
class CopyDialog(Gtk.Window):
    def __init__(self, _parent, _signal, _event):
        super().__init__()
        self._parent = _parent
        self._signal = _signal
        self._signal.connect("notify::propList", self.signal_threadslot)
        self._event = _event
        #
        self.set_transient_for(self._parent)
        self.set_modal(True)
        self.set_titlebar(Gtk.Box.new(0,0))
        self.set_destroy_with_parent(True)
        self.set_resizable(False)
        self.set_name("copydialog")
        self.set_size_request(DWIDTH, 10)
        self.error_set = 0
        #
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(self.box)
        #
        self.prog_bar = Gtk.ProgressBar.new()
        self.prog_bar.set_show_text(True)
        self.prog_bar.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.box.append(self.prog_bar)
        #
        box_btn = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box_btn.set_hexpand(True)
        self.box.append(box_btn)
        #
        self.cancel_btn = Gtk.Button(label=_lang.CANCEL)
        self.cancel_btn.set_hexpand(True)
        box_btn.append(self.cancel_btn)
        self.cancel_btn.connect("clicked", self.on_cancel_btn)
        #
        self.close_btn = Gtk.Button(label=_lang.CLOSE)
        self.close_btn.set_hexpand(True)
        box_btn.append(self.close_btn)
        self.close_btn.connect("clicked", self.on_close_btn)
        self.close_btn.set_sensitive(False)
        #
        # self.present()
        
    def signal_threadslot(self, _signal, _param):
        _list = _signal.propList[0]
        ########## copy operation
        if _list[0] == "COPYD":
            _data = _list[1]
            self.set_values_widgets(_data)
        elif _list[0] == "COPYD_DONE":
            _data = _list[1]
            self.prog_bar.set_text(_data[0])
        elif _list[0] == "COPYD_ERROR":
            _data = _list[1]
            self.prog_bar.set_text(_data[0])
        elif _list[0] == "COPYD_ABORT":
            _data = _list[1]
            self.prog_bar.set_text(_data[0])
        ######## delete operation
        elif _list[0] == "DELETED":
            _data = _list[1]
            self.set_values_widgets(_data)
        elif _list[0] == "DELETED_DONE":
            _data = _list[1]
            self.prog_bar.set_text(_data[0])
        elif _list[0] == "DELETED_ERROR":
            _data = _list[1]
            self.prog_bar.set_text(_data[0])
        elif _list[0] == "DELETED_ABORT":
            _data = _list[1]
            self.prog_bar.set_text(_data[0])
    
    def set_values_widgets(self, _data):
        _lbl = _data[0]
        _num = _data[1]
        self.prog_bar.set_text(_lbl or "-------")
        self.prog_bar.set_fraction(float(_num) or 1)
        
    def on_cancel_btn(self, w):
        self._event.set()
        
    def on_close_btn(self, w):
        self.destroy()
        if self.error_set == 1:
            SimpleDialog(self_main, _lang.GERROR, _errors)


def add_link_sfx(file_name_dst):
    ff = Gio.File.new_for_path(file_name_dst)
    qret = ff.query_exists(None)
    while qret:
        z = datetime.datetime.now()
        #dY, dM, dD, dH, dm, ds, dms
        commSfx = "_{}.{}.{}_{}.{}.{}".format(z.year, z.month, z.day, z.hour, z.minute, z.second)
        file_name_dst += commSfx
        # file_name_dst += "_1"
        del ff
        ff = Gio.File.new_for_path(file_name_dst)
        qret = ff.query_exists(None)
    return file_name_dst

def add_file_sfx(file_name_dst):
    _file_exists = os.path.exists(file_name_dst)
    while _file_exists:
        z = datetime.datetime.now()
        #dY, dM, dD, dH, dm, ds, dms
        commSfx = "_{}.{}.{}_{}.{}.{}".format(z.year, z.month, z.day, z.hour, z.minute, z.second)
        _sfx = commSfx
        # _sfx = "_1"
        file_name_dst = file_name_dst+_sfx
        _file_exists = os.path.exists(file_name_dst)
    return file_name_dst

def on_copy_file2(dest_path, ff, _overwrite):
    global _errors
    try:
        if _overwrite == 0:
            dest_path = add_file_sfx(dest_path)
        ret = False
        _f = shutil.copy2(ff, dest_path, follow_symlinks=False)
        if _f == dest_path:
            ret = True
        if ret == False:
            _errors += "Error while copying {}\n".format(ff.get_path())
            return _errors
        return 1
    except Exception as E:
        _errors += str(E)+"\n"
        return _errors

# make a shadow copy of a folder
def on_copy_dir2(dest_path):
    global _errors
    try:
        dest_path2 = add_file_sfx(dest_path)
        shutil.copytree(dest_path, dest_path2)
        return 1
    except Exception as E:
        _errors += str(E)+"\n"
        return _errors
    
def on_walktree(root_path, _path, base_path_src, _overwrite):
    #
    global _errors
    FULL_PATH_SRC = root_path
    BASE_PATH_SRC = base_path_src
    file_dst = None
    dest_path = None
    file_name_dst = None
    #
    _fffff = _path[len(BASE_PATH_SRC)+1:]
    f_file_name = os.path.join(FULL_PATH_SRC,_fffff)
    if not os.path.exists(f_file_name):
        try:
            os.mkdir(f_file_name, mode=0o755)
        except Exception as E:
            _errors += str(E)+"\n"
            return _errors
    #
    for f in os.listdir(_path):
        pathname = os.path.join(_path, f)
        mode = os.lstat(pathname).st_mode
        if stat.S_ISDIR(mode):
            # It's a directory, recurse into it
            if os.path.exists(pathname):
                on_walktree(root_path, pathname, base_path_src, _overwrite)
        elif stat.S_ISREG(mode):
            # file to copy
            file_src = pathname
            # file destination
            file_dst = pathname[len(BASE_PATH_SRC)+1:]
            dest_path = os.path.join(FULL_PATH_SRC, file_dst)
            #
            if _overwrite == 0:
                dest_path = add_file_sfx(dest_path)
            #
            ff = Gio.File.new_for_path(file_src)
            try:
                ret = on_copy_file(dest_path, ff)
            except GLib.Error as err:
                _errors += err.message+"\n"
        elif stat.S_ISLNK(mode):
            try:
                link_to = os.readlink(pathname)
                file_dst = pathname[len(BASE_PATH_SRC)+1:]
                dest_path = os.path.join(FULL_PATH_SRC, file_dst)
                dest_path = add_link_sfx(dest_path)
                os.symlink(link_to, dest_path)
            except Exception as E:
                _errors += str(E)+"\n"
        else:
            # Unknown file type
            _errors += "Skipped unknown item: {}\n".format(pathname)
    if _errors == "":
        return 1
    else:
        return _errors
    
# operation: copy or cut
def on_copy_file(dest_path=None, ff=None, operation=None, _signal=None, _overwrite=None):
    global _errors
    try:
        mode = os.lstat(ff).st_mode
        if stat.S_ISDIR(mode):
            if _signal:
                _signal.propList = ["PULSE_COPY",os.path.basename(ff)]
            if not os.path.exists(dest_path):
                try:
                    shutil.copytree(ff, dest_path)
                    if operation == "cut":
                        shutil.rmtree(ff)
                except Exception as E:
                    _errors += str(E)+"\n"
                    return _errors
                return 1
            else:
                # make a copy of the same folder in the same directory
                if operation == "cut":
                    _errors += "Error {}: same folder.".format(os.path.basename(ff)) 
                    return _errors
                if dest_path == ff:
                    ret = on_copy_dir2(dest_path)
                    if ret != 1:
                        return _errors
                    return 1
                #
                ret = on_walktree(os.path.dirname(dest_path), ff, os.path.dirname(ff), _overwrite)
                if ret != 1:
                    return _errors
                elif ret == 1:
                    try:
                        if operation == "cut":
                            shutil.rmtree(ff)
                    except Exception as E:
                        _errors += str(E)+"\n"
                        return _errors
                    return 1
        elif stat.S_ISREG(mode):
            if _signal:
                _signal.propList = ["PULSE_COPY",os.path.basename(ff)]
            # 
            if not os.path.exists(dest_path):
                ret = on_copy_file2(dest_path, ff, _overwrite)
                if ret != 1:
                    _errors += "Error: {}".format(os.path.basename(ff))
                    return _errors
                elif ret == 1:
                    try:
                        if operation == "cut":
                            os.unlink(ff)
                    except Exception as E:
                        _errors += str(E)+"\n"
                        return _errors
                    return 1
            else:
                # it is the same file, make a copy
                try:
                    if operation == "cut":
                        _errors += "Error {}: same file.".format(os.path.basename(ff)) 
                        return _errors
                    ret = on_copy_file2(dest_path, ff, _overwrite)
                    if ret != 1:
                        _errors += "Error: {}".format(os.path.basename(ff))
                        return _errors
                except Exception as E:
                    _errors += str(E)+"\n"
                    return _errors
                return 1
        elif stat.S_ISLNK(mode):
            _signal.propList = ["PULSE_COPY",os.path.basename(ff)]
            if os.path.islink(dest_path) and os.path.exists(dest_path) == True:
                pathname = ff
                try:
                    link_to = os.readlink(pathname)
                    os.symlink(link_to, dest_path)
                    if operation == "cut":
                        os.unlink(ff)
                    return 1
                except Exception as E:
                    _errors += str(E)+"\n"
                    return _errors
            else:
                # it is the same file, make a copy
                try:
                    if operation == "cut":
                        _errors += "Error {}: same file.".format(os.path.basename(ff)) 
                        return _errors
                    dest_path = add_link_sfx(dest_path)
                    ret = on_copy_file2(dest_path, ff, _overwrite)
                    if ret != 1:
                        _errors += "Error: {}".format(os.path.basename(ff))
                        return _errors
                except Exception as E:
                    _errors += str(E)+"\n"
                    return _errors
                return 1
        else:
            _signal.propList = ["PULSE_COPY",os.path.basename(ff)]
            _errors += "Unknown or unsupported item: {}\n".format(ff)
            return _errors
    except Exception as E:
        _errors += "Error: {}".format(str(E))
        
import time
# 
class CopyThread(Thread):
    def __init__(self, path_source,_dest,_operation, _signal, _event, _overwrite):
        self.path_source = path_source
        self._dest = _dest
        self._operation = _operation
        self._signal = _signal
        self._event = _event
        self._overwrite = _overwrite
        self.run()
        
    def run(self):
        for ff in self.path_source:
            if self._event.is_set():
                self._signal.propList = ["COPY_ABORT"]
                return
            dest_path = os.path.join(self._dest, os.path.basename(ff))
            on_copy_file(dest_path, ff, self._operation, self._signal, self._overwrite)
            time.sleep(0.01)
        #
        if _errors != "":
            self._signal.propList = ["COPY_ERROR"]
        else:
            self._signal.propList = ["COPY_DONE"]
        
# def copy_file_function2(path_source,_dest,_operation,_event,_signal,_object,_same_item,_overwrite):
    # if "" in path_source:
        # path_source.remove("")
    # if "\x00" in path_source:
        # path_source.remove("\x00")
    # if _object != None:
        # #
        # num_items = len(path_source)
        # #
        # _event = Event()
        # #
        # def signal_threadslot_c(_signal,_param,num_items):
            # _list = _signal.propList[0]
            # if _list[0] == "PULSE_COPY":
                # _prev_value = _CD.prog_bar.get_fraction()
                # _next_value = float(_prev_value+(1/num_items))
                # _signal.propList = ["COPYD",[_list[1],_next_value]]
            # elif _list[0] == "COPY_DONE":
                # _CD.close_btn.set_sensitive(True)
                # _CD.cancel_btn.set_sensitive(False)
                # _signal.propList = ["COPYD_DONE",[_lang.DONE]]
            # elif _list[0] == "COPY_ERROR":
                # _CD.close_btn.set_sensitive(True)
                # _CD.cancel_btn.set_sensitive(False)
                # _signal.propList = ["COPYD_ERROR",[_lang.DONEWITHERRORS]]
                # _CD.error_set = 1
            # elif _list[0] == "COPY_ABORT":
                # _CD.close_btn.set_sensitive(True)
                # _CD.cancel_btn.set_sensitive(False)
                # _signal.propList = ["COPYD_ABORT",[_lang.ABORTEDBYUSER]]
        # _signalc = SignalObject()
        # _signalc.connect("notify::propList", signal_threadslot_c, num_items)
        # _CD = CopyDialog(self_main, _signalc, _event)
        # #
        # _object = Thread(target=CopyThread, args=(path_source,_dest,_operation,_signalc,_event,_overwrite), daemon=True)
        # _object.start()
        # #
        # _CD.present()
        # #
        # return _object

def CopyThread2(_d):
    path_source,_dest,_operation,_signal,_event,_overwrite = _d
    for ff in path_source:
        if _event.is_set():
            _signal.propList = ["COPY_ABORT"]
            return
        dest_path = os.path.join(_dest, os.path.basename(ff))
        on_copy_file(dest_path, ff, _operation, _signal, _overwrite)
        time.sleep(0.01)
    #
    if _errors != "":
        _signal.propList = ["COPY_ERROR"]
    else:
        _signal.propList = ["COPY_DONE"]
    return

def copy_file_function2(path_source,_dest,_operation,_event,_signal,_object,_same_item,_overwrite):
    if "" in path_source:
        path_source.remove("")
    if "\x00" in path_source:
        path_source.remove("\x00")
    if _object != None:
        #
        num_items = len(path_source)
        #
        _event = Event()
        #
        def signal_threadslot_c(_signal,_param,num_items):
            _list = _signal.propList[0]
            if _list[0] == "PULSE_COPY":
                _prev_value = _CD.prog_bar.get_fraction()
                _next_value = float(_prev_value+(1/num_items))
                _signal.propList = ["COPYD",[_list[1],_next_value]]
            elif _list[0] == "COPY_DONE":
                _CD.close_btn.set_sensitive(True)
                _CD.cancel_btn.set_sensitive(False)
                _signal.propList = ["COPYD_DONE",[_lang.DONE]]
            elif _list[0] == "COPY_ERROR":
                _CD.close_btn.set_sensitive(True)
                _CD.cancel_btn.set_sensitive(False)
                _signal.propList = ["COPYD_ERROR",[_lang.DONEWITHERRORS]]
                _CD.error_set = 1
            elif _list[0] == "COPY_ABORT":
                _CD.close_btn.set_sensitive(True)
                _CD.cancel_btn.set_sensitive(False)
                _signal.propList = ["COPYD_ABORT",[_lang.ABORTEDBYUSER]]
        _signalc = SignalObject()
        _signalc.connect("notify::propList", signal_threadslot_c, num_items)
        _CD = CopyDialog(self_main, _signalc, _event)
        #
        # _object = Thread(target=CopyThread, args=(path_source,_dest,_operation,_signalc,_event,_overwrite), daemon=True)
        # _object.start()
        ########
        _object = GLib.Thread.new(None, CopyThread2, (path_source,_dest,_operation,_signalc,_event,_overwrite))
        #######
        #
        _CD.present()
        #
        return _object

def copy_file_function(path_source,_dest,_operation,_event,_signal,_object,_same_item):
    there_same_item = 0
    # check whether there is some items with the same name at destination
    for el in path_source[:]:
        if el == "":
            path_source.remove("")
            continue
        if os.path.exists(os.path.join(_dest, os.path.basename(el))):
            if os.path.dirname(el) != _dest:
                there_same_item = 1
                break
    _result = None
    if there_same_item == 1:
        _OB = OBDial(self_main, _result)
        def dialog_action(_obj, _res, _data):
            # 0 yes overwrite - 1 no backup
            _result = _obj.choose_finish(_res)
            if _result == 0:
                copy_file_function2(path_source,_dest,_operation,_event,_signal,_object,_same_item,_overwrite=1)
            elif _result == 1:
                copy_file_function2(path_source,_dest,_operation,_event,_signal,_object,_same_item,_overwrite=0)
        _OB.choose(self_main, None, dialog_action, _result)
    else:
        copy_file_function2(path_source,_dest,_operation,_event,_signal,_object,_same_item,_overwrite=0)

##############

# overwrite/backup dialog
class OBDial(Gtk.AlertDialog):
    def __init__(self, _parent, _data):
        super().__init__()
        self._parent = _parent
        self._data = _data
        self._str1 = _lang.FILEOVERWRITE+"?"
        self._str2 = _lang.FILEWITHBACKUP
        #
        self.set_buttons([_lang.YES, _lang.NO])
        self.props.cancel_button = 1
        #
        self.set_message(self._str1)
        self.set_detail(self._str2)

def on_app_activated(_w, _appinfo, _ff, _APP):
    _appinfo.launch([_ff], None)
    _APP.close()

# _path is the dir - _file is the file name
def on_choose_app(_path, _file):
    _ff = Gio.File.new_for_path(os.path.join(_path, _file))
    DAC = Gtk.AppChooserDialog.new(self_main, Gtk.DialogFlags.MODAL, _ff)
    DAC.set_size_request(-1,400)
    DAC.get_widget().set_show_default(True)
    DAC.get_widget().connect("application-activated", on_app_activated, _ff, DAC)
    dac_box = DAC.get_content_area() # vertical
    box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    dac_box.append(box2)
    _btn = Gtk.Button(label=_lang.SETCONTENTTYPE)
    _btn.set_hexpand(True)
    def on_set_as_default_app(w):
        content_type = DAC.get_content_type()
        DAC.get_app_info().set_as_default_for_type(content_type)
    _btn.connect("clicked", on_set_as_default_app)
    box2.append(_btn)
    
    def on_response(_dialog, _responseid):
        if _responseid == Gtk.ResponseType.OK:
            DAC.get_app_info().launch([_ff], None)
            _dialog.destroy()
        elif _responseid == Gtk.ResponseType.CANCEL:
            _dialog.destroy()
    DAC.connect("response", on_response)
    DAC.set_visible(True)
    
#############

class ItemBox(Gtk.Box):
    def __init__(self, _parent, _item):
        super().__init__()
        self._parent = _parent
        self._item = _item # gtk.listitem
        self.item_name = None
        
        def on_sel(__item, __gparam, c=None):
            # it is none when change path
            item_to_add = self
            if __item.get_selected() == True:
                if item_to_add not in self._parent.SELECTED_WIDGET:
                    self._parent.SELECTED_WIDGET.append(item_to_add)
                    self._parent.SELECTED_ITEMS.append(self.item_name)
            else:
                if item_to_add in self._parent.SELECTED_WIDGET:
                    self._parent.SELECTED_WIDGET.remove(item_to_add)
                if self.item_name in self._parent.SELECTED_ITEMS:
                    self._parent.SELECTED_ITEMS.remove(self.item_name)
        self._item.connect("notify::selected", on_sel)
        #
        self._path = self._parent._path
        #
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(BOX_INTERNAL_SPACING)
        self.set_size_request(BOX_SIZE_W,BOX_SIZE_H)
        #
        icon = Gtk.Image.new()
        icon.set_pixel_size(ICON_SIZE)
        self.icon = icon
        self.append(icon)
        #
        self.lbl = Gtk.Label(wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR, lines=3, max_width_chars=12,
                        ellipsize=Pango.EllipsizeMode.MIDDLE, justify=Gtk.Justification.CENTER,
                        halign=Gtk.Align.CENTER, valign=Gtk.Align.START)
        self.append(self.lbl)
        #
        # mouse motion
        event_controller = Gtk.EventControllerMotion.new()
        event_controller.connect("enter", self.on_enter)
        event_controller.connect("leave", self.on_leave)
        self.add_controller(event_controller)
        #############
        #
        self.ctrl_pressed = 0
        self.shift_pressed = 0
        self.escape_pressed = 0
        # keyboard
        keycontroller = Gtk.EventControllerKey()
        keycontroller.connect('key-pressed', self.on_key_pressed)
        keycontroller.connect('key-released', self.on_key_released)
        self.add_controller(keycontroller)
        # right button
        self._gesture_r = Gtk.GestureClick.new()
        self._gesture_r.set_button(3)
        self.add_controller(self._gesture_r)
        self._gesture_r.connect('pressed', self.on_gesture_r)
        self.right_click_setted = 0
        ## main - dragging
        self.isDragging = 0
        self.dragging_prepare = 0
        self.drag_begin = 0
        drag_controller = Gtk.DragSource()
        drag_controller.connect("prepare", self.on_drag_prepare)
        drag_controller.connect("drag-begin", self.on_drag_begin)
        drag_controller.connect("drag-end", self.on_drag_end)
        self.add_controller(drag_controller)
        # drop
        self.drop_controller = Gtk.DropTarget.new(type=GObject.TYPE_NONE, actions=Gdk.DragAction.COPY)
        self.drop_controller.set_gtypes([self, Gdk.FileList, str])
        self.drop_controller.connect("drop", self.on_drop)
        self.add_controller(self.drop_controller)
        
    def on_get_symlink(self):
        if self._item.get_item() != None:
            print("IS SYMLINK ITEMBOX:: ", self._item.get_item().get_is_symlink())
    
    def on_gesture_r(self, o,n,x,y):
        num_items = 0
        num_selected_items = len(self._parent.SELECTED_WIDGET)
        if num_selected_items == 0 or self not in self._parent.SELECTED_WIDGET:
            self.select_this_unselect_others()
            num_items = 1
        elif num_selected_items == 1:
            num_items = 1
        elif num_selected_items > 1:
            num_items = num_selected_items
        # window - box
        _popover = WinPopover(self._parent,self,self._parent._path,num_items,[x,y])
        
    def on_key_pressed(self, event, keyval, keycode, state):
        if keyval == Gdk.KEY_Control_L or keyval == Gdk.KEY_Control_R:
            self.ctrl_pressed = 1
        elif keyval == Gdk.KEY_Shift_L or keyval == Gdk.KEY_Shift_R:
            self.shift_pressed = 1
        # elif keyval == Gdk.KEY_Escape:
            # self.escape_pressed = 1
    
    def on_key_released(self, event, keyval, keycode, state):
        self.ctrl_pressed = 0
        self.shift_pressed = 0
        self.escape_pressed = 0
    
    def select_this_unselect_others(self):
        _mod = self._parent.grid1.get_model()
        # set selection and unselect the others
        for i in range(_mod.get_n_items()):
            # gio.fileinfo
            f_info = _mod.get_item(i)
            if i == self._item.get_position():
                if f_info.get_name() == self.lbl.get_label():
                    # remove all
                    self._parent.SELECTED_WIDGET = [] 
                    self._parent.SELECTED_ITEMS = []
                    #
                    _mod.select_item(i, True)
                    break
    
    def on_drag_prepare(self, ctrl, _x, _y, data=None):
        self.dragging_prepare = 1
        __item_pos = self._item.get_position()
        # # unselect all if this item is not selected
        # and select this item
        if self._item.get_selected() == False:
            self.select_this_unselect_others()
        #
        SELECTED_ITEMS = []
        _data = ""
        _mod = self._parent.grid1.get_model()
        # get selected
        _n_items = _mod.get_n_items()
        for i in range(_n_items):
            if _mod.is_selected(i):
                # gfileinfo
                _fi = _mod.get_item(i)
                full_path = os.path.join(self._path,_fi.get_name())
                _fg = Gio.File.new_for_path(full_path)
                file_uri = _fg.get_uri()
                SELECTED_ITEMS.append(file_uri)
                _data += (file_uri+"\n")
        if len(SELECTED_ITEMS) == 0:
            return None
        _data = _data[:-1]+"\r\n"
        #
        if self.shift_pressed == 1:
            ctrl.set_actions(Gdk.DragAction.MOVE)
        elif self.shift_pressed == 0:
            ctrl.set_actions(Gdk.DragAction.COPY)
        gbytes = GLib.Bytes.new(bytes(_data, 'utf-8'))
        _atom = "text/uri-list"
        content = Gdk.ContentProvider.new_for_bytes(_atom, gbytes)
        return content
    
    def on_drag_begin(self, ctrl, drag):
        self.drag_begin = 1
        #
        if len(self._parent.SELECTED_WIDGET) == 1:
            if self._parent.SELECTED_WIDGET[0] == self:
                n_ic = None
                ########
                _icon = self.icon # gtk.image
                texture = _icon.get_paintable()
                if texture == None:
                    for ic in _icon.get_gicon().get_names():
                        if icon_theme.has_icon(ic):
                            n_ic = icon_theme.lookup_icon(ic, [], DRAG_ICON_SIZE, 1, 0, Gtk.IconLookupFlags.FORCE_REGULAR)
                            break
                    if n_ic:
                        ctrl.set_icon(n_ic, 0, 0) # paintable
                else:
                    __w = texture.get_width()
                    __h = texture.get_height()
                    if __h > __w:
                        __w = int(DRAG_ICON_SIZE*__w/__h)
                        __h = DRAG_ICON_SIZE 
                    elif __w > __h:
                        t_rx = __w/__h
                        __w = DRAG_ICON_SIZE
                        __h = int(DRAG_ICON_SIZE/t_rx)
                    else:
                        __w = DRAG_ICON_SIZE
                        __h = DRAG_ICON_SIZE
                    _snapshot = Gtk.Snapshot.new()
                    size_rect = Graphene.Rect()
                    size_rect.init(0,0,__w,__h)
                    _snapshot.append_scaled_texture(texture, 0, size_rect)
                    _rs = Graphene.Size()
                    _rs.init(__w,__h)
                    texture = _snapshot.to_paintable(_rs)
                    ctrl.set_icon(texture, 0, 0) # paintable
        elif len(self._parent.SELECTED_WIDGET) > 1:
            _texture = Gdk.Texture.new_from_filename(os.path.join(HOME_CONFIG,"icons","items_multi.png"))
            snapshot = Gtk.Snapshot.new()
            _bounds = Graphene.Rect.alloc()
            _bounds.init(0, 0, DRAG_ICON_SIZE, DRAG_ICON_SIZE)
            snapshot.append_scaled_texture(_texture, 0, _bounds)
            paintable = snapshot.to_paintable(None)
            ctrl.set_icon(paintable, 0, 0) # paintable
    
    def on_drag_end(self, ctrl, drag, data=None):
        self.isDragging = 0
        self.dragging_prepare = 0
        self.drag_begin = 0
    
    # dropping items in this program
    # _source: [__gi__.GLocalFile] - _dest: "destination_directory" - _operation: copy cut
    def on_copy_cup_operation(self,_source,_dest,_operation):
        path_source = []
        for ff in _source:
            path_source.append(ff.get_path())
        thread_object = object
        _thread = copy_file_function(path_source,_dest,_operation, None, None, thread_object, 0)
        
    def on_drop(self, ctrl, value, _x, _y):
        _operation = ""
        if  ctrl.get_actions() == Gdk.DragAction.COPY:
            _operation = "copy"
        elif ctrl.get_actions() == Gdk.DragAction.MOVE:
            _operation = "cut"
        
        if self.ctrl_pressed == 1:
            _operation = "cut"
        
        if _operation == "":
            return
        #
        if isinstance(value, Gdk.FileList) and value != []:
            files = value.get_files()
            self.cancel_op = -1
            OW = None
            ##########
            _dest = os.path.join(self._path, self.item_name)
            mode = os.lstat(_dest).st_mode
            if stat.S_ISDIR(mode):
                # exactly the same directory
                if files[0].get_path() == _dest:
                    return
                # from same directory
                if os.path.dirname(files[0].get_path()) == os.path.dirname(_dest):
                    self.copy_move_from_same_dir(files, _dest, _operation)
                # from other directory
                else:
                    self.on_copy_cup_operation(files, _dest, _operation)
            return
    
    def copy_move_from_same_dir(self, files, _dest, _operation):
        popover = Gtk.PopoverMenu()
        popover.set_autohide(True)
        popover.set_has_arrow(False)
        popover.set_halign(Gtk.Align.START)
        popover.set_parent(self)
        #
        # The 'File' menu items
        file_menu = Gio.Menu()
        action_group = Gio.SimpleActionGroup()
        #
        file_menu.append(_lang.COPY, 'win.Copy')
        button_copy = Gio.SimpleAction(name="Copy", parameter_type=None, enabled=True)
        button_copy.connect("activate", self.on_copy_move, files, _dest, "copy", popover)
        action_group.add_action(button_copy)
        #
        file_menu.append(_lang.MOVE, 'win.Move')
        button_move = Gio.SimpleAction(name="Move", parameter_type=None, enabled=True)
        button_move.connect("activate", self.on_copy_move, files, _dest, "cut", popover)
        action_group.add_action(button_move)
        #
        popover.insert_action_group('win', action_group)
        popover.set_menu_model(file_menu)
        #
        popover.popup()
        
    def on_copy_move(self, w, param, files, _dest, _operation, _p):
        _p.popdown()
        self.on_copy_cup_operation(files, _dest, _operation)
    
    def on_enter(self, _c, _x, _y) -> bool:
        self._parent.is_inside = True
        #
        _lt = self.lbl.get_layout()
        if _lt is not None:
            is_truncated = _lt.is_ellipsized()
            if is_truncated:
                self.lbl.set_tooltip_text(self.lbl.get_label())
        return True
    
    def on_leave(self, _c) -> bool:
        # notify the main program
        self._parent.is_inside = False
        return True
    
# class DeleteThread(Thread):
    # def __init__(self, path_source, _signal, _event):
        # self.path_source = path_source
        # self._signal = _signal
        # self._event = _event
        # self.run()
        # 
    # def run(self):
        # global _errors
        # for ff in self.path_source:
            # time.sleep(0.01)
            # if self._event.is_set():
                # self._signal.propList = ["DELETE_ABORT"]
                # return
            # #
            # self._signal.propList = ["PULSE_COPY",os.path.basename(ff)]
            # mode = os.lstat(ff).st_mode
            # if stat.S_ISDIR(mode):
                # try:
                    # shutil.rmtree(ff)
                # except Exception as E:
                    # _errors += str(E)
            # elif stat.S_ISREG(mode) or stat.S_ISLNK(mode):
                # try:
                    # os.unlink(ff)
                # except Exception as E:
                    # _errors += str(E)
            # else:
                # _errors += "{}: {}".format(FILENOTSUPPORTED, os.path.basename(ff))
        # #
        # if _errors != "":
            # self._signal.propList = ["DELETE_ERROR"]
        # else:
            # self._signal.propList = ["DELETE_DONE"]

class OWD(Gtk.AppChooserDialog):
    def __init__(self, _parent, _file):
        super().__init__()
        self._parent = _parent
        self._file = _file
        #
        self.set_transient_for(self._parent)
        self.set_modal(True)
        self.set_destroy_with_parent(True)
        self.set_size_request(-1, 400)
        # vertical box
        self.main_box = self.get_content_area()
        #
        self.box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.box2.set_hexpand(True)
        self.main_box.append(self.box2)
        #
        lbl = Gtk.Label(label="ciao")
        self.box2.append(lbl)
        #
        self.present()

class WinPopover(Gtk.PopoverMenu):
    # parent: window - widget: box or scrollwindow - type: 1 one item - >1 more than one item - -99 background
    def __init__(self, _parent, _widget, _path, _type, _pos):
        super().__init__()
        self._parent = _parent # srollwindow
        self._widget = _widget # itembox
        self._path = _path # parent folder
        self._type = _type
        self._pos = _pos # [x,y]
        self.set_has_arrow(False)
        self.set_halign(Gtk.Align.START)
        self.set_parent(self._widget)
        #####################
        # The main menu
        self.file_menu = Gio.Menu.new()
        action_group = Gio.SimpleActionGroup()
        self.insert_action_group('win', action_group)
        self.set_menu_model(self.file_menu)
        
        if self._type == 1:
            # open in a new tab
            item_name = self._widget.item_name
            _file = os.path.join(self._path, item_name)
            if os.path.isdir(_file):
                self.file_menu.append(_lang.OPENFOLDERNEWTAB, 'win.OpenFolderTab')
                button_oftab = Gio.SimpleAction(name="OpenFolderTab", parameter_type=None, enabled=True)
                button_oftab.connect("activate", self.on_open_folder_tab, _file)
                action_group.add_action(button_oftab)
        
        if self._type == -99:
            # new folder
            self.file_menu.append(_lang.NEWFOLDER, 'win.NewFolder')
            button_nf = Gio.SimpleAction(name="NewFolder", parameter_type=None, enabled=True)
            button_nf.connect("activate", self.on_new_folder)
            action_group.add_action(button_nf)
            ##### new file
            doc_submenu = Gio.Menu.new()
            self.file_menu.append_submenu(_lang.NEWDOCUMENT, doc_submenu)
            menuitem_txt = Gio.MenuItem.new_submenu(_lang.NEWTEXTFILE, doc_submenu)
            #
            doc_action_group = Gio.SimpleActionGroup()
            self.insert_action_group('win2', doc_action_group)
            #
            doc_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_TEMPLATES)
            def on_new_file(action, param, _d, ff):
                try:
                    dest_path = os.path.join(self._path, _d)
                    ret = on_copy_file2(dest_path, ff, 0)
                    if isinstance(ret, str):
                        global _errors
                        AlDial(self_main, str(E))
                        _errors = ""
                except Exception as E:
                    AlDial(self_main, str(E))
            #
            if os.path.exists(doc_dir):
                doc_list = os.listdir(doc_dir)
                if len(doc_list) > 0:
                    for _d in doc_list[::-1]:
                        doc_submenu.append(os.path.splitext(_d)[0], 'win2.{}'.format(_d.replace(" ","_")))
                        button_txt = Gio.SimpleAction(name=_d.replace(" ","_"), parameter_type=None, enabled=True)
                        button_txt.connect("activate", on_new_file, _d, os.path.join(doc_dir, _d))
                        #
                        doc_action_group.add_action(button_txt)
        # open and open with...
        if self._type == 1:
            self.file_menu.append(_lang.OPENWITHAPP, 'win.OpenWithApp')
            button_owa = Gio.SimpleAction(name="OpenWithApp", parameter_type=None, enabled=True)
            button_owa.connect("activate", self.on_openwith_app, self._widget.item_name)
            action_group.add_action(button_owa)
            
            # self.file_menu.append(_lang.OPENWITH, 'win.OpenWith')
            # button_ow = Gio.SimpleAction(name="OpenWith", parameter_type=None, enabled=True)
            # button_ow.connect("activate", self.on_openwith, self._widget.item_name)
            # action_group.add_action(button_ow)
            
            openwith_submenu = Gio.Menu.new()
            self.file_menu.append_submenu(_lang.OPENWITH, openwith_submenu)
            app_action_group = Gio.SimpleActionGroup()
            self.insert_action_group('win3', app_action_group)
            #
            item_name = self._widget.item_name
            _file = os.path.join(self._path, item_name)
            # [[appinfo], is_default_appinfo]
            app_items = self._open_with_items(Gio.File.new_for_path(_file))
            if app_items:
                fapps = app_items[0]
                is_default = app_items[1]
                # gio.appinfo
                is_default_name = is_default.get_display_name()
                for fapp in fapps:
                    if isinstance(is_default, Gio.AppInfo):
                        _label = fapp.get_display_name().split("_")[0]
                        pre_label = _label.replace(" ", "_").replace("=","_").replace("(","_").replace(")","_")
                        if _label == is_default_name:
                            _label += " "+_lang.FAPPDEFAULT
                            openwith_submenu.insert(0, _label, 'win3.{}'.format(pre_label))
                        else:
                            openwith_submenu.append(_label, 'win3.{}'.format(pre_label))
                        if _label:
                            button_app = Gio.SimpleAction(name=pre_label, parameter_type=None, enabled=True)
                            button_app.connect("activate", self.on_app_exec, fapp, _file)
                            app_action_group.add_action(button_app)
            # dialog
            openwith_submenu.append(_lang.OPENWITH, 'win3.OpenWith')
            button_ow = Gio.SimpleAction(name="OpenWith", parameter_type=None, enabled=True)
            button_ow.connect("activate", self.on_openwith, self._widget.item_name)
            app_action_group.add_action(button_ow)
        # exec
        if self._type == 1:
            item_name = self._widget.item_name
            _file = os.path.join(self._path, item_name)
            if os.path.isfile(_file) and os.access(_file, os.X_OK):
                def _execute_file(action, param, _f, _p):
                    _p.popdown()
                    try:
                        subprocess.Popen([_f])
                    except Exception as E:
                        AlDial(self_main, str(E))
                self.file_menu.append(_lang.FEXECUTE, 'win.Execute')
                button_execute = Gio.SimpleAction(name="Execute", parameter_type=None, enabled=True)
                button_execute.connect("activate", _execute_file, _file, self)
                action_group.add_action(button_execute)
        # items
        if self._type != -99:
            # copy items
            self.file_menu.append(_lang.COPY, 'win.Copy')
            button_copy = Gio.SimpleAction(name="Copy", parameter_type=None, enabled=True)
            button_copy.connect("activate", self.on_copy, "copy")
            action_group.add_action(button_copy)
            # cut items
            self.file_menu.append(_lang.CUT, 'win.Cut')
            button_copy = Gio.SimpleAction(name="Cut", parameter_type=None, enabled=True)
            button_copy.connect("activate", self.on_copy, "cut")
            action_group.add_action(button_copy)
        # Open in terminal
        if self._type == -99:
            self.file_menu.append(_lang.TERMINAL, 'win.Terminal')
            button_term = Gio.SimpleAction(name="Terminal", parameter_type=None, enabled=True)
            button_term.connect("activate", self._widget.on_terminal, self._path, self)
            action_group.add_action(button_term)
        if self._type == 1:
            try: # e.g. not accessible item
                ff = os.path.join(self._path, self._widget.item_name)
                mode = os.lstat(ff).st_mode
                if stat.S_ISDIR(mode):
                    self.file_menu.append(_lang.TERMINAL, 'win.Terminal')
                    self.button_term = Gio.SimpleAction(name="Terminal", parameter_type=None, enabled=True)
                    self.button_term.connect("activate", self._parent.on_terminal, ff)
                    action_group.add_action(self.button_term)
            except:
                pass
        # paste items
        if self._type == -99:
            self.file_menu.append(_lang.PASTE, 'win.Paste')
            self.button_paste = Gio.SimpleAction(name="Paste", parameter_type=None, enabled=False)
            self.button_paste.connect("activate", self.on_paste_function)
            action_group.add_action(self.button_paste)
            _atom = "x-special/gnome-copied-files"
            clipboard.read_async([_atom],1,None,self.get_data_paste,self)
        # only one item selected
        if self._type == 1:
            self.file_menu.append(_lang.RENAME, 'win.Rename')
            button_rename = Gio.SimpleAction(name="Rename", parameter_type=None, enabled=True)
            button_rename.connect("activate", self.on_rename)
            action_group.add_action(button_rename)
        # one or more items selected
        if self._type > 0:
            self.file_menu.append(_lang.DELETE, 'win.Delete')
            button_remove = Gio.SimpleAction(name="Delete", parameter_type=None, enabled=True)
            button_remove.connect("activate", self.on_remove)
            action_group.add_action(button_remove)
            # only for HOME
            if self._path[0:len(_HOME)] == _HOME:
                self.file_menu.append(_lang.TRASHCAN, 'win.Trash')
                button_trash = Gio.SimpleAction(name="Trash", parameter_type=None, enabled=True)
                # button_trash.connect("activate", self.on_trash)
                button_trash.connect("activate", self._parent.on_trash)
                action_group.add_action(button_trash)
        # scripts
        if self._type > 0:
            _list_dir = os.listdir(SCRIPTS_DIRECTORY)
            for el in _list_dir:
                if os.access(os.path.join(SCRIPTS_DIRECTORY,el), os.X_OK):
                    self.file_menu.append(el, 'win.{}'.format(el))
                    btn_script = Gio.SimpleAction(name=el, parameter_type=None, enabled=True)
                    btn_script.connect("activate", self.on_script, os.path.join(SCRIPTS_DIRECTORY,el))
                    action_group.add_action(btn_script)
        # property dialog
        self.file_menu.append(_lang.PROPERTY, 'win.Property')
        button_property = Gio.SimpleAction(name="Property", parameter_type=None, enabled=True)
        button_property.connect("activate", self.on_property)
        action_group.add_action(button_property)
        # background
        # if self._type == -99:
        _rect = Gdk.Rectangle()
        _rect.x = self._pos[0]
        _rect.y = self._pos[1]
        _rect.width = 1
        _rect.height = 1
        self.set_pointing_to(_rect)
        self.popup()
        
    def _open_with_items(self, _gfile):
        items = []
        is_default = None
        if _gfile != None:
            _info = _gfile.query_info("standard::content-type", 0, None)
            content_type = _info.get_content_type() or ""
            default = False
            if content_type:
                if is_default == None:
                    is_default = Gio.AppInfo.get_default_for_type(content_type, False)
                for app in Gio.AppInfo.get_all_for_type(content_type): #if ct else []:
                    if app == is_default:
                        items.insert(0, app)
                    else:
                        items.append(app)
        return [items, is_default]
        
    def on_app_exec(self, action, param, fapp, _file):
        try:
            ret = fapp.launch([Gio.File.new_for_path(_file)], None)
            if ret == False:
                AlDial(self_main, _lang.FAPPERROR)
        except Exception as E:
            AlDial(self_main, str(E))
        
    def on_open_folder_tab(self, action, param, item_path):
        sw = ScrolWin(item_path, self._parent._parent)
        sw.grid1.grab_focus()
        if sw != None:
            idx = self._parent._parent._notebook.append_page(sw, sw.tab_label)
            self._parent._parent._notebook.set_tab_reorderable(sw, True)
            self._parent._parent._notebook.set_current_page(idx)
        
    def on_new_folder(self, action, param):
        WD = RenDialog(self_main, 2, _lang.CHOOSENEWNAME, self._path)
    
    def on_openwith_app(self, action, param, _file):
        new_path = os.path.join(self._path, _file)
        mode = os.lstat(new_path).st_mode
        is_link = stat.S_ISLNK(mode)
        if is_link:
            new_path = os.readlink(new_path)
        if stat.S_ISDIR(mode):
            self._parent._parent.trigger_path_update(new_path)
        elif stat.S_ISREG(mode) or is_link:
            _fl = Gtk.FileLauncher.new(Gio.File.new_for_path(new_path))
            def on_launch_cb(_obj, _res, _d):
                try:
                    ret = _obj.launch_finish(_res)
                    if ret == False:
                        AlDial(self_main, _fi.get_name())
                except GLib.Error as gerr:
                    AlDial(self_main, "{}\n{}".format(_fi.get_name(), gerr.message))
            _fl.launch(None,None,on_launch_cb,None)
    
    def on_openwith(self, action, param, _file):
        on_choose_app(self._path, _file)
    
    # def on_terminal(self, action, param, _path):
        # try:
            # subprocess.run([TERMINAL, "{}{}".format(TERMINAL_ARG,_path)])
        # except Exception as E:
            # AlDial(self_main, str(E))
    
    def on_script(self, action, param, _script):
        self.popdown()
        _list = ""
        _path = self._parent._path
        for el in self._parent.SELECTED_ITEMS:
            _list += os.path.join(_path, el)+"\n"
        try:
            subprocess.run([_script, "{}".format(_list)])
            # ret = GLib.spawn_sync(None, [_script, "{}".format(_list), "&"], None, GLib.SpawnFlags.DEFAULT, None, None)
            # if ret[0] == False:
                # AlDial(self_main, _lang.FAPPERROR)
        except:
            pass
        
    def on_property(self, action, param):
        if self._type > 0:
            LIST_SELECTED = []
            ITEM_SELECTED = []
            model = self._parent.grid1.get_model()
            num_items = model.get_n_items()
            items_selected = 0
            item_not_readable = 0
            for i in range(num_items):
                if model.is_selected(i):
                    items_selected += 1
                    # gio.fileinfo
                    f_info = model.get_item(i)
                    f_name = f_info.get_name()
                    ff = os.path.join(self._parent._path, f_name)
                    if not os.access(ff, os.R_OK):
                        item_not_readable += 1
                        # continue
                    if os.path.isdir(ff) and not os.path.islink(ff):
                        if not os.access(ff, os.X_OK):
                            item_not_readable += 1
                    #
                    LIST_SELECTED.append(ff)
                    ITEM_SELECTED.append(f_info)
            #
            if len(ITEM_SELECTED) > 0 and item_not_readable == 0:
                PropertyDialog(self, ITEM_SELECTED)
            else:
                AlDial(self_main, _lang.ITEMSNOTREADABLE)
        elif self._type == -99:
            current_path = self._parent._notebook.get_nth_page(self._parent._notebook.get_current_page())._path
            PropertyDialog(self, current_path)
        
    def on_copy(self, action, param, _type):
        self.popdown()
        _item = self._parent.SELECTED_ITEMS
        _data = "{}\n".format(_type)
        for el in _item:
            _f = os.path.join(self._widget._path, el)
            _f_uri = Gio.File.new_for_path(_f).get_uri()
            _data += _f_uri+"\n"
        _data += "\0"
        gbytes = GLib.Bytes.new(bytes(_data, 'utf-8'))
        _atom = "x-special/gnome-copied-files"
        content = Gdk.ContentProvider.new_for_bytes(_atom, gbytes)
        clipboard.set_content(content)
        
    def on_rename(self, action, param):
        self.popdown()
        if len(self._parent.SELECTED_WIDGET) == 1:
            _item = self._parent.SELECTED_WIDGET[0]
            WD = RenDialog(self_main, 1, _lang.CHOOSENEWNAME, _item)
        
    
    def on_remove(self, action, param):
        self.popdown()
        _YND = YNDial(self, _lang.DELETEQ, _lang.ITEMREMOVEDEVER)
        return
        
    def dialog_action(self, _obj, _res, _data=None):
        _result = _obj.choose_finish(_res)
        self._value = _result
        if _result == 1:
            return
        #
        LIST_SELECTED = []
        model = self._parent.grid1.get_model()
        num_items = model.get_n_items()
        for i in range(num_items):
            if model.is_selected(i):
                # gio.fileinfo
                f_info = model.get_item(i)
                f_name = f_info.get_name()
                ff = os.path.join(self._parent._path, f_name)
                LIST_SELECTED.append(ff)
        if len(LIST_SELECTED) > 0:
            num_items = len(LIST_SELECTED)
            _eventd = Event()
            def signal_threadslot_d(_signal,_param,num_items):
                _list = _signal.propList[0]
                if _list[0] == "PULSE_COPY":
                    _prev_value = _CD.prog_bar.get_fraction()
                    _next_value = float(_prev_value+(1/num_items))
                    _signal.propList = ["DELETED",[_list[1],_next_value]]
                elif _list[0] == "DELETE_DONE":
                    _CD.close_btn.set_sensitive(True)
                    _CD.cancel_btn.set_sensitive(False)
                    _signal.propList = ["DELETED_DONE",[_lang.DONE]]
                elif _list[0] == "DELETE_ERROR":
                    _CD.close_btn.set_sensitive(True)
                    _CD.cancel_btn.set_sensitive(False)
                    _signal.propList = ["DELETED_ERROR",[_lang.DONEWITHERRORS]]
                    _CD.error_set = 1
                elif _list[0] == "DELETE_ABORT":
                    _CD.close_btn.set_sensitive(True)
                    _CD.cancel_btn.set_sensitive(False)
                    _signal.propList = ["DELETED_ABORT",[_lang.ABORTEDBYUSER]]
            #
            _signald = SignalObject()
            _signald.connect("notify::propList", signal_threadslot_d, num_items)
            _CD = CopyDialog(self_main, _signald, _eventd)
            #
            # _object = Thread(target=DeleteThread, args=(LIST_SELECTED,_signald,_eventd), daemon=True)
            # _object.start()
            #
            _object = GLib.Thread.new(None, self.DeleteThread2, (LIST_SELECTED,_signald,_eventd))
            #
            _CD.present()
    
    def DeleteThread2(self, _d):
        path_source, _signal, _event = _d
        global _errors
        for ff in path_source:
            time.sleep(0.01)
            if _event.is_set():
                _signal.propList = ["DELETE_ABORT"]
                return
            #
            _signal.propList = ["PULSE_COPY",os.path.basename(ff)]
            mode = os.lstat(ff).st_mode
            if stat.S_ISDIR(mode):
                try:
                    shutil.rmtree(ff)
                except Exception as E:
                    _errors += str(E)
            elif stat.S_ISREG(mode) or stat.S_ISLNK(mode):
                try:
                    os.unlink(ff)
                except Exception as E:
                    _errors += str(E)
            else:
                _errors += "{}: {}".format(FILENOTSUPPORTED, os.path.basename(ff))
        #
        if _errors != "":
            _signal.propList = ["DELETE_ERROR"]
        else:
            _signal.propList = ["DELETE_DONE"]
        return
    
    # def on_trash(self, action, param, _a=None, _b=None):
        # # only home
        # can_trash = 0
        # if len(self._parent.SELECTED_ITEMS) > 0:
            # if self._path[0:len(_HOME)] == _HOME:
                # can_trash = 1
        # if can_trash:
            # ITEMS_TO_TRASH = []
            # for el in self._parent.SELECTED_ITEMS:
                # ITEMS_TO_TRASH.append(os.path.join(self._path, el))
            # TrashModule(ITEMS_TO_TRASH)
    
    def on_paste(self, action, param):
        self.popdown()
        _atom = "x-special/gnome-copied-files"
        clipboard.read_async([_atom],1,None,self.get_data_paste,self)
    
    def get_data_paste(self, obj, res, _d):
        try:
            _data = clipboard.read_finish(res)
        except Exception as E:
            return
        _atom = "x-special/gnome-copied-files"
        gio_input_stream = _data[0]
        outputStream = Gio.MemoryOutputStream.new_resizable()
        outputStream.splice_async(gio_input_stream,Gio.OutputStreamSpliceFlags.CLOSE_TARGET,GLib.PRIORITY_DEFAULT,None,self.on_get_data_paste, None)
    
    def on_get_data_paste(self, obj, res, _d):
        global _errors
        try:
            _data = obj.splice_finish(res)
            _dbytes = obj.steal_as_bytes()
            _list = _dbytes.get_data().decode("utf-8").split("\n")
            _errors = ""
            if len(_list) > 1:
                self.paste_list = _list
                self.button_paste.set_enabled(True)
            return
        except Exception as E:
            pass
        
    def on_paste_function(self, action, param):
        self.popdown()
        global _errors
        _list = self.paste_list
        _operation = _list[0]
        #
        path_source_tmp = _list[1:]
        path_source = [unquote(x)[7:] for x in path_source_tmp]
        _dest = self._path
        thread_object = object
        _thread = copy_file_function(path_source,_dest,_operation, None, None, thread_object, 1)


class PropertyDialog(Gtk.Window):
    def __init__(self, _parent, _list):
        super().__init__()
        self._parent = _parent
        self._list = _list
        if isinstance(self._list, list):
            self.set_transient_for(self._parent._parent._parent)
        elif isinstance(self._list, str):
            self.set_transient_for(self._parent._parent)
        self.set_modal(True)
        self.set_title(_lang.PROPERTY)
        self.set_resizable(True)
        self.set_default_size(PDWIDTH, 100)
        # 
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(self.headerbar)
        self.headerbar.set_show_title_buttons(False)
        #
        self.apply_btn = Gtk.Button(label=_lang.APPLY)
        self.apply_btn.connect("clicked", self.on_apply)
        #
        self.close_btn = Gtk.Button(label=_lang.CLOSE)
        self.close_btn.connect("clicked", self.on_close)
        self.headerbar.pack_end(self.close_btn)
        #
        self.set_destroy_with_parent(True)
        self.set_resizable(False)
        self.set_name("propertydialog")
        #
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(self.box)
        #
        prop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.box.append(prop_box)
        #
        self.exec_is_changed = False
        self.perm_is_changed = False
        # one or more than one item selected
        if isinstance(self._list, list):
            self.total_num_items_hiddens = 0
            # one item selected
            if len(self._list) == 1:
                gfile = self._list[0]
                file_name = gfile.get_name()
                file_type = gfile.get_content_type()
                if file_type == "inode/directory":
                    file_type = _lang.FOLDER
                dir_name = self._parent._parent._path
                self.file_path = os.path.join(dir_name, file_name)
                mode =  os.lstat(self.file_path).st_mode
                file_size = 0
                self.has_dir = 0
                self.total_num_items = 0
                if os.path.isdir(self.file_path) and not os.path.islink(self.file_path):
                    self.has_dir = 1
                    file_size = self.get_size(self.file_path)
                elif not os.path.islink(self.file_path):
                    file_size = gfile.get_size()
                    self.total_num_items += 1
                else:
                    self.total_num_items += 1
                #
                file_gicon = gfile.get_icon()
                _img = Gtk.Image.new_from_gicon(file_gicon)
                _img.set_pixel_size(64)
                prop_box.append(_img)
                #
                file_lbl = Gtk.Label(label="<b>"+file_name+"</b>")
                file_lbl.set_use_markup(True)
                file_lbl.props.halign = Gtk.Align.CENTER
                file_lbl.set_wrap(True)
                file_lbl.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
                file_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
                file_lbl.set_lines(5)
                prop_box.append(file_lbl)
                #
                type_lbl = Gtk.Label.new()
                prop_box.append(type_lbl)
                if gfile.get_is_symlink():
                    type_lbl.set_label("<i>"+_lang.ITEMTYPE+"</i> "+_lang.LINKTYPE)
                    type_lbl.set_use_markup(True)
                    link_to = os.readlink(self.file_path)
                    link_lbl = Gtk.Label(label="("+link_to+")")
                    link_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
                    prop_box.append(link_lbl)
                else:
                    type_lbl.set_label("<i>"+_lang.ITEMTYPE+"</i> "+file_type)
                    type_lbl.set_use_markup(True)
                #
                if os.path.isdir(self.file_path) and not os.path.islink(self.file_path):
                    size_lbl = Gtk.Label(label="<i>"+_lang.SIZEITEM+"</i> "+convert_size(file_size))
                    size_lbl.set_use_markup(True)
                    prop_box.append(size_lbl)
                    #
                    num_items_lbl = Gtk.Label(label="<i>{}</i> {}".format(_lang.NUMITEMS, self.total_num_items))
                    num_items_lbl.set_use_markup(True)
                    prop_box.append(num_items_lbl)
                elif not os.path.islink(self.file_path):
                    size_lbl = Gtk.Label(label="<i>"+_lang.SIZEITEM+"</i> "+convert_size(file_size))
                    size_lbl.set_use_markup(True)
                    prop_box.append(size_lbl)
                #
                _frame1 = Gtk.Frame.new(label=None)
                prop_box.append(_frame1)
                box_frame1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                _frame1.set_child(box_frame1)
                #
                access_dt = gfile.get_access_date_time().format("%x %X")
                access_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                access_box.set_hexpand(True)
                access_lbl = Gtk.Label(label="<i>{} </i>".format(_lang.ACCESS))
                access_lbl.props.halign = Gtk.Align.END
                access_lbl.set_hexpand(True)
                access_lbl.set_use_markup(True)
                access_box.append(access_lbl)
                access_lbl2 = Gtk.Label(label=access_dt)
                access_lbl2.props.halign = Gtk.Align.START
                access_box.append(access_lbl2)
                box_frame1.append(access_box)
                # 
                modified_dt = gfile.get_modification_date_time().format("%x %X")
                modified_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                modified_box.set_hexpand(True)
                modified_lbl = Gtk.Label(label="<i>{} </i>".format(_lang.MODIFICATION))
                modified_lbl.props.halign = Gtk.Align.END
                modified_lbl.set_hexpand(True)
                modified_lbl.set_use_markup(True)
                modified_box.append(modified_lbl)
                modified_lbl2 = Gtk.Label(label=modified_dt)
                modified_lbl2.props.halign = Gtk.Align.START
                modified_box.append(modified_lbl2)
                box_frame1.append(modified_box)
                # 
                creation_dt = gfile.get_creation_date_time().format("%x %X")
                creation_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                creation_box.set_hexpand(True)
                creation_lbl = Gtk.Label(label="<i>{} </i>".format(_lang.CREATION))
                creation_lbl.props.halign = Gtk.Align.END
                creation_lbl.set_hexpand(True)
                creation_lbl.set_use_markup(True)
                creation_box.append(creation_lbl)
                creation_lbl2 = Gtk.Label(label=creation_dt)
                creation_lbl2.props.halign = Gtk.Align.START
                creation_box.append(creation_lbl2)
                #
                box_frame1.append(creation_box)
                #
                is_executable = os.access(self.file_path, os.X_OK)
                # executable or accessible checkbox
                if stat.S_ISREG(mode) or stat.S_ISLNK(mode):
                    self.chk_exec = Gtk.CheckButton.new_with_label(_lang.FILE_EXECUTABLE)
                    prop_box.append(self.chk_exec)
                    self.chk_exec.set_active(is_executable)
                    self.chk_exec.connect("toggled", self.on_chk_exec)
                elif stat.S_ISDIR(mode):
                    self.chk_exec = Gtk.CheckButton.new_with_label(_lang.FOLDER_ACCESS)
                    prop_box.append(self.chk_exec)
                    self.chk_exec.set_active(is_executable)
                    self.chk_exec.connect("toggled", self.on_chk_exec)
                #
                # PERMISSIONS
                file_stat = os.stat(self.file_path)
                file_mode = file_stat.st_mode
                file_perm = oct(file_mode & 0o777)[-3:]
                user_perm = file_perm[0]
                group_perm = file_perm[1]
                other_perm = file_perm[2]
                #
                _frame2 = Gtk.Frame.new(label=None)
                prop_box.append(_frame2)
                box_frame2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                _frame2.set_child(box_frame2)
                # recursive option if folder
                if stat.S_ISDIR(mode):
                    self.chk_recursive = Gtk.CheckButton.new_with_label(_lang.FOLDER_RECURSIVE)
                    box_frame2.append(self.chk_recursive)
                #
                boxuser = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0) 
                box_frame2.append(boxuser)
                path = Path(self.file_path)
                owner = path.owner()
                user_lbl = Gtk.Label(label=owner)
                user_lbl.set_hexpand(True)
                user_lbl.props.halign = Gtk.Align.START
                boxuser.append(user_lbl)
                self.dd_user = Gtk.DropDown.new_from_strings([_lang.PROPREADWRITE,_lang.PROPREAD,_lang.PROPWRITE,_lang.PROPFORBIDDEN])
                self.dd_user.props.halign = Gtk.Align.END
                self.on_dropdown_select(self.dd_user, user_perm)
                boxuser.append(self.dd_user)
                self.dd_user.connect("notify::selected", self.on_dropdown_changed)
                #
                boxgroup = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0) 
                box_frame2.append(boxgroup)
                group_lbl = Gtk.Label(label=_lang.ISGROUP)
                group_lbl.set_hexpand(True)
                group_lbl.props.halign = Gtk.Align.START
                boxgroup.append(group_lbl)
                self.dd_group = Gtk.DropDown.new_from_strings([_lang.PROPREADWRITE,_lang.PROPREAD,_lang.PROPWRITE,_lang.PROPFORBIDDEN])
                self.dd_group.props.halign = Gtk.Align.END
                self.on_dropdown_select(self.dd_group, group_perm)
                boxgroup.append(self.dd_group)
                self.dd_group.connect("notify::selected", self.on_dropdown_changed)
                #
                boxother = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0) 
                box_frame2.append(boxother)
                other_lbl = Gtk.Label(label=_lang.ISOTHER)
                other_lbl.set_hexpand(True)
                other_lbl.props.halign = Gtk.Align.START
                boxother.append(other_lbl)
                self.dd_other = Gtk.DropDown.new_from_strings([_lang.PROPREADWRITE,_lang.PROPREAD,_lang.PROPWRITE,_lang.PROPFORBIDDEN])
                self.dd_other.props.halign = Gtk.Align.END
                self.on_dropdown_select(self.dd_other, other_perm)
                boxother.append(self.dd_other)
                self.dd_other.connect("notify::selected", self.on_dropdown_changed)
                #
                self.headerbar.pack_start(self.apply_btn)
            # more than one item selected
            elif len(self._list) > 1:
                len_list = len(self._list)
                list_size = 0
                self.has_dir = 0
                self.total_num_items = 0
                self.not_owner = 0
                for el in self._list:
                    dir_name = self._parent._parent._path
                    file_name = el.get_name()
                    self.file_path = os.path.join(dir_name,file_name)
                    try:
                        path = Path(os.path.join(self._parent._parent._path,el.get_name()))
                        owner = path.owner()
                        if owner != GLib.get_user_name():
                            self.not_owner = 1
                            break
                    except Exception as E:
                        break
                    try:
                        if os.path.isdir(self.file_path) and not os.path.islink(self.file_path):
                            self.has_dir += 1
                            list_size += self.get_size(self.file_path)
                        elif not os.path.islink(self.file_path):
                            list_size += el.get_size()
                            self.total_num_items += 1
                        else:
                            self.total_num_items += 1
                    except:
                        pass
                #
                if self.not_owner == 0:
                    # number of items
                    nitem_lbl = Gtk.Label(label="<i>{}</i> {}".format(_lang.NUMITEMS, len_list))
                    nitem_lbl.set_use_markup(True)
                    prop_box.append(nitem_lbl)
                    #
                    item_size = Gtk.Label(label="<i>{}</i> {}".format(_lang.SIZEITEMS, convert_size(list_size)))
                    item_size.set_use_markup(True)
                    prop_box.append(item_size)
                    #
                    _frame1 = Gtk.Frame.new(label=None)
                    prop_box.append(_frame1)
                    box_frame1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                    _frame1.set_child(box_frame1)
                    #
                    message_lbl = Gtk.Label(label="<b>"+_lang.PERMNOTICE+"</b>")
                    message_lbl.set_use_markup(True)
                    box_frame1.append(message_lbl)
                    #
                    if self.has_dir < self.total_num_items:
                        self.chk_exec = Gtk.CheckButton.new_with_label(_lang.FILE_EXECUTABLE)
                        box_frame1.append(self.chk_exec)
                    # recursive option if one folder at least
                    if self.has_dir:
                        self.chk_recursive = Gtk.CheckButton.new_with_label(_lang.FOLDER_RECURSIVE)
                        box_frame1.append(self.chk_recursive)
                        self.chk_recursive.set_active(True)
                    #
                    boxuser = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0) 
                    box_frame1.append(boxuser)
                    user_lbl = Gtk.Label(label=owner)
                    user_lbl.set_hexpand(True)
                    user_lbl.props.halign = Gtk.Align.START
                    boxuser.append(user_lbl)
                    self.dd_user = Gtk.DropDown.new_from_strings([_lang.PROPREADWRITE,_lang.PROPREAD,_lang.PROPWRITE,_lang.PROPFORBIDDEN])
                    self.dd_user.props.halign = Gtk.Align.END
                    boxuser.append(self.dd_user)
                    #
                    boxgroup = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0) 
                    box_frame1.append(boxgroup)
                    group_lbl = Gtk.Label(label=_lang.ISGROUP)
                    group_lbl.set_hexpand(True)
                    group_lbl.props.halign = Gtk.Align.START
                    boxgroup.append(group_lbl)
                    self.dd_group = Gtk.DropDown.new_from_strings([_lang.PROPREADWRITE,_lang.PROPREAD,_lang.PROPWRITE,_lang.PROPFORBIDDEN])
                    self.dd_group.props.halign = Gtk.Align.END
                    boxgroup.append(self.dd_group)
                    #
                    boxother = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0) 
                    box_frame1.append(boxother)
                    other_lbl = Gtk.Label(label=_lang.ISOTHER)
                    other_lbl.set_hexpand(True)
                    other_lbl.props.halign = Gtk.Align.START
                    boxother.append(other_lbl)
                    self.dd_other = Gtk.DropDown.new_from_strings([_lang.PROPREADWRITE,_lang.PROPREAD,_lang.PROPWRITE,_lang.PROPFORBIDDEN])
                    self.dd_other.props.halign = Gtk.Align.END
                    boxother.append(self.dd_other)
                    #
                    self.headerbar.pack_start(self.apply_btn)
                else:
                    err_lbl = Gtk.Label(label=_lang.NOTOWNER)
                    prop_box.append(err_lbl)
        
        # background selected
        elif isinstance(self._list, str):
            folder_size = 0
            self.total_num_items = 0
            self.total_num_items_hiddens = 0
            _errors = ""
            try:
                folder_size = self.get_size(self._list)
            except Exception as E:
                _errors += str(E)
            #
            if _errors:
                AlDial(self_main, str(E))
            else:
                #
                _gfile = Gio.File.new_for_path(self._list)
                if icon_theme.has_icon("folder"):
                    file_icon = icon_theme.lookup_icon("folder", [], 64, 1, 0, Gtk.IconLookupFlags.FORCE_REGULAR)
                _img = Gtk.Image.new_from_paintable(file_icon)
                _img.set_pixel_size(64)
                prop_box.append(_img)
                #
                lbl_name = Gtk.Label(label="<b>"+os.path.basename(self._list)+"</b>")
                lbl_name.set_use_markup(True)
                prop_box.append(lbl_name)
                #
                if os.path.islink(self._list):
                    link_to =  os.readlink(self._list)
                    lbl_link = Gtk.Label(label="<i>{}</i> {}".format(_lang.LINKTO, os.path.basename(link_to)))
                    lbl_link.set_use_markup(True)
                    prop_box.append(lbl_link)
                #
                lbl1 = Gtk.Label(label="<i>{}</i> {}". format(_lang.SIZEITEM,convert_size(folder_size)))
                lbl1.set_use_markup(True)
                prop_box.append(lbl1)
                #
                lbl2 = Gtk.Label(label="<i>{}</i> {}".format(_lang.NUMITEMS, self.total_num_items))
                lbl2.set_use_markup(True)
                prop_box.append(lbl2)
                #
                if self.total_num_items_hiddens > 0:
                    lbl3 = Gtk.Label(label="(<i>{}</i> {})".format(_lang.ITEMSHIDDEN, self.total_num_items_hiddens))
                    lbl3.set_use_markup(True)
                    prop_box.append(lbl3)
        #
        self.present()
    
    def get_size(self, start_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                self.total_num_items += 1
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
                    if f[0] == ".":
                        self.total_num_items_hiddens += 1
        return total_size
    
    def on_apply(self, w):
        if len(self._list) == 1:
            _chk_exec = self.chk_exec.get_active()
            #
            if self.perm_is_changed == True:
                u_perm = self.dd_user.get_selected() # position
                g_perm = self.dd_group.get_selected()
                o_perm = self.dd_other.get_selected()
                _perm = 0
                if _chk_exec == True:
                    _perm = 100
                # user
                if u_perm == 0: # readwrite
                    _perm += 600
                elif u_perm == 1: # read
                    _perm += 400
                elif u_perm == 2: # write
                    _perm += 200
                # group
                if g_perm == 0: # readwrite
                    _perm += 60
                elif g_perm == 1: # read
                    _perm += 40
                elif g_perm == 2: # write
                    _perm += 20
                # other
                if o_perm == 0: # readwrite
                    _perm += 6
                elif o_perm == 1: # read
                    _perm += 4
                elif o_perm == 2: # write
                    _perm += 2
                try:
                    if not os.path.islink(self.file_path):
                        os.chmod(self.file_path, int(str(_perm), base=8))
                except Exception as E:
                    AlDial(self_main, str(E))
                #
                if self.has_dir == 1 and self.chk_recursive.get_active():
                    try:
                        for dirpath, dirnames, filenames in os.walk(self.file_path):
                            for f in filenames:
                                fp = os.path.join(dirpath, f)
                                # skip if it is symbolic link
                                if not os.path.islink(fp):
                                    os.chmod(fp, int(str(_perm), base=8))
                    except Exception as E:
                        AlDial(self_main, str(E))
        if len(self._list) > 1:
            _r = False # file executable bit
            _fr = False # folder access bit
            if self.has_dir < self.total_num_items:
                _r = self.chk_exec.get_active()
            if self.has_dir:
                _fr = self.chk_recursive.get_active()
            _u = self.dd_user.get_selected() # user
            _g = self.dd_group.get_selected() # group
            _o = self.dd_other.get_selected() # other
            _errors = ""
            #
            _perm = 0 # file permissions
            _fperm = 100 # folder permissions
            if _r:
                _perm += 100
            if not _fr:
                _fperm -= 100
            #
            if _u == 0: # readwrite
                _perm += 600
                _fperm += 600
            elif _u == 1: # read
                _perm += 400
                _fperm += 400
            elif _u == 2: # write
                _perm += 200
                _fperm += 200
            #
            if _g== 0: # readwrite
                _perm += 60
                _fperm += 60
            elif _g == 1: # read
                _perm += 40
                _fperm += 40
            elif _g == 2: # write
                _perm += 20
                _fperm += 20
            #
            if _o== 0: # readwrite
                _perm += 6
                _fperm += 6
            elif _o == 1: # read
                _perm += 4
                _fperm += 4
            elif _o == 2: # write
                _perm += 2
                _fperm += 2
            if _perm == 0:
                return
            if _fperm == 0:
                return
            try:
                for el in self._list:
                    file_name = el.get_name()
                    dir_name = self._parent._parent._path
                    file_path = os.path.join(dir_name, file_name)
                    if os.path.islink(file_path):
                        continue
                    elif os.path.isdir(file_path):
                        os.chmod(file_path, int(str(_fperm), base=8))
                    elif os.path.isfile(file_path):
                        os.chmod(file_path, int(str(_perm), base=8))
            except Exception as E:
                _errors += str(E)
            #
            if _errors != "":
                AlDial(self_main, str(E))
        #
        self.destroy()
    
    # the item permissions
    def on_dropdown_changed(self, _dd, _p):
        self.is_changed = True
        
    # populate the dropdown widgets
    def on_dropdown_select(self, _dd, _perm):
        if _perm in ["7","6"]: # readwrite+execute
            _dd.set_selected(0)
            self.perm_is_changed = True
        elif _perm == "4": # read
            _dd.set_selected(1)
            self.perm_is_changed = True
        elif _perm == "2": # write
            _dd.set_selected(2)
            self.perm_is_changed = True
        elif _perm == "0": # forbidden
            _dd.set_selected(3)
            self.perm_is_changed = True
        
    def on_chk_exec(self, _c):
        self.exec_is_changed = True
        
    def on_close(self, w):
        self.destroy()
        
        
# yes/no dialog - delete items
class YNDial(Gtk.AlertDialog):
    def __init__(self, _parent, _str1, _str2):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        self._str2 = _str2
        #
        self.set_buttons([_lang.YES, _lang.NO])
        self.props.cancel_button = 1
        #
        self.set_message(self._str1)
        self.set_detail(self._str2)
        #
        self.choose(self._parent._parent._parent, None, self._parent.dialog_action, None)

# yes/no dialog - remove bookmark
class YNDial2(Gtk.AlertDialog):
    def __init__(self, _parent, _str1, _str2, _row):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        self._str2 = _str2
        self._row = _row
        #
        self.set_buttons([_lang.YES, _lang.NO])
        self.props.cancel_button = 1
        #
        self.set_message(self._str1)
        self.set_detail(self._str2)
        #
        self.choose(self_main, None, self._parent.dialog_action_bk, _row)


class AlDial(Gtk.AlertDialog):
    def __init__(self, _parent, _str1):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        #
        self.set_message(self._str1)
        #
        self.show(self._parent)

# for errors
class SimpleDialog(Gtk.Window):
    def __init__(self, _parent, _str1, _str2):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        self._str2 = _str2
        self.set_transient_for(self._parent)
        self.set_modal(True)
        self.set_titlebar(Gtk.Box.new(0,0))
        self.set_destroy_with_parent(True)
        self.set_resizable(False)
        self.set_name("simpledialog")
        self.set_size_request(DWIDTH, 10)
        #
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(self.box)
        #
        _msg1 = self._str1
        lbl = Gtk.Label(label=_str1)
        self.box.append(lbl)
        #
        _expander = Gtk.Expander.new(label=None)
        _expander.connect("activate", self.on_exp_act)
        self.box.append(_expander)
        #
        dsw = Gtk.ScrolledWindow()
        dsw.set_hexpand(True)
        dsw.set_vexpand(True)
        _expander.set_child(dsw)
        lbl2 = Gtk.Label(label=self._str2)
        lbl2.set_wrap(True)
        lbl2.set_wrap_mode(Pango.WrapMode.WORD) # WORD_CHAR
        dsw.set_child(lbl2)
        #
        close_btn = Gtk.Button(label=_lang.CLOSE)
        self.box.append(close_btn)
        close_btn.connect("clicked", self.on_close)
        #
        self.present()
    
    def on_exp_act(self, _exp):
        if _exp.get_expanded() == False:
            self.set_size_request(DWIDTH, DHEIGHT)
        else:
            self.set_size_request(DWIDTH, 10)
    
    def on_close(self, w):
        self.destroy()
    
# _type: 1 rename - 2 new folder
class RenDialog(Gtk.Window):
    def __init__(self, _parent, _type, _str1, _item):
        super().__init__()
        self._parent = _parent
        self._type = _type
        self._str1 = _str1
        self._item = _item
        self.set_transient_for(self._parent)
        self.set_modal(True)
        self.set_titlebar(Gtk.Box.new(0,0))
        self.set_destroy_with_parent(True)
        self.set_resizable(False)
        self.set_name("renamedialog")
        self.set_size_request(DWIDTH, 10)
        #
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(self.box)
        #
        if self._type == 1 or self._type == 2:
            lbl = Gtk.Label(label=self._str1)
            self.box.append(lbl)
            #
            self._entry = Gtk.Entry.new()
            self.box.append(self._entry)
            if isinstance(self._item, str):
                self.dir_path = self._item
                self.item_name = ""
            else:
                self.dir_path = self._item._path
                self.item_name = self._item.item_name
                self._entry.get_buffer().set_text(self.item_name, -1)
            #
            self.msg_lbl = Gtk.Label(label=_lang.CHOSEOTHERNAME)
            self.msg_lbl.set_visible(False)
            self.box.append(self.msg_lbl)
            #
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            btn_box.set_hexpand(True)
            self.box.append(btn_box)
            #
            self.accept_btn = Gtk.Button(label=_lang.ACCEPT)
            self.accept_btn.set_hexpand(True)
            self.accept_btn.connect("clicked", self.on_accept)
            btn_box.append(self.accept_btn)
            #
            close_btn = Gtk.Button(label=_lang.CLOSE)
            close_btn.set_hexpand(True)
            close_btn.connect("clicked", self.on_close)
            btn_box.append(close_btn)
        #
        self.present()
        self._entry.connect("activate", self.on_activate)
        self._entry.grab_focus()
        self._entry.get_buffer().connect("inserted-text", self.on_entry)
        self._entry.get_buffer().connect("deleted-text", self.on_entry)
        
    def on_entry(self, _b, _p, _c, _c2=None):
        self.msg_lbl.set_visible(False)
        
    def on_activate(self, _w):
        self.on_rename_item()
        
    def on_accept(self, w):
        self.on_rename_item()
        
    def on_rename_item(self):
        newname = self._entry.get_buffer().get_text()
        if self._type == 1:
            if os.path.exists(os.path.join(self.dir_path,newname)):
                self.msg_lbl.set_visible(True)
                self._entry.grab_focus()
                return
            #
            is_renamed = 0
            try:
                oldname = os.path.join(self.dir_path, self.item_name)
                os.rename(oldname, os.path.join(self.dir_path,newname))
                is_renamed = 1
            except Exception as E:
                self._entry.grab_focus()
            if is_renamed == 1:
                self.destroy()
        elif self._type == 2:
            if os.path.exists(os.path.join(self.dir_path,newname)):
                self.msg_lbl.set_visible(True)
                self._entry.grab_focus()
                return
            try:
                ff = Gio.File.new_for_path(os.path.join(self.dir_path,newname))
                ret = ff.make_directory(None)
                if ret == True:
                    self.destroy()
                else:
                    self.destroy()
                    AlDial(self_main, FOLDERNEWERROR)
            except Exception as E:
                self.destroy()
                AlDial(self_main, str(E))
    
    def on_close(self, w):
        self.destroy()
        

##########
ATTRIBUTES = ",".join((
    "standard::name", "standard::display-name", "standard::icon", "standard::symbolic-icon",
    "standard::type", "standard::is-symlink", "standard::is-hidden", "standard::is-backup", "standard::content-type",
    "standard::size", "standard::target-uri", "time::modified", "time::created", "time::access", "access::can-write",
    "thumbnail::path", "thumbnail::failed", "xattr::xdg.tags"))
##########

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(WWIDTH, WHEIGHT)
        self.app_ = self.get_application()
        self.set_title("File Manager")
        global self_main
        self_main = self
        self.connect("show", self.on_main_shown)
        self.connect("close-request", self.on_close)
        # self.connect("force-close", self.on_force_close)
        #
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(PANEL_STYLE_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        #
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(self.headerbar)
        _w = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        _w.set_size_request(1,-1)
        _w.set_hexpand(False)
        self.headerbar.set_title_widget(_w)
        self.headerbar.set_show_title_buttons(True)
        # remove the title widget
        hb_tw = self.headerbar.get_title_widget()
        self.headerbar.remove(hb_tw)
        #
        self.home_path = os.path.expanduser("~")
        self.starting_path = os.path.expanduser("~")
        self.file_to_select = None
        try:
            if len(sys.argv) > 1:
                path_tmp = sys.argv[1]
                if path_tmp != "trash://":
                    if os.path.isdir(path_tmp) and os.path.exists(path_tmp):
                        self.starting_path = path_tmp.rstrip("/")
                    else:
                        if os.path.exists(path_tmp):
                            root_path = os.path.dirname(path_tmp)
                            self.starting_path = root_path
                            self.file_to_select = os.path.basename(path_tmp)
                    if self.starting_path != self.home_path:
                        if not os.access(self.starting_path, os.R_OK):
                            sys.exit()
                else:
                    self.file_to_select = "trash://"
            else:
                if not os.access(self.starting_path, os.R_OK):
                    sys.exit()
        except Exception as E:
            self.starting_path = os.path.expanduser("~")
        #
        # MAIN BOX
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)
        #
        self.main_paned = Gtk.Paned.new(orientation=Gtk.Orientation.HORIZONTAL)
        # self.main_paned.set_wide_handle(True)
        self.main_paned.set_resize_start_child(True)
        self.main_paned.set_shrink_start_child(True)
        self.main_paned.set_position(LATERAL_PANEL_WIDTH)
        # self.main_paned.connect("notify::position", self.on_paned_moved)
        self.main_box.append(self.main_paned)
        ## BOX: lateral panel
        self.lat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.lat_box.set_hexpand(True)
        self.lat_box.set_vexpand(True)
        self.lat_box.set_margin_start(10)
        self.lat_box.set_margin_end(6)
        self.lat_box.set_margin_top(10)
        self.lat_box.set_margin_bottom(6)
        #
        self.main_paned.set_start_child(self.lat_box)
        self.lateral_panel_folder_populate() # the main user folders
        self.lateral_panel_bookmark_populate() # the user bookmarks
        self.lateral_panel_volume_populate() # the volume section
        ## BOX: switch and iconview
        self.icons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_paned.set_end_child(self.icons_box)
        ##
        self._notebook = None
        ####### PATH BAR
        self.path_bar = PathBar(self)
        self.path_bar.connect_path_changed(self.on_folder_navigated)
        self.trigger_path_update(self.starting_path)
        self.path_bar.set_hexpand(True)
        self.headerbar.pack_start(self.path_bar)
        ####
        # button box
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.icons_box.append(btn_box)
        ######### hamburger menu
        self.ham_menu = Gtk.MenuButton.new()
        if icon_theme.has_icon("open-menu-symbolic"):
            self.ham_menu.set_icon_name("open-menu-symbolic")
        elif icon_theme.has_icon("application-menu"):
            self.ham_menu.set_icon_name("application-menu")
        self.headerbar.pack_end(self.ham_menu)
        # popover menu
        self.ham_pop = Gtk.Popover.new()
        self.ham_pop.set_has_arrow(False)
        self.ham_pop.set_halign(Gtk.Align.START)
        self.ham_menu.set_popover(self.ham_pop)
        ## menu - actions
        quit_action = Gio.SimpleAction.new("quit", None) # look at MENU_XML win.quit
        quit_action.connect("activate", self.on_quit_action_actived)
        self.add_action(quit_action) # (self window) == win in MENU_XML
        #
        about_action = Gio.SimpleAction.new("about", None) # look at MENU_XML win.about
        about_action.connect("activate", self.on_about_action_actived)
        self.add_action(about_action) # (self window) == win in MENU_XML
        #
        settings_action = Gio.SimpleAction.new("settings", None) # look at MENU_XML win.about
        settings_action.connect("activate", self.on_settings_action)
        self.add_action(settings_action) # (self window) == win in MENU_XML
        #
        self.hidden_action = Gio.SimpleAction.new("hidden", None)
        self.hidden_action.connect("activate", self.on_show_hidden)
        self.add_action(self.hidden_action) # (self window) == win in MENU_XML
        #
        menu = Gtk.Builder.new_from_string(MENU_XML, -1).get_object("app-menu")
        self.ham_menu.set_menu_model(menu)
        ##### root button
        self.root_btn = Gtk.Button.new()
        self.root_btn.set_tooltip_text(_lang.ROOTTAB)
        self.root_btn.connect("clicked", self.on_root_tab)
        self.headerbar.pack_end(self.root_btn)
        if icon_theme.has_icon("drive-harddisk"):
            self.root_btn.set_icon_name("drive-harddisk")
        elif icon_theme.has_icon("gnome-dev-harddisk"):
            self.root_btn.set_icon_name("gnome-dev-harddisk")
        elif icon_theme.has_icon("gtk-harddisk"):
            self.root_btn.set_icon_name("gtk-harddisk")
        ##### new tab button
        self.new_tab_btn = Gtk.Button.new()
        self.new_tab_btn.set_tooltip_text(_lang.NEWTAB)
        self.new_tab_btn.connect("clicked", self.on_new_tab)
        self.headerbar.pack_end(self.new_tab_btn)
        if icon_theme.has_icon("folder-new"):
            self.new_tab_btn.set_icon_name("folder-new")
        elif icon_theme.has_icon("gtk-add"):
            self.new_tab_btn.set_icon_name("gtk-add")
        elif icon_theme.has_icon("add"):
            self.new_tab_btn.set_icon_name("add")
        elif icon_theme.has_icon("gtk-home"):
            self.new_tab_btn.set_icon_name("gtk-home")
        elif icon_theme.has_icon("folder"):
            self.new_tab_btn.set_icon_name("folder")
        ########
        # notebook
        self._notebook = Gtk.Notebook.new()
        self._notebook.props.hexpand = True
        self._notebook.props.vexpand = True
        self._notebook.set_scrollable(True)
        self.icons_box.append(self._notebook)
        # FIRST STACK CHILD - mandatory
        if self.file_to_select == "trash://":
            sw = ScrolWinTrash(self)
        else:
            sw = ScrolWin(self.starting_path, self)
            sw.grid1.grab_focus()
        if sw != None:
            self._notebook.append_page(sw, sw.tab_label)
            self._notebook.set_tab_reorderable(sw, True)
        else:
            sys.exit()
        self._notebook.connect("switch_page", self.on_notebook_tab_changed)
        #
        self._ctrl = Gtk.ShortcutController()
        self.add_controller(self._ctrl)
        # quit the application
        _ca = Gtk.CallbackAction.new(self.on_quit_action, None, None)
        _st = Gtk.ShortcutTrigger.parse_string("<Primary>q")
        _sc = Gtk.Shortcut.new(_st, _ca)
        self._ctrl.add_shortcut(_sc)
        
    def on_quit_action(self, action, param=None, _a=None, _b=None, _c=None):
        self.app_.quit()
        
    def on_close(self, _w):
        _WWIDTH = self.get_width()
        _WHEIGHT = self.get_height()
        _LATERAL_PANEL_WIDTH = self.main_paned.get_position()
        if _WWIDTH != WWIDTH or _WHEIGHT != WHEIGHT or _LATERAL_PANEL_WIDTH != LATERAL_PANEL_WIDTH:
            self.on_setting_conf()
        
    def on_setting_conf(self):
        global WWIDTH
        global WHEIGHT
        global PANEL_ICON_SIZE
        config_conf["wwidth"] = self.get_width()
        config_conf["wheight"] = self.get_height()
        config_conf["panel_lateral_width"] = self.main_paned.get_position()
        try:
            _ff = open(config_file,"w")
            _data_json = config_conf
            json.dump(_data_json, _ff, indent = 4)
            _ff.close()
        except:
            pass
        
    # def on_force_close(self, _w):
        # self.set_visible(False)
    
    def on_main_shown(self, w):
        self._lb1.unselect_all()
    
    # def on_paned_moved(self, _p, _param=None):
        # print("paned position:: ", _p.get_position())
    
    def lateral_panel_folder_populate(self):
        self.lat_sw = Gtk.ScrolledWindow.new()
        self.lat_sw.set_hexpand(True)
        self.lat_sw.set_vexpand(True)
        self.lat_sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC) 
        self.lat_box.append(self.lat_sw)
        #
        self.scroll_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.lat_sw.set_child(self.scroll_box)
        #
        # str = GLib.get_user_special_dir : GLib.UserDirectory DIRECTORY_DESKTOP DIRECTORY_DOCUMENTS DIRECTORY_DOWNLOAD
        # DIRECTORY_MUSIC DIRECTORY_PICTURES DIRECTORY_PUBLIC_SHARE DIRECTORY_TEMPLATES
        # DIRECTORY_VIDEOS 
        #
        HOME_DIRS = []
        for el in [GLib.UserDirectory.DIRECTORY_DESKTOP,GLib.UserDirectory.DIRECTORY_DOCUMENTS,GLib.UserDirectory.DIRECTORY_PICTURES,GLib.UserDirectory.DIRECTORY_MUSIC,GLib.UserDirectory.DIRECTORY_VIDEOS,GLib.UserDirectory.DIRECTORY_PUBLIC_SHARE,GLib.UserDirectory.DIRECTORY_DOWNLOAD]:
            HOME_DIRS.append(os.path.basename(GLib.get_user_special_dir(el)))
        HOME_DIRS_ICONS = ["folder-desktop", "folder-documents", "folder-pictures", "folder-music", "folder-videos", "folder-publicshare", "folder-downloads"]
        #
        self.exp1 = Gtk.Expander.new(label=_lang.LHOME)
        self.exp1.set_expanded(True)
        #
        self._lb1 = Gtk.ListBox.new()
        # self.scroll_box.append(self._lb1)
        self.exp1.set_child(self._lb1)
        self.scroll_box.append(self.exp1)
        self._lb1.connect("row-activated", self.on_row_activated)
        #
        _sep = Gtk.Separator.new(orientation=Gtk.Orientation.HORIZONTAL)
        _sep.set_name("separator1")
        self.scroll_box.append(_sep)
        #
        for i,el in enumerate(HOME_DIRS):
            if not os.path.exists(os.path.join(_HOME,el)):
                continue
            _box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=0)
            hip = icon_theme.lookup_icon(HOME_DIRS_ICONS[i], [], PANEL_ICON_SIZE, 1, 0, Gtk.IconLookupFlags.FORCE_SYMBOLIC)
            hi = Gtk.Image.new_from_paintable(hip)
            hi.set_pixel_size(PANEL_ICON_SIZE)
            _box.append(hi)
            hl = Gtk.Label(label=el)
            _box.name = os.path.join(_HOME, el)
            _box.append(hl)
            self._lb1.append(_box)
        # the trashcan
        _boxt = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=0)
        hipt = icon_theme.lookup_icon("trashcan_empty", ["trash_empty"], PANEL_ICON_SIZE, 1, 0, Gtk.IconLookupFlags.FORCE_SYMBOLIC)
        hit = Gtk.Image.new_from_paintable(hipt)
        hit.set_pixel_size(PANEL_ICON_SIZE)
        _boxt.append(hit)
        hlt = Gtk.Label(label=_lang.TRASHCAN)
        _boxt.name = "//TRASHCAN"
        _boxt.append(hlt)
        self._lb1.append(_boxt)
        
    def lateral_panel_bookmark_populate(self):
        self.exp2 = Gtk.Expander.new(label=_lang.LBOOKMARKS)
        self.exp2.set_expanded(True)
        #
        self._lb2 = Gtk.ListBox.new()
        self._lb2.set_selection_mode(Gtk.SelectionMode.NONE)
        # self.scroll_box.append(self._lb2)
        self.exp2.set_child(self._lb2)
        self.scroll_box.append(self.exp2)
        #
        self._lb2.connect("row-activated", self.on_row_activated)
        ##
        _sep = Gtk.Separator.new(orientation=Gtk.Orientation.HORIZONTAL)
        _sep.set_name("separator1")
        self.scroll_box.append(_sep)
        # drop
        self.drop_controller_lb = Gtk.DropTarget.new(type=GObject.TYPE_NONE, actions=Gdk.DragAction.COPY)
        self.drop_controller_lb.set_gtypes([self, Gdk.FileList, str])
        self.drop_controller_lb.connect("drop", self.on_drop_lb)
        self._lb2.add_controller(self.drop_controller_lb)
        ###########
        self.bookmark_list = []
        _list_tmp = None
        _f = open(BOOKMARK_FILE)
        _list_tmp = _f.readlines()
        _f.close()
        for ell in _list_tmp:
            _ff = unquote(ell).rstrip()
            self.bookmark_list.append(_ff)
        #
        for el in self.bookmark_list:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            box.set_hexpand(True)
            lbl = Gtk.Label(label=os.path.basename(el))
            lbl.set_hexpand(True)
            box.append(lbl)
            box.name = el
            box.set_tooltip_text(el)
            box.set_halign(Gtk.Align.START)
            self._lb2.insert(box, -1)
            # right button
            _gesture_r = Gtk.GestureClick.new()
            _gesture_r.set_button(3)
            box.add_controller(_gesture_r)
            _gesture_r.connect('pressed', self.on_bk_gesture_r)
    
    def lateral_panel_volume_populate(self):
        self.exp3 = Gtk.Expander.new(label=_lang.LDEVICES)
        self.exp3.set_expanded(True)
        #
        self.volume_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.volume_box.set_halign(Gtk.Align.START)
        # self.scroll_box.append(self.volume_box)
        self.exp3.set_child(self.volume_box)
        self.scroll_box.append(self.exp3)
        #
        #############
        self._vm = Gio.VolumeMonitor.get()
        # [mount_points, block_devices, can_eject]
        self.STARTING_MOUNTS_LIST = []
        for _mount in self._vm.get_mounts():
            gfile = _mount.get_root()
            self.STARTING_MOUNTS_LIST.append([_mount.get_default_location().get_path(), self.find_mount_device(_mount.get_default_location().get_path()), _mount.can_eject(), _mount])
        #######
        self._guc = GUdev.Client.new(["block", None])
        ret = self._guc.query_by_subsystem("block")
        #
        for _d in ret:
            if _d.get_device_file() not in MEDIA_SKIP:
                self.on_add_device(None, None, _d)
        #
        self._guc.connect("uevent", self.on_uevent)
        ######
        self._vm.connect("mount-added", self.on_mount_added) # set the mount path
        # self._vm.connect("mount-pre-unmount", self.on_mount_pre_unmount)
        self._vm.connect("mount-removed", self.on_mount_removed) # just a dialog
        # self._vm.connect("mount-changed", self.on_mount_changed)
        
    # find the block device from the mount path
    def find_mount_device(self, path):
        target_path = os.path.realpath(path)
        target_dev = os.stat(target_path).st_dev
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    device, mount_point = parts[0], parts[1]
                    if os.path.exists(mount_point) and os.stat(mount_point).st_dev == target_dev:
                        if device.startswith('/dev/'):
                            return device
        
    # find the mount path from the block device
    def find_mount_point(self, target_device):
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    device, mount_point = parts[0], parts[1]
                    if os.path.exists(mount_point) and device == target_device:
                        if device.startswith('/dev/'):
                            return mount_point
        return None
        
    def on_mount_mount(self, _w, target_device=None, mount_path=None):
        if target_device == None and mount_path == None:
            return
        if mount_path == None:
            mount_path = None
            #
            _fc = self.volume_box.get_first_child()
            if _fc == None:
                return
            i = 0
            while _fc != None:
                i += 1
                if i == 20:
                    break
                if _fc._device == target_device:
                    mount_path = _fc.lbl.mount_path
                    if mount_path == None:
                        mount_path = self.find_mount_point(target_device)
                        _fc.lbl.mount_path = mount_path
                    break
                else:
                    _fc = self.volume_box.get_next_sibling()
        #
        if mount_path != None and os.path.exists(mount_path):
            sw = ScrolWin(mount_path, self)
            if sw != None:
                idx = self._notebook.append_page(sw, sw.tab_label)
                self._notebook.set_tab_reorderable(sw, True)
                self._notebook.set_current_page(idx)
    
    # the device has been mounted - set the mount path
    def on_mount_added(self, _vm, _mount):
        self.STARTING_MOUNTS_LIST.append([_mount.get_default_location().get_path(), self.find_mount_device(_mount.get_default_location().get_path()), _mount.can_eject(), _mount])
        mount_gfile = _mount.get_root()
        # the mount point
        mount_path = mount_gfile.get_path()
        target_device = self.find_mount_device(mount_path)
        #
        _fc = self.volume_box.get_first_child()
        if _fc == None:
            return
        i = 0
        while _fc != None:
            i += 1
            if i == 20:
                break
            if _fc._device == target_device:
                _fc.lbl.mount_path = mount_path
                _fc._mount = _mount
                # set the icon
                _m_icon = _mount.get_icon()
                _fc.icon.set_from_gicon(_m_icon)
                # add the eject button if not
                if _mount.can_eject():
                    if _fc._eject_btn == None:
                        self.add_eject_btn(_fc)
                break
            else:
                _fc = self.volume_box.get_next_sibling()
    
    # _mount is gio.mount
    # the device has been unmounted
    def on_mount_removed(self, _vm, _mount):
        for _m in self.STARTING_MOUNTS_LIST[:]:
            if _m[3] == _mount:
                self.STARTING_MOUNTS_LIST.remove(_m)
                break
        m_name = _mount.get_name()
        # close the tabs open
        n_pages = self._notebook.get_n_pages()
        for i in reversed(range(n_pages)):
            _sw = self._notebook.get_nth_page(i)
            try:
                if _sw._path.startswith(_mount.get_default_location().get_path()):
                    self._notebook.remove_page(i)
            except:
                pass
        n_pages = self._notebook.get_n_pages()
        if n_pages == 0:
            sw = ScrolWin(_HOME, self)
            sw.grid1.grab_focus()
            if sw != None:
                self._notebook.append_page(sw, sw.tab_label)
                self._notebook.set_tab_reorderable(sw, True)
        #
        AlDial(self_main, "{}: {}".format(_lang.MOUNTUNMOUNTED, m_name))
    
    # def on_mount_changed(self, _vm, _mount):
        # print("mount changed:: ", _mount.get_name())
    
    # # _mount is gio.mount
    # def on_mount_pre_unmount(self, _vm, _mount):
        # print("mount pre unmount:: ", _mount.get_name())
   
    def on_udisk_mount_device(self, _w, box):
        target_device = box._device
        mount_point= self.find_mount_point(target_device)
        #
        if mount_point == None:
            self.udisk_mount_device(_w, box)
        else:
            self.udisk_unmount_device(_w, box)
    
    def device_get_used_size(self, mount_point):
        if mount_point != None and os.path.exists(mount_point):
            try:
                ret = os.statvfs(mount_point)
                device_free_size = (ret.f_blocks - ret.f_bfree) * ret.f_bsize
                return convert_size(device_free_size)
            except:
                return 0
        return 0
    
    def device_get_size(self, _dev, _parent=None):
        if _parent == None:
            device_size = subprocess.check_output(["cat", "/sys/block/{}/size".format(os.path.basename(_dev))])
            return convert_size(int(device_size.decode().strip("\n"))*512)
        else:
            device_size = subprocess.check_output(["cat", "/sys/block/{}/{}/size".format(os.path.basename(_parent), os.path.basename(_dev))])
            return convert_size(int(device_size.decode().strip("\n"))*512)
        return 0
    
    def on_add_device(self, client, action, device):
        target_device = device.get_device_file()
        parent_device = device.get_parent().get_device_file()
        device_name = device.get_property("ID_FS_LABEL")
        #
        device_size = self.device_get_size(target_device, parent_device)
        #
        _model = "------"
        if device.has_property("ID_MODEL"):
            _model = device.get_property("ID_MODEL")
            if _model:
                _model = _model.replace("_"," ")
            else:
                _model = _lang.DDEVICE
        #
        if parent_device != None:
            _fc = self.volume_box.get_first_child()
            if _fc == None:
                return
            i = 0
            while _fc != None:
                i += 1
                if i == 20:
                    break
                if _fc._device == parent_device:
                    self.volume_box.remove(_fc)
                    break
                else:
                    _fc = self.volume_box.get_next_sibling()
        if 1:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            box.set_hexpand(True)
            self.volume_box.append(box)
            m_name = device_name or os.path.basename(target_device) # _mount.get_name()
            m_icon = icon_theme.lookup_icon("drive", ["drive-harddisk"], PANEL_ICON_SIZE, 1, 0, Gtk.IconLookupFlags.FORCE_SYMBOLIC)
            m_icn = Gtk.Image.new_from_paintable(m_icon)
            box.append(m_icn)
            ## label button
            m_lbl = Gtk.Button.new()
            mount_path = None
            m_lbl.connect("clicked", self.on_mount_mount, target_device, mount_path)
            m_lbl2 = Gtk.Label(label=m_name)
            m_lbl2.set_hexpand(True)
            m_lbl.set_child(m_lbl2)
            m_lbl.add_css_class("flat")
            m_lbl.set_hexpand(True)
            m_lbl.set_halign(Gtk.Align.START)
            box.lbl = m_lbl2 # the label
            box.icon = m_icn # the icon
            box.append(m_lbl)
            # box._path = _mount.get_default_location().get_path()
            box._device = target_device # the device
            box.lbl.mount_path = None
            ## mount button
            m_icn_mount = icon_theme.lookup_icon("media-eject", ["exit", "gtk-close", "gtk-quit", "window-close"], PANEL_ICON_SIZE, 1, 0, Gtk.IconLookupFlags.FORCE_SYMBOLIC)
            p_icn_mount = Gtk.Image.new_from_paintable(m_icn_mount)
            btn_mount = Gtk.Button.new()
            btn_mount.add_css_class("flat")
            box.btn_mount = btn_mount
            box._parent_device = parent_device
            box._model = _model
            #
            mount_point = None
            can_eject = 0
            box._mount = None
            for _mount in self.STARTING_MOUNTS_LIST:
                if _mount[1] == target_device:
                    mount_point = _mount[0]
                    can_eject = _mount[2]
                    box._mount = _mount[3]
                    # set the icon
                    _m_icon = _mount[3].get_icon()
                    box.icon.set_from_gicon(_m_icon)
                    break
            #
            event_controller = Gtk.EventControllerMotion.new()
            event_controller.connect("enter", self.on_enter,device_size,_model,target_device)
            m_lbl2.add_controller(event_controller)
            if mount_point and os.path.exists(mount_point):
                btn_mount.set_tooltip_text(_lang.MUMOUNT)
            else:
                btn_mount.set_tooltip_text(_lang.MMOUNT)
            #
            btn_mount.set_child(p_icn_mount)
            box.append(btn_mount)
            btn_mount.connect("clicked", self.on_udisk_mount_device, box)
            ## eject button
            box._eject_btn = None
            if can_eject != 0 and box._mount != None:
                self.add_eject_btn(box)
    
    def on_enter(self, ctrl, x, y, device_size,_model,target_device):
        mount_point = None
        for _mount in self.STARTING_MOUNTS_LIST:
            if _mount[1] == target_device:
                mount_point = _mount[0]
                break
        if mount_point:
            device_size_used = self.device_get_used_size(mount_point)
            if device_size_used != 0:
                _text = "{}: {} ({})\n{}: {}\n{}: {}".format(_lang.DSIZE, device_size, device_size_used, _lang.DMODEL, _model, _lang.DDEVICE, target_device)
                ctrl.get_widget().set_tooltip_text(_text)
        else:
            ctrl.get_widget().set_tooltip_text("{}: {}\n{}: {}\n{}: {}".format(_lang.DSIZE, device_size, _lang.DMODEL, _model, _lang.DDEVICE, target_device))
        return True
        
    # this is possible for mounted discs
    def add_eject_btn(self, box):
        m_icn_eject = icon_theme.lookup_icon("media-eject", ["exit", "gtk-close", "gtk-quit", "window-close"], PANEL_ICON_SIZE, 1, 0, Gtk.IconLookupFlags.FORCE_SYMBOLIC)
        p_icn_eject = Gtk.Image.new_from_paintable(m_icn_eject)
        btn_eject = Gtk.Button.new()
        btn_eject.add_css_class("flat")
        btn_eject.set_tooltip_text(_lang.MEJECT)
        btn_eject.set_child(p_icn_eject)
        box.append(btn_eject)
        box._eject_btn = btn_eject
        btn_eject.connect("clicked", self.on_media_eject, box._mount)
    
    def on_media_eject(self, _w, _mount):
        mount_can_eject = _mount.can_eject()
        if mount_can_eject:
            mount_name = _mount.get_name()
            mount_can_eject = _mount.can_eject()
            mount_uiid = _mount.get_uuid()
            mount_path = _mount.get_default_location().get_path()
            def asyncReadyCallback2(source_object, res, data):
                ret = -1
                try:
                    ret = _mount.eject_with_operation_finish(res)
                except:
                    pass
                #
                if ret == True:
                    self.on_remove_device(mount_path)
                    AlDial(self_main, "{}: {}".format(_lang.MOUNTEJECTED, mount_name))
            _mount.eject_with_operation(Gio.MountUnmountFlags.NONE, None, None, asyncReadyCallback2, None)
    
    # handle: adding and removing a device and change the name in the view
    def on_uevent(self, client, action, device):
        if action == "add":
            self.on_add_device(client, action, device)
        if action == "remove":
            target_device = device.get_device_file()
            parent_device = device.get_parent().get_device_file()
            device_name = device.get_property("ID_FS_LABEL")
            #
            _fc = self.volume_box.get_first_child()
            if _fc == None:
                return
            #
            i = 0
            while _fc != None:
                i += 1
                if i == 20:
                    break
                if _fc._device == target_device:
                    try:
                        self.volume_box.remove(_fc)
                    except:
                        pass
                    break
                else:
                    _fc = self.volume_box.get_next_sibling()
        # change: 1) name 2) mounted 3) unmounted
        elif action == "change":
            target_device = device.get_device_file()
            parent_device = device.get_parent().get_device_file()
            device_name = device.get_property("ID_FS_LABEL")
            device_size = self.device_get_size(target_device, parent_device)
            # update the label
            _fc = self.volume_box.get_first_child()
            if _fc == None:
                return
            i = 0
            while _fc != None:
                i += 1
                if i == 20:
                    break
                if _fc._device == target_device:
                    try:
                        if _fc.lbl.get_label() != device_name:
                            _fc.lbl.set_label(device_name)
                        # update the tooltip
                        device_size = self.device_get_size(target_device, parent_device)
                        _model = device.get_property("ID_MODEL")
                        if _model:
                            _model = _model.replace("_"," ")
                        else:
                            _model = _lang.DDEVICE
                        #
                        # update the mount point
                        mount_point= self.find_mount_point(target_device)
                        #
                        _model = _fc._model
                        #
                        if os.path.exists(mount_point):
                            _fc.btn_mount.set_tooltip_text(_lang.MUMOUNT)
                        else:
                            _fc.btn_mount.set_tooltip_text(_lang.MMOUNT)
                    except:
                        pass
                    break
                else:
                    _fc = self.volume_box.get_next_sibling()
    
    # target_device e.g.: /dev/sdb1
    def udisk_mount_device(self, _w, box):
        client = UDisks.Client.new_sync(None)
        object_manager = client.get_object_manager()
        objects = object_manager.get_objects()
        #
        target_device = box._device
        parent_device = box._parent_device
        for obj in objects:
            block = obj.get_block()
            if block and block.props.device == target_device:
                filesystem = obj.get_filesystem()
                if not filesystem:
                    AlDial(self_main, "{}: {}".format(_lang.MDEVICECANNOMOUNT, target_device))
                    return False
                #
                options = GLib.Variant('a{sv}', {})
                try:
                    mount_path = filesystem.call_mount_sync(options, None)
                    box.btn_mount.set_tooltip_text(_lang.MUMOUNT)
                    _model = box._model
                    device_size = self.device_get_size(target_device, parent_device)
                    device_size_used = self.device_get_used_size(mount_path)
                    return True
                except Exception as E:
                    AlDial(self_main, str(E))
                    return False
        return False
    
    # target_device e.g.: /dev/sdb1
    def udisk_unmount_device(self, _w, box):
        client = UDisks.Client.new_sync(None)
        object_manager = client.get_object_manager()
        objects = object_manager.get_objects()
        #
        target_device = box._device
        parent_device = box._parent_device
        for obj in objects:
            block = obj.get_block()
            if block and block.props.device == target_device:
                filesystem = obj.get_filesystem()
                if not filesystem:
                    return False
                if not filesystem.props.mount_points:
                    return True
                options = GLib.Variant('a{sv}', {})
                try:
                    filesystem.call_unmount_sync(options, None)
                    box.btn_mount.set_tooltip_text(_lang.MMOUNT)
                    _model = box._model
                    return True
                except Exception as E:
                    AlDial(self_main, str(E))
                    return False
        AlDial(self_main, "{}: {}".format(_lang.DEVICENOTFOUND, target_device))
        return False
    
    # yndial2 function
    def dialog_action_bk(self, _obj, _res, bk_name):
        _result = _obj.choose_finish(_res)
        if _result == 1:
            return
        else:
            for i in range(len(self.bookmark_list)):
                _row = self._lb2.get_row_at_index(i)
                _name = _row.get_child().name
                if _name == bk_name:
                    self._lb2.remove(_row)
                    self.bookmark_list.remove(bk_name)
                    try:
                        _f = open(BOOKMARK_FILE, "w")
                        for el in self.bookmark_list:
                            _f.write(el+"\n")
                        _f.close()
                    except Exception as E:
                        AlDial(self_main, str(E))
                    break
        
    def on_bk_gesture_r(self, o,n,x,y):
        bk_name = o.get_widget().name
        YNDial2(self, _lang.DELETEQ, _lang.BOOKMARKREMOVEFOREVER, bk_name)
    
    # def on_row_selected(self, _lb, _row):
        # print("row selected:: ", _lb, _row)
    
    def on_row_activated(self, _lb, _row):
        selected_row = _row
        if selected_row == None:
            return
        _child = selected_row.get_child()
        ##### add the tab
        _path = _child.name
        # the recycle bin
        if _path == "//TRASHCAN":
            _n_pages = self._notebook.get_n_pages()
            for _t in range(_n_pages):
                _page = self._notebook.get_nth_page(_t)
                if _page._path == _path:
                    return
            swt = ScrolWinTrash(self)
            idx = self._notebook.append_page(swt, swt.tab_label)
            self._notebook.set_tab_reorderable(swt, True)
            self._notebook.set_current_page(idx)
            return
        if not os.path.exists(_path):
            AlDial(self_main, _lang.FOLDERNOTFOUND+": {}".format(os.path.basename(_path)))
            return
        sw = ScrolWin(_path, self)
        idx = self._notebook.append_page(sw, sw.tab_label)
        self._notebook.set_tab_reorderable(sw, True)
        self._notebook.set_current_page(idx)
    
    def on_drop_lb(self, ctrl, value, _x, _y):
        _row = self._lb2.get_row_at_index(_y)
        #
        if value != []:
            _values = value.get_files()
            for el in _values:
                _path = el.get_path()
                if os.path.exists(_path) and _path not in self.bookmark_list:
                    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                    lbl = Gtk.Label(label=os.path.basename(_path))
                    lbl.set_hexpand(True)
                    box.append(lbl)
                    box.name = _path
                    box.set_tooltip_text(_path)
                    box.set_halign(Gtk.Align.START)
                    self._lb2.insert(box, -1)
                    # right button
                    _gesture_r = Gtk.GestureClick.new()
                    _gesture_r.set_button(3)
                    box.add_controller(_gesture_r)
                    _gesture_r.connect('pressed', self.on_bk_gesture_r)
                    #
                    self.bookmark_list.append(_path)
                    try:
                        _f = open(BOOKMARK_FILE, "w")
                        for el in self.bookmark_list:
                            _f.write(el+"\n")
                        _f.close()
                    except Exception as E:
                        AlDial(self_main, str(E))
                    break
    
    # the root folder
    def on_root_tab(self, w):
        sw = ScrolWin("/", self)
        if sw != None:
            idx = self._notebook.append_page(sw, sw.tab_label)
            self._notebook.set_tab_reorderable(sw, True)
            self._notebook.set_current_page(idx)
            # self.trigger_path_update("/")
    
    # open a new tab at the starting directory
    def on_new_tab(self, w):
        sw = ScrolWin(self.home_path, self)
        if sw != None:
            idx = self._notebook.append_page(sw, sw.tab_label)
            self._notebook.set_tab_reorderable(sw, True)
            self._notebook.set_current_page(idx)
            # # useless
            # self.trigger_path_update(self.home_path)
    
    # set the new path to the current page
    def on_notebook_new_path(self, _path):
        if isinstance(self._notebook, Gtk.Notebook):
            _dir = Gio.File.new_for_path(_path)
            sw = self._notebook.get_nth_page(self._notebook.get_current_page())
            _m = sw._m
            _m.set_file(_dir)
            sw._label_tab.set_tooltip_text(_path)
    
    def on_notebook_tab_changed(self, notebook, page, page_num):
        self.path_bar.set_path(page._path, 1)
    
    def on_about_action_actived(self, action, param=None):
        _aboutdial = Gtk.AboutDialog.new()
        _img = Gtk.Image.new_from_file(os.path.join(HOME_CONFIG,"icons","icon_horizon.svg"))
        _paintable = _img.get_paintable()
        _aboutdial.set_logo(_paintable)
        _aboutdial.set_program_name(FMNAME)
        _aboutdial.set_version(VERSION)
        _aboutdial.set_authors(["Philip J. Fry"])
        _aboutdial.set_comments("Made for me 🙂")
        _aboutdial.set_website(FMSITE)
        _aboutdial.set_license_type(Gtk.License.GPL_3_0_ONLY)
        _aboutdial.set_transient_for(self_main)
        _aboutdial.present()
        
    def on_quit_action_actived(self, action, param=None):
        self.app_.quit()
    
    
######### PATH BAR
    def on_folder_navigated(self, target_path):
        self.trigger_path_update(target_path)
    
    def trigger_path_update(self, new_path):
        self.path_bar.set_path(new_path)
        self.on_notebook_new_path(new_path)
        # 
        if isinstance(self._notebook, Gtk.Notebook):
            sw = self._notebook.get_nth_page(self._notebook.get_current_page())
            sw._label_tab.set_label(os.path.basename(new_path))
            self._lb1.unselect_all()
            sw.grid1.grab_focus()
        
#########

    def update_filter(self, custom_filter, search_text):
        custom_filter.changed(Gtk.FilterChange.DIFFERENT)
    
    def on_show_hidden(self, action=None, param=None):
        _cw = self._notebook.get_nth_page(self._notebook.get_current_page())
        custom_filter = _cw._c_filter
        _cw.is_hidden = not _cw.is_hidden
        self.update_filter(custom_filter, ".")
    
    def on_settings_action(self, action=None, param=None):
        WinSettings(self_main)
    
    # def on_changed(self, text):
        # print('changed to: ',text.get_text())


class PathBar(Gtk.ScrolledWindow):
    
    def __init__(self, _parent):
        super().__init__()
        self._parent = _parent
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.set_child(self.box)
        self.on_path_changed_callback = None
    
    def set_path(self, absolute_path, _int=0):
        child = self.box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.box.remove(child)
            child = next_child
        
        if not absolute_path:
            return
        #
        if absolute_path == "//TRASHCAN":
            btn = Gtk.Button.new_with_label(_lang.TRASHCAN)
            btn.add_css_class("flat")
            self.box.append(btn)
            return
        components = [c for c in absolute_path.split("/") if c]
        current_accumulator = "/"
        is_home = 0
        if absolute_path[0:len(_HOME)] == _HOME:
            is_home = 1
        if is_home:
            self._append_segment_button(0, GLib.get_user_name(), GLib.get_home_dir(), is_last=(len(components) == 0))
        else:
            self._append_segment_button(0, "Root", "/", is_last=(len(components) == 0))
        #
        for i, comp in enumerate(components):
            current_accumulator = os.path.join(current_accumulator, comp)
            is_last = i == len(components) - 1
            if is_home and i in [0,1]:
                continue
            self._append_separator()
            self._append_segment_button(i, comp, current_accumulator, is_last)
        #
        if _int == 0 and isinstance(self._parent._notebook, Gtk.Notebook):
            sw = self._parent._notebook.get_nth_page(self._parent._notebook.get_current_page())
            sw._path = absolute_path
        #
        _adj = self.get_hadjustment()
        GLib.idle_add(lambda: _adj.set_value(_adj.get_upper()))
    
    def _append_segment_button(self, i: int, label: str, target_path: str, is_last: bool):
        btn = Gtk.Button.new()
        btn.add_css_class("flat")
        # if home add an icon
        has_home_icon = 0
        if i == 0 and label == GLib.get_user_name():
            if icon_theme.has_icon("gtk-home"):
                btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                btn_img = Gtk.Image.new_from_icon_name("gtk-home")
                btn_box.append(btn_img)
                btn_box.append(Gtk.Label(label=label))
                btn.set_child(btn_box)
                has_home_icon = 1
        if has_home_icon == 0:
            btn.set_label(label=label)
        if is_last:
            btn.set_sensitive(True)
            btn.add_css_class("suggested-action")
        #
        btn.connect("clicked", self._on_button_clicked, target_path)
        # 
        self.box.append(btn)
    
    def _append_separator(self):
        arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
        arrow.add_css_class("dim-label")
        self.box.append(arrow)
    
    def _on_button_clicked(self, button, target_path):
        if self.on_path_changed_callback:
            self.on_path_changed_callback(target_path)
    
    def connect_path_changed(self, callback):
        self.on_path_changed_callback = callback

class TData(GObject.Object):
    name = GObject.Property(type=str)
    date = GObject.Property(type=str)
    fakename = GObject.Property(type=str)
    def __init__(self, name, date, fakename):
        super().__init__()
        self.name = name
        self.date = date
        self.fakename = fakename

class ScrolWinTrash(Gtk.ScrolledWindow):
    def __init__(self, _parent):
        super().__init__()
        self._parent = _parent
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.propagate_natural_height = 1
        self.propagate_natural_width = 1
        self._path = "//TRASHCAN"
        #
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.set_hexpand(True)
        self.main_box.set_vexpand(True)
        self.set_child(self.main_box)
        ####
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.append(btn_box)
        #
        btn_restore = Gtk.Button.new_with_label(label=_lang.TRESTORE)
        btn_restore.connect("clicked", self.on_restoredelete_btn, "restore")
        btn_box.append(btn_restore)
        #
        fake_w = Gtk.Box(orientation=0,spacing=0)
        fake_w.set_hexpand(True)
        btn_box.append(fake_w)
        #
        btn_delete = Gtk.Button.new_with_label(label=_lang.TDELETE)
        btn_delete.connect("clicked", self.on_restoredelete_btn, "delete")
        btn_box.append(btn_delete)
        #
        btn_empty_trash = Gtk.Button.new_with_label(label=_lang.TEMPTY)
        btn_empty_trash.connect("clicked", self.on_emptytrash_btn)
        btn_box.append(btn_empty_trash)
        ####
        self.swt = Gtk.ScrolledWindow.new()
        self.main_box.append(self.swt)
        self.swt.set_propagate_natural_height(True)
        self.swt.set_propagate_natural_width(True)
        self.swt.set_policy(Gtk.PolicyType.ALWAYS , Gtk.PolicyType.AUTOMATIC)
        ####
        self.on_create_notebook_label()
        #
        self._T = ReadTrash("HOME").return_the_list()
        #
        self.on_liststore()
        #
        self._multi = Gtk.MultiSelection.new(self._ls)
        self._tree = Gtk.ColumnView.new(self._multi)
        self._tree.set_reorderable(False)
        self._tree.set_hexpand(True)
        self._tree.set_vexpand(True)
        self._tree.set_show_row_separators(True)
        self._tree.set_show_column_separators(True)
        self._tree.connect("activate", self.on_tree_activate)
        #
        _colv = Gtk.ColumnViewColumn.new(_lang.FILENAME, None)
        _colv.set_expand(True)
        _colv.set_resizable(True)
        ############
        _factory = Gtk.SignalListItemFactory()
        def f_setup(fact, item):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            #
            icon = Gtk.Image.new()
            icon.set_pixel_size(TRASH_ICON_SIZE)
            box.icon = icon
            box.append(icon)
            #
            lbl = Gtk.Label.new()
            box.lbl = lbl
            box.append(lbl)
            #
            item.set_child(box)
        _factory.connect("setup", f_setup)
        #
        def f_bind(_f, item):
            _fileinfo, box = item.get_item(), item.get_child()
            _name = _fileinfo.name # full path home starting
            fake_name = _fileinfo.fakename # the name in the files folder
            _ff = Gio.File.new_for_path(os.path.join(TRASHCAN_FILES_DIR, fake_name))
            # gio.FileInfo
            _fi = _ff.query_info("standard::icon,owner::user",0,None)
            _ficon = _fi.get_icon()
            #
            box.icon.set_from_gicon(_ficon)
            #
            box.lbl.set_label(os.path.basename(_name))
            box.item_name = _name
            box.item_date = _fileinfo.date
            box.fake_name = _fileinfo.fakename
        _factory.connect("bind", f_bind)
        #
        _colv.set_factory(_factory)
        self._tree.insert_column(0, _colv)
        ############
        _colv2 = Gtk.ColumnViewColumn.new(_lang.ORIGINALEPATH, None)
        _colv2.set_expand(True)
        _colv2.set_resizable(True)
        #
        _factory2 = Gtk.SignalListItemFactory()
        def f_setup2(fact, item):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            lbl2 = Gtk.Label.new()
            box.lbl2 = lbl2
            box.append(lbl2)
            #
            item.set_child(box)
        _factory2.connect("setup", f_setup2)
        #
        def f_bind2(_f, item):
            _fileinfo, box = item.get_item(), item.get_child()
            _name = _fileinfo.name
            box.lbl2.set_label(os.path.dirname(_name))
        _factory2.connect("bind", f_bind2)
        #
        _colv2.set_factory(_factory2)
        self._tree.insert_column(1, _colv2)
        ############
        _colv3 = Gtk.ColumnViewColumn.new(_lang.DELETIONDATE, None)
        _colv3.set_expand(True)
        _colv3.set_resizable(True)
        #
        _factory3 = Gtk.SignalListItemFactory()
        def f_setup3(fact, item):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            lbl3 = Gtk.Label.new()
            box.lbl3 = lbl3
            box.append(lbl3)
            item.set_child(box)
        _factory3.connect("setup", f_setup3)
        #
        def f_bind3(_f, item):
            _fileinfo, box = item.get_item(), item.get_child()
            _date = _fileinfo.date
            _date2 = datetime.datetime.fromisoformat(_date)
            _date3 = _date2.strftime("%x %X")
            box.lbl3.set_label(_date3)
        _factory3.connect("bind", f_bind3)
        #
        _colv3.set_factory(_factory3)
        self._tree.insert_column(2, _colv3)
        #
        self.swt.set_child(self._tree)
        #
        this_dir = Gio.File.new_for_path(TRASHCAN_FILES_DIR)
        self.deleterestore_button_pressed = 0
        try:
            # events: moved in - moved out - renamed - deleted
            self._monitor = this_dir.monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
            self._monitor.connect("changed", self.on_change)
        except GLib.Error as E:
            pass
    
    def on_change(self, _mon, _file, _fother, _event):
        if _event == Gio.FileMonitorEvent.MOVED_IN:
            file_path = _file.get_path()
            ret = self.get_file_data(file_path)
            #
            if ret != -1:
                try:
                    realname, date, fakename = ret
                    _tdata = TData(realname, date, fakename)
                    self._ls.append(_tdata)
                except:
                    pass
        elif _event == Gio.FileMonitorEvent.MOVED_OUT or _event == Gio.FileMonitorEvent.DELETED:
            pass
            # if self.deleterestore_button_pressed == 1:
                # self.deleterestore_button_pressed = 0
            # else:
                # file_path = _file.get_path()
                # #
                # for i in range(self._multi.get_n_items()):
                    # _data_item = self._multi.get_item(i) # is Data object
                    # self._ls.remove(i)
    
    def get_file_data(self, file_path):
        fakename = os.path.basename(file_path)
        info_file = os.path.join(TRASHCAN_FILES_INFO,fakename+".trashinfo")
        if os.path.exists(info_file):
            info_file_data = ""
            with open(info_file, "r") as _f:
                info_file_data = _f.readlines()
            path_tmp = unquote(info_file_data[1].split("=")[1].rstrip())
            realname = path_tmp[len(_HOME)+1:]
            date = info_file_data[2].split("=")[1].rstrip()
            return [realname, date, fakename]
        return -1
    
    def on_tree_activate(self, column_view, position):
        _item = self._multi.get_item(position)
        file_name = os.path.basename(_item.name)
        trash_file_path = os.path.join(TRASHCAN_FILES_DIR, file_name)
        #
        _fl = Gtk.FileLauncher.new(Gio.File.new_for_path(trash_file_path))
        def on_launch_cb(_obj, _res, _d):
            try:
                ret = _obj.launch_finish(_res)
                if ret == False:
                    AlDial(self_main, _fi.get_name())
            except GLib.Error as gerr:
                AlDial(self_main, "{}\n{}".format(_fi.get_name(), gerr.message))
        _fl.launch(None,None,on_launch_cb,None)
        
    def on_restoredelete_btn(self, _w, _type):
        self.deleterestore_button_pressed = 1
        _errors = ""
        n_items = self._multi.get_n_items()
        LIST_TDATA = []
        for i in range(n_items):
            if self._multi.is_selected(i):
                _data_item = self._multi.get_item(i) # is Data object
                LIST_TDATA.append(_data_item)
        for el in reversed(LIST_TDATA):
            if _type == "restore":
                ret = RestoreTrash("HOME", [el]).itemRestore()
                if ret == [1,-1]:
                    ret2 = self._ls.find(el)
                    if ret2[0] == True:
                        self._ls.remove(ret2[1])
                else:
                    _errors += "{}: {}\n".format(_lang.GERROR, os.path.basename(_data_item.name))
            elif _type == "delete":
                ret = DeleteTrash("HOME", [el]).itemDelete()
                if ret == [1,-1]:
                    ret2 = self._ls.find(el)
                    if ret2[0] == True:
                        self._ls.remove(ret2[1])
                else:
                    _errors += "{}: {}\n".format(_lang.GERROR, os.path.basename(_data_item.name))
        if _errors != "":
            self.deleterestore_button_pressed = 0
            SimpleDialog(self_main, _lang.GERRORS, _errors)
    
    def on_emptytrash_btn(self, _w):
        ret = emptyTrash("HOME").tempty()
        if ret == 0:
            self._ls.remove_all()
            expunged_files = os.listdir(TRASHCAN_FILES_EXPUNGED)
            try:
                for _f in expunged_files:
                    os.unlink(_f)
            except Exception as E:
                AlDial(self_main, str(E))
        else:
            AlDial(self_main, _lang.TEMPTYERROR)
        
    def on_liststore(self):
        _list = []
        for el in self._T:
            _list.append([el.realname, el.deletiondate, el.fakename])
        self._ls = Gio.ListStore()
        for el in _list:
            self._ls.append(TData(el[0],el[1],el[2]))
        
    def on_create_notebook_label(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        lbl = Gtk.Label(label=_lang.TRASHCAN) # page label
        lbl.set_hexpand(True)
        box.append(lbl)
        self._label_tab = lbl
        btn = Gtk.Button.new() # page button
        if icon_theme.has_icon("gtk-close"):
            _btn_il = "gtk-close"
        elif icon_theme.has_icon("stock-close"):
            _btn_il = "stock-close"
        elif icon_theme.has_icon("close"):
            _btn_il = "close"
        elif icon_theme.has_icon("window-close"):
            _btn_il = "window-close"
        btn.set_icon_name(_btn_il)
        btn.connect("clicked", self.on_close_this)
        box.append(btn)
        #
        self.tab_label = box
    
    def on_close_this(self, w):
        if self._parent._notebook.get_n_pages() > 1:
            idx = self._parent._notebook.get_current_page()
            self._parent._notebook.remove_page(idx)
            try:
                ret = self._monitor.cancel()
            except:
                pass

# a new page
class ScrolWin(Gtk.ScrolledWindow):
    def __init__(self, _path, _parent):
        super().__init__()
        if not os.path.exists(_path) or not os.access(_path, os.R_OK):
            return None
        self._path = _path
        print("3557", self._path)
        self._parent = _parent
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.propagate_natural_height = 1
        self.propagate_natural_width = 1
        # notebook page label
        self.on_create_notebook_label()
        # Gtk.DirectoryList
        self.grid1 = Gtk.GridView()
        self.grid1.set_orientation(Gtk.Orientation.VERTICAL)
        self.grid1.set_hexpand(True)
        self.grid1.set_vexpand(False)
        self.grid1.set_min_columns(1)
        if USE_RUBBERBAND == 1:
            self.grid1.set_enable_rubberband(True)
        #
        def on_grid_activate(grid, pos):
            _mod = grid.get_model()
            # get selected
            _n_items = multisel.get_n_items()
            for i in range(_n_items):
                if _mod.is_selected(i):
                    # gio.fileinfo
                    _fi = _mod.get_item(i)
                    if _fi.get_file_type() == Gio.FileType.DIRECTORY:
                        new_path = os.path.join(self._path, _fi.get_name())
                        if os.access(new_path, os.R_OK):
                            self._parent.trigger_path_update(new_path)
                            self._path = new_path
                        # else:
                            # print("folder not accessible:: ", new_path)
                    elif _fi.get_file_type() == Gio.FileType.REGULAR:
                        new_path = os.path.join(self._path, _fi.get_name())
                        _fl = Gtk.FileLauncher.new(Gio.File.new_for_path(new_path))
                        def on_launch_cb(_obj, _res, _d):
                            try:
                                ret = _obj.launch_finish(_res)
                                if ret == False:
                                    AlDial(self_main, _fi.get_name())
                            except GLib.Error as gerr:
                                AlDial(self_main, "{}\n{}".format(_fi.get_name(), gerr.message))
                        _fl.launch(None,None,on_launch_cb,None)
        self.grid1.connect("activate", on_grid_activate)
        self.set_child(self.grid1)
        ########
        _dir = Gio.File.new_for_path(_path)
        _m = Gtk.DirectoryList.new(ATTRIBUTES, _dir)
        multisel = Gtk.MultiSelection()
        self._m = _m
        ###
        self.is_hidden = 1
        def filter_func(item, user_data=None):
            if self.is_hidden == 1:
                if item.get_name()[0] != ".":
                    return True
                else:
                    return False
            else:
                return True
                
        custom_filter = Gtk.CustomFilter.new(filter_func)
        self._c_filter = custom_filter
        ###
        def is_dir(info: Gio.FileInfo) -> bool:
            return info.get_file_type() in (Gio.FileType.DIRECTORY, Gio.FileType.MOUNTABLE)
        
        def sort_key(info: Gio.FileInfo) -> str:
            name = info.get_name()
            if name != None:
                k = ("0" if is_dir(info) else "1") + GLib.utf8_collate_key_for_filename(name.casefold(), -1) + "\x00" + name
                return k
            # else:
                # return 0
        
        def _cmp(a, b):
            return (a > b) - (a < b)
        
        def folders_first(a, b) -> int:
            return _cmp(not is_dir(a), not is_dir(b))
        
        def _compare(a, b, _d = None):
            aa = a.get_name()
            bb = b.get_name()
            c = _cmp(sort_key(a), sort_key(b))
            return folders_first(a, b) or (-c if False else c)
            
        _sorter = Gtk.CustomSorter.new(_compare)
        sort_model = Gtk.SortListModel(model=_m, sorter=_sorter)
        #
        multisel = Gtk.MultiSelection()
        #
        filter_model = Gtk.FilterListModel.new(sort_model, custom_filter)
        multisel.set_model(filter_model)
        #
        self.grid1.set_model(multisel)
        ##########
        _m.set_monitored(True)
        ###########
        factory = Gtk.SignalListItemFactory()
        self.NUM_MOD_ITEMS = 0 # used for selecting file passed as argument
        factory.connect("setup", self.f_setup)
        factory.connect("bind", self.f_bind)
        ##########
        self.grid1.set_factory(factory)
        self._model = self.grid1.get_model()
        #####
        # notification from an item the pointer is in
        self.is_inside = False
        #
        self.SELECTED_WIDGET = []
        self.SELECTED_ITEMS = []
        #
        self.ctrl_pressed = 0
        self.shift_pressed = 0
        self.escape_pressed = 0
        # keyboard
        keycontroller = Gtk.EventControllerKey()
        keycontroller.connect('key-pressed', self.on_key_pressed)
        keycontroller.connect('key-released', self.on_key_released)
        self.grid1.add_controller(keycontroller)
        ## main - dragging
        self.dragging_prepare = 0
        self.drag_begin = 0
        # drop
        self.drop_controller = Gtk.DropTarget.new(type=GObject.TYPE_NONE, actions=Gdk.DragAction.COPY)
        self.drop_controller.set_gtypes([self, Gdk.FileList, str])
        self.drop_controller.connect("drop", self.on_drop)
        self.grid1.add_controller(self.drop_controller)
        ##
        # left button
        self._gesture_l = Gtk.GestureClick.new()
        self._gesture_l.set_button(1)
        self.grid1.add_controller(self._gesture_l)
        self._gesture_l.connect('pressed', self.on_gesture_l, 1)
        self.left_click_setted = 0
        # right button
        self._gesture_r = Gtk.GestureClick.new()
        self._gesture_r.set_button(3)
        self.grid1.add_controller(self._gesture_r)
        self._gesture_r.connect('pressed', self.on_gesture_r)
        self.right_click_setted = 0
        #
        self.grid1.grab_focus()
        ### shortcuts
        self._ctrl = Gtk.ShortcutController()
        self.add_controller(self._ctrl)
        # items to the recycle bin
        _ca = Gtk.CallbackAction.new(self.on_trash, None, None)
        _st = Gtk.ShortcutTrigger.parse_string("<Control>r")
        _sc = Gtk.Shortcut.new(_st, _ca)
        self._ctrl.add_shortcut(_sc)
        # open the terminal
        _ca = Gtk.CallbackAction.new(self.on_terminal, None, None)
        _st = Gtk.ShortcutTrigger.parse_string("<Control>t")
        _sc = Gtk.Shortcut.new(_st, _ca)
        self._ctrl.add_shortcut(_sc)
    
    def on_terminal(self, action, param, _path=None, _a=None, _b=None):
        # if isinstance(_a, Gtk.Popover):
            # _a.popdown()
        if _path and os.path.exists(_path):
            _path = _path
        else:
            if len(self.SELECTED_ITEMS) == 1:
                _path = os.path.join(self._path, self.SELECTED_ITEMS[0])
            elif len(self.SELECTED_ITEMS) == 0:
                _path = self._path
        try:
            TERMINAL2 = shutil.which(TERMINAL)
            if TERMINAL_ARG[-1] == "=":
                subprocess.Popen([TERMINAL, "{}{}".format(TERMINAL_ARG,_path)])
                # ret = GLib.spawn_sync(None, [TERMINAL2, "{}{}".format(TERMINAL_ARG, _path)], None, GLib.SpawnFlags.DEFAULT, None, None)
            else:
                subprocess.Popen([TERMINAL, TERMINAL_ARG, _path])
                # ret = GLib.spawn_sync(None, [TERMINAL2, TERMINAL_ARG, _path], None, GLib.SpawnFlags.DEFAULT, None, None)
            # if ret[0] == False:
                # AlDial(self_main, _lang.FAPPERROR)
        except Exception as E:
            AlDial(self_main, str(E))
        
    def on_trash(self, action, param, _a=None, _b=None):
        # only home
        can_trash = 0
        if len(self.SELECTED_ITEMS) > 0:
            if self._path[0:len(_HOME)] == _HOME:
                can_trash = 1
        if can_trash:
            ITEMS_TO_TRASH = []
            for el in self.SELECTED_ITEMS:
                ITEMS_TO_TRASH.append(os.path.join(self._path, el))
            TrashModule(ITEMS_TO_TRASH)
    
    def f_setup(self, fact, item):
        box = ItemBox(self, item)
        ######
        _ol = Gtk.Overlay.new()
        _ol.set_hexpand(True)
        _ol.set_vexpand(True)
        _ol.set_child(box)
        item.set_child(_ol)
        _ol.box = box
        self.NUM_MOD_ITEMS += 1
    
    def f_bind(self, _f, item):
        _gfileinfo, box = item.get_item(), item.get_child().box
        _ol = item.get_child()
        _name = _gfileinfo.get_name()
        box.lbl.set_label(_name)
        box.item_name = _name
        has_thumb = -1
        if CAN_THUMB_EVERYWHERE == 0:
            if len(self._path) >= len(_HOME):
                _path_only_home = self._path[0:len(_HOME)]
                if _path_only_home != _HOME:
                    has_thumb = 0
            else:
                has_thumb = 0
        # thumbnailer
        if CAN_THUMB == 1 and has_thumb == -1:
            has_thumb = self.generate_thumb(box, _gfileinfo, _name, has_thumb)
        #
        if has_thumb == 0:
            _icon = _gfileinfo.get_icon()
            box.icon.set_from_gicon(_icon)
        #
        if _gfileinfo.get_is_symlink():
            if icon_theme.has_icon("link"):
                _il = icon_theme.lookup_icon("link", [], LINK_ICON_SIZE, 1, 0, Gtk.IconLookupFlags.FORCE_REGULAR)
            img_il = Gtk.Image.new_from_paintable(_il)
            img_il.set_pixel_size(LINK_ICON_SIZE)
            img_il.set_halign(Gtk.Align.END)
            img_il.set_valign(Gtk.Align.START)
            _ol.add_overlay(img_il)
        # scroll to item to select
        if _name[0] != ".":
            if self._parent.file_to_select != None:
                if self._parent.file_to_select == _name:
                    # self._model.select_item(self.NUM_MOD_ITEMS-1, False)
                    self._parent.file_to_select = None
                    self.grid1.scroll_to(self.NUM_MOD_ITEMS-1, Gtk.ListScrollFlags.SELECT, None)
    
    def generate_thumb(self, box, _gfileinfo, _name, has_thumb):
        thumbnailerN = GnomeDesktop.DesktopThumbnailFactory.new(THUMBNAIL_SIZE)
        tf = Gio.File.new_for_path(os.path.join(self._path, _name))
        _uri = tf.get_uri()
        _mtime = _gfileinfo.get_modification_date_time().to_unix()
        # can be None or str
        _thumb_path = thumbnailerN.lookup(_uri, _mtime)
        #
        if _thumb_path == None:
            # can be False or True
            _thumb_path_failed = thumbnailerN.has_valid_failed_thumbnail(_uri, _mtime)
            if _thumb_path_failed == True:
                has_thumb = 0
            else:
                #
                try:
                    mime_type = _gfileinfo.get_content_type()
                    icon_pixbuf = thumbnailerN.generate_thumbnail(_uri, mime_type, None)
                    # True or False
                    ret = thumbnailerN.save_thumbnail(icon_pixbuf, _uri, _mtime, None)
                    _thumb_path = thumbnailerN.lookup(_uri, _mtime)
                    has_thumb = 1
                except GLib.Error as E:
                    # generate failed thumbnailer - True or False
                    ret = thumbnailerN.create_failed_thumbnail(_uri, _mtime, None)
                    has_thumb = 0
        else:
            try:
                box.icon.set_from_file(_thumb_path)
                has_thumb = -1
            except:
                has_thumb = 0
        if has_thumb == 1:
            _texture_img = Gdk.Texture.new_for_pixbuf(icon_pixbuf)
            if isinstance(_texture_img, Gdk.Texture):
                box.icon.set_from_paintable(_texture_img)
            else:
                has_thumb = 0
        return has_thumb
        
    def on_close_this(self, w):
        if self._parent._notebook.get_n_pages() > 1:
            idx = self._parent._notebook.get_current_page()
            self._parent._notebook.remove_page(idx)
        
    def on_create_notebook_label(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        if self._path == "/":
            lbl = Gtk.Label(label=_lang.ROOTDIR) # page label
        else:
            lbl = Gtk.Label(label=os.path.basename(self._path)) # page label
        box.set_tooltip_text(self._path)
        lbl.set_hexpand(True)
        box.append(lbl)
        self._label_tab = lbl
        btn = Gtk.Button.new() # page button
        if icon_theme.has_icon("gtk-close"):
            _btn_il = "gtk-close"
        elif icon_theme.has_icon("stock-close"):
            _btn_il = "stock-close"
        elif icon_theme.has_icon("close"):
            _btn_il = "close"
        elif icon_theme.has_icon("window-close"):
            _btn_il = "window-close"
        btn.set_icon_name(_btn_il)
        btn.connect("clicked", self.on_close_this)
        box.append(btn)
        #
        self.tab_label = box
        
    # mouse pressed (1) and released (0)
    def on_gesture_l(self, o,n,x,y, _t):
        if self.is_inside != False:
            return
        if self.ctrl_pressed == 1:
            return
        # unselect all
        if _t == 1:
            _mod = self.grid1.get_model()
            _mod.unselect_all()
            self.SELECTED_WIDGET = []
            self.SELECTED_ITEMS = []
    
    # da fare: con x e y cercare il box e se trovo uno fare nulla
    def on_gesture_r(self, o,n,x,y):
        if self.is_inside != False:
            return
        if self.ctrl_pressed == 1:
            return
        # unselect all
        _mod = self.grid1.get_model()
        _mod.unselect_all()
        self.SELECTED_WIDGET = []
        self.SELECTED_ITEMS = []
        # show the contextual menu
        # window - scrollwindow
        _popover = WinPopover(self._parent,self,self._path,-99,[x,y])
    
    def on_key_pressed(self, event, keyval, keycode, state):
        if keyval == Gdk.KEY_Control_L or keyval == Gdk.KEY_Control_R:
            self.ctrl_pressed = 1
        elif keyval == Gdk.KEY_Shift_L or keyval == Gdk.KEY_Shift_R:
            self.shift_pressed = 1
        elif keyval == Gdk.KEY_Escape:
            self.escape_pressed = 1
        elif keyval == Gdk.KEY_Delete:
            self.on_trash(None, None, None, None)
    
    def on_key_released(self, event, keyval, keycode, state):
        self.ctrl_pressed = 0
        self.shift_pressed = 0
        self.escape_pressed = 0
    
    def on_drag_prepare(self, ctrl, _x, _y, data=None):
        self.dragging_prepare = 1
        #
        SELECTED_ITEMS = []
        _data = ""
        _mod = self.grid1.get_model()
        # get selected
        _n_items = _mod.get_n_items()
        for i in range(_n_items):
            if _mod.is_selected(i):
                # gfileinfo
                _fi = _mod.get_item(i)
                full_path = os.path.join(self._path,_fi.get_name())
                _fg = Gio.File.new_for_path(full_path)
                file_uri = _fg.get_uri()
                SELECTED_ITEMS.append(file_uri)
                _data += (file_uri+"\n")
        if len(SELECTED_ITEMS) == 0:
            return None
        _data = _data[:-1]+"\r\n"
        #
        if self.shift_pressed == 1:
            ctrl.set_actions(Gdk.DragAction.MOVE)
        elif self.shift_pressed == 0:
            ctrl.set_actions(Gdk.DragAction.COPY)
        
        gbytes = GLib.Bytes.new(bytes(_data, 'utf-8'))
        _atom = "text/uri-list"
        content = Gdk.ContentProvider.new_for_bytes(_atom, gbytes)
        return content
    
    def on_drag_begin(self, ctrl, drag):
        self.drag_begin = 1
    
    def on_drag_end(self, ctrl, drag, data=None):
        self.dragging_prepare = 0
        self.drag_begin = 0
    
    # dropping items in this program
    # _source: [__gi__.GLocalFile] - _dest: "destination_directory" - _operation: copy cut
    def on_copy_cup_operation(self,_source,_dest,_operation):
        path_source = []
        for ff in _source:
            path_source.append(ff.get_path())
        thread_object = object
        _thread = copy_file_function(path_source,_dest,_operation, None, None, thread_object, 0)
    
    def on_drop(self, ctrl, value, _x, _y):
        _operation = ""
        if  ctrl.get_actions() == Gdk.DragAction.COPY:
            _operation = "copy"
        elif ctrl.get_actions() == Gdk.DragAction.MOVE:
            _operation = "cut"
        
        if _operation == "":
            return
        
        # external item moving
        if isinstance(value, Gdk.FileList) and value != []:
            files = value.get_files()
            self.cancel_op = -1
            OW = None
            ##########
            # exactly the same directory
            if os.path.dirname(files[0].get_path()) == self._path:
                AlDial(self_main, _lang.SAMEITEMEXIST)
                return
            self.on_copy_cup_operation(files,self._path,_operation)
            return
            ##########
        return
        
    def on_dir_changed(self, _directorylist, _pos , _removed, _added):
        _item = _directorylist.get_item(_pos)
        # if _item != None:
            # print("changed:: ", _item.get_name()) # gfileinfo
        if self.is_first_start == 0:
            self.is_first_start = 1
        return
        ########
        _gi = _d.get_file()
        
################## TRASHCAN ############## 

class TrashItems():
    def __init__(self):
        self.fakename = ""
        self.realname = ""
        self.deletiondate = ""

# only HOME
class mountPoint():
    def __init__(self, mpath):
        self.path = mpath
        
    # find the trash directory of the given device
    def find_trash_path(self):
        trash_path = ""
        if self.path == "HOME":
            trash_path = os.path.join(os.path.expanduser("~"), ".local/share/Trash")
        else:
            user_id = os.getuid()
            trash_path = os.path.join(self.path, ".Trash-"+str(user_id))
        return trash_path

# read the trash directory
class ReadTrash():
    def __init__(self, tpath):
        self.tpath = tpath
        # HOME trash path
        self.Ttrash = mountPoint(self.tpath).find_trash_path()
        self.Tfiles = os.path.join(self.Ttrash, "files")
        self.Tinfo = os.path.join(self.Ttrash, "info")
        self.can_read_trash = 0
        self.Ttrash_can_read_trash()
        
    def Ttrash_can_read_trash(self):
        if not os.path.exists(self.Ttrash) or not os.path.exists(self.Tfiles) or not os.path.exists(self.Tinfo):
            return
        if not os.access(self.Tfiles, os.R_OK) or not os.access(self.Tinfo, os.R_OK):
            return
        #
        self.can_read_trash = 1
        return
    
    def trashed_items(self):
        list_trasheditems = []
        info_items = os.listdir(self.Tinfo)
        for iitem in info_items:
            try:
                with open(os.path.join(self.Tinfo, iitem), 'r') as read_data:
                    read_data.readline()
                    fake_name = os.path.splitext(os.path.basename(iitem))[0]
                    spath = unquote(read_data.readline())[5:].rstrip()
                    deletion_date = read_data.readline()[13:].rstrip()
                    diskpart = TrashItems()
                    diskpart.fakename = fake_name
                    if self.tpath == "HOME":
                        diskpart.realname = spath[len(os.path.expanduser('~'))+1:]
                    else:
                        diskpart.realname = spath
                    diskpart.deletiondate = deletion_date
                    list_trasheditems.append(diskpart)
            except:
                return -1
        #
        return list_trasheditems
    
    # the current list of the items in the trashcan
    def return_the_list(self):
        if self.can_read_trash:
            self.items_in_trash = self.trashed_items()
        else:
            return -2
        if self.items_in_trash != -1:
            return self.items_in_trash
        else:
            return -1

# restore the selected item
class RestoreTrash():
    def __init__(self, tpath, items_in_trash):
        self.items_in_trash = items_in_trash
        self.Ttrash = mountPoint(tpath).find_trash_path()
        self.Tfiles = os.path.join(self.Ttrash, "files")
        self.Tinfo = os.path.join(self.Ttrash, "info")
        self.can_restore = 0
        self.Ttrash_can_restore()

    def Ttrash_can_restore(self):
        if not os.access(self.Tfiles, os.W_OK) or not os.access(self.Tinfo, os.W_OK):
            return
        else:
            self.can_restore = 1
    
    # restore the selected item
    def itemRestore(self):
        if self.can_restore:
            iitem = self.items_in_trash[0]
            fake_name = iitem.fakename
            real_name = os.path.basename(iitem.name) # has full path from home folder
            file_full_path = os.path.join(_HOME, iitem.name)
            ret = os.path.exists(file_full_path)
            if ret:
                file_full_path = self.setNewname(file_full_path)
            try:
                shutil.move(os.path.join(self.Tfiles, fake_name), file_full_path)
                fake_path = os.path.join(self.Tinfo, fake_name+".trashinfo")
                os.unlink(fake_path)
            except Exception as E:
                return str(E)
            return [1,-1]
        else:
            return -2
    
    def setNewname(self, oldName):
        return add_file_sfx(oldName)

# delete the selected item
class DeleteTrash():
    def __init__(self, tpath, items_in_trash):
        self.items_in_trash = items_in_trash
        self.Ttrash = mountPoint(tpath).find_trash_path()
        self.Tfiles = os.path.join(self.Ttrash, "files")
        self.Tinfo = os.path.join(self.Ttrash, "info")
        self.can_delete = 0
        self.Ttrash_can_delete()

    def Ttrash_can_delete(self):
        if not os.access(self.Tfiles, os.W_OK) or not os.access(self.Tinfo, os.W_OK):
            return
        else:
            self.can_delete = 1
    
    # delete the item
    def itemDelete(self):
        if self.can_delete:
            iitem = self.items_in_trash[0]
            fake_name = iitem.fakename
            real_name = os.path.basename(iitem.name)
            full_fake_name = os.path.join(self.Tfiles, fake_name)
            item_trashinfo = os.path.join(self.Tinfo, fake_name+".trashinfo")
            if os.path.isdir(full_fake_name):
                try:
                    shutil.rmtree(full_fake_name)
                    os.unlink(item_trashinfo)
                except Exception as E:
                    return str(E)
            else:
                try:
                    os.unlink(full_fake_name)
                    os.unlink(item_trashinfo)
                except Exception as E:
                    return str(E)
            return [1,-1]
        else:
            return -2

# empty the trashcan
class emptyTrash():
    def __init__(self, tpath):
        self.tpath = tpath
        self.Ttrash = mountPoint(tpath).find_trash_path()
        self.Tfiles = os.path.join(self.Ttrash, "files")
        self.Tinfo = os.path.join(self.Ttrash, "info")
        self.can_delete = 0
        self.Ttrash_can_delete()
    
    def Ttrash_can_delete(self):
        if not os.access(self.Tfiles, os.W_OK) or not os.access(self.Tinfo, os.W_OK):
            return
        else:
            self.can_delete = 1
        
    # empty the trashcan
    def tempty(self):
        if self.can_delete:
            ret = 0
            for ffile in os.listdir(self.Tfiles):
                ffile_path = os.path.join(self.Tfiles, ffile)
                if os.path.isfile(ffile_path) or os.path.islink(ffile_path):
                    try:
                        os.unlink(ffile_path)
                    except:
                        ret = -1
                elif os.path.isdir(ffile_path):
                    try:
                        shutil.rmtree(ffile_path)
                    except:
                        ret = -1
                else:
                    try:
                        os.unlink(ffile_path)
                    except:
                        ret = -1
                    
            for ffile in os.listdir(self.Tinfo):
                ffile_path = os.path.join(self.Tinfo, ffile)
                try:
                    os.unlink(ffile_path)
                except:
                    ret = -1
            return ret
        else:
            return -2


class TrashIsEmpty():
    def __init__(self, path):
        self.path = path
        self.trash_path = mountPoint(self.path).find_trash_path()
        self.Tfiles = os.path.join(self.trash_path, "files")
        
    def isEmpty(self):
        if os.path.exists(self.Tfiles):
            iitems = os.listdir(self.Tfiles)
            if len(iitems) > 0:
                return 1
            else:
                return 0
        else:
            return 0

class TrashModule():
    def __init__(self, list_items):
        self.list_items = list_items
        self.trash_path = self.find_trash_path(self.list_items[0])
        self.Tfiles = TRASHCAN_FILES_DIR
        self.Tinfo = TRASHCAN_FILES_INFO
        self.can_trash = 0
        self.Ttrash_can_trash()
        #
        if self.can_trash:
            self.Tcan_trash(self.list_items)

    def find_trash_path(self, path):
        mount_point = ""
        trash_path = None
        while not os.path.ismount(path):
            path = os.path.dirname(path)
        mount_point = path
        #
        if mount_point == "/home" or mount_point == "/":
            trash_path = os.path.join(_HOME, ".local/share/Trash")
        else:
            user_id = os.getuid()
            trash_path = os.path.join(mount_point, ".Trash-"+str(user_id))
        return trash_path

    def Ttrash_can_trash(self):
        if not os.path.exists(self.trash_path):
            if os.access(os.path.dirname(self.trash_path), os.W_OK):
                try:
                    os.mkdir(self.trash_path, 0o700)
                    os.mkdir(self.Tfiles, 0o700)
                    os.mkdir(self.Tinfo, 0o700)
                    self.can_trash = 1
                except Exception as E:
                    AlDial(self_main, str(E))
                    return
                finally:
                    return
            else:
                AlDial(self_main, _lang.TRASHCANPROBLEM)
                return
        #
        if not os.access(self.Tfiles, os.W_OK):
            AlDial(self_main, _lang.TRASHCANPROBLEM)
            return
        if not os.access(self.Tinfo, os.W_OK):
            AlDial(self_main, _lang.TRASHCANPROBLEM)
            return
        #
        if os.access(self.trash_path, os.W_OK):
            if not os.path.exists(self.Tfiles):
                try:
                    os.mkdir(self.Tfiles, 0o700)
                except Exception as E:
                    AlDial(self_main, str(E))
                    return
            if not os.path.exists(self.Tinfo):
                try:
                    os.mkdir(self.Tinfo, 0o700)
                except Exception as E:
                    AlDial(self_main, str(E))
                    return
            self.can_trash = 1
            return
        else:
            AlDial(self_main, _lang.TRASHCANPROBLEM)
            return
        
    def Tcan_trash(self, list_items):
        for item_path in list_items:
            item = os.path.basename(item_path)
            tnow = datetime.datetime.now()
            del_time = tnow.strftime("%Y-%m-%dT%H:%M:%S")
            item_uri = quote("file://{}".format(item_path), safe='/:?=&')[7:]
            if os.path.exists(os.path.join(self.Tinfo, item+".trashinfo")):
                basename, suffix = os.path.splitext(item)
                i = 2
                aa = basename+"."+str(i)+suffix+".trashinfo"
                #
                while os.path.exists(os.path.join(self.Tinfo, basename+"."+str(i)+suffix+".trashinfo")):
                    i += 1
                else:
                    item = basename+"."+str(i)+suffix
            #
            try:
                shutil.move(item_path, os.path.join(self.Tfiles, item))
            except Exception as E:
                AlDial(self_main, str(E))
                continue
            ifile = open(os.path.join(self.Tinfo, "{}.trashinfo".format(item)),"w")
            ifile.write("[Trash Info]\n")
            ifile.write("Path={}\n".format(item_uri))
            ifile.write("DeletionDate={}\n".format(del_time))
            ifile.close()

################## END TRASHCAN ###############

class SignalObject(GObject.Object):
    
    def __init__(self):
        GObject.Object.__init__(self)
        self._name = ""
        self.value = -999
        self._list = []
    
    @GObject.Property(type=str)
    def propName(self):
        'Read-write integer property.'
        return self._name

    @propName.setter
    def propName(self, name):
        self._name = name
    
    @GObject.Property(type=int)
    def propInt(self):
        'Read-write integer property.'
        return self.value

    @propInt.setter
    def propInt(self, value):
        self.value = value
    
    @GObject.Property(type=object)
    def propList(self):
        'Read-write integer property.'
        return self._list

    @propList.setter
    def propList(self, data):
        self._list = [data]
    
##################

class WinSettings(Gtk.Window):
    def __init__(self, _parent):
        super().__init__()
        self._parent = _parent
        self.set_transient_for(self._parent)
        self.set_destroy_with_parent(True)
        self.set_name("settingdialog")
        self.set_resizable(True)
        self.set_size_request(800, 800)
        self.set_title("Settings")
        # 
        self.headerbar = Gtk.HeaderBar.new()
        self.set_titlebar(self.headerbar)
        self.headerbar.set_show_title_buttons(False)
        #
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self.main_box)
        #
        self.stack_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.append(self.stack_box)
        #
        self.stack_sidebar = Gtk.StackSidebar.new()
        self.stack_sidebar.set_vexpand(True)
        self.stack_box.append(self.stack_sidebar)
        #
        btn_apply = Gtk.Button(label=_lang.APPLY)
        btn_apply.connect("clicked", self.on_apply)
        self.headerbar.pack_start(btn_apply)
        #
        btn_close = Gtk.Button(label=_lang.CLOSE)
        btn_close.connect("clicked", self.on_close)
        self.headerbar.pack_end(btn_close)
        #
        self._stack = Gtk.Stack.new()
        self._stack.props.hexpand = True
        self._stack.props.vexpand = True
        self.stack_sidebar.set_stack(self._stack)
        self.stack_box.append(self._stack)
        ############
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sw1 = Gtk.ScrolledWindow.new()
        sw1.set_propagate_natural_width(True)
        sw1.set_child(box1)
        #
        self._stack.add_titled(sw1,"box1",_lang.PGENERAL)
        bgrid1 = Gtk.Grid.new()
        bgrid1.set_column_homogeneous(False)
        bgrid1.set_hexpand(True)
        bgrid1.set_vexpand(True)
        box1.append(bgrid1)
        # icon size
        lbl11 = Gtk.Label(label=_lang.PICONSIZE)
        lbl11.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl11,0,0,1,1)
        self.iconsize_spinbtn = Gtk.SpinButton.new_with_range(0,1024,1)
        self.iconsize_spinbtn.set_value(ICON_SIZE)
        bgrid1.attach_next_to(self.iconsize_spinbtn,lbl11,1,1,1)
        # cell width
        lbl12 = Gtk.Label(label=_lang.PCELLWIDTH)
        lbl12.set_halign(Gtk.Align.START)
        lbl12.set_tooltip_text(_lang.PCELLWIDTH2)
        bgrid1.attach(lbl12,0,1,1,1)
        self.cellw_spinbtn = Gtk.SpinButton.new_with_range(0,400,1)
        self.cellw_spinbtn.set_value(BOX_SIZE_W-ICON_SIZE)
        bgrid1.attach_next_to(self.cellw_spinbtn,lbl12,1,1,1)
        # cell height
        lbl13 = Gtk.Label(label=_lang.PCELLHEIGHT)
        lbl13.set_halign(Gtk.Align.START)
        lbl13.set_tooltip_text(_lang.PCELLHEIGHT2)
        bgrid1.attach(lbl13,0,2,1,1)
        self.cellh_spinbtn = Gtk.SpinButton.new_with_range(0,400,1)
        self.cellh_spinbtn.set_value(BOX_SIZE_H-ICON_SIZE)
        bgrid1.attach_next_to(self.cellh_spinbtn,lbl13,1,1,1)
        # link emblem size
        lbl14 = Gtk.Label(label=_lang.PLINKICONSIZE)
        lbl14.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl14,0,3,1,1)
        self.link_spinbtn = Gtk.SpinButton.new_with_range(0,256,1)
        self.link_spinbtn.set_value(LINK_ICON_SIZE)
        bgrid1.attach_next_to(self.link_spinbtn,lbl14,1,1,1)
        # left panel icon size
        lbl15 = Gtk.Label(label=_lang.PPANELICONSIZE)
        lbl15.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl15,0,4,1,1)
        self.panel_spinbtn = Gtk.SpinButton.new_with_range(0,1000,1)
        self.panel_spinbtn.set_value(PANEL_ICON_SIZE)
        bgrid1.attach_next_to(self.panel_spinbtn,lbl15,1,1,1)
        # recycle bin view icon size
        lbl16 = Gtk.Label(label=_lang.PTRASHVIEWICONSIZE)
        lbl16.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl16,0,5,1,1)
        self.trashviconsize_spinbtn = Gtk.SpinButton.new_with_range(0,256,1)
        self.trashviconsize_spinbtn.set_value(TRASH_ICON_SIZE)
        bgrid1.attach_next_to(self.trashviconsize_spinbtn,lbl16,1,1,1)
        # # 
        # lbl17 = Gtk.Label(label=_lang.PSERVICEICONSIZE)
        # lbl17.set_halign(Gtk.Align.START)
        # bgrid1.attach(lbl17,0,6,1,1)
        # self.serviceiconsize_spinbtn = Gtk.SpinButton.new_with_range(0,256,1)
        # self.serviceiconsize_spinbtn.set_value(TRASH_ICON_SIZE)
        # # self.serviceiconsize_spinbtn.connect('value-changed', self.on_spinbtn, "service_icon_size")
        # bgrid1.attach_next_to(self.serviceiconsize_spinbtn,lbl17,1,1,1)
        # icon size while dragging
        lbl18 = Gtk.Label(label=_lang.PDRAGICONSIZE)
        lbl18.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl18,0,7,1,1)
        self.dragiconsize_spinbtn = Gtk.SpinButton.new_with_range(0,256,1)
        self.dragiconsize_spinbtn.set_value(DRAG_ICON_SIZE)
        bgrid1.attach_next_to(self.dragiconsize_spinbtn,lbl18,1,1,1)
        # item(s) property dialog width
        lbl19 = Gtk.Label(label=_lang.PPROPERTYDIALOGWIDTH)
        lbl19.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl19,0,8,1,1)
        self.propdialogw_spinbtn = Gtk.SpinButton.new_with_range(0,1000,1)
        self.propdialogw_spinbtn.set_value(PDWIDTH)
        bgrid1.attach_next_to(self.propdialogw_spinbtn,lbl19,1,1,1)
        # dialog width
        lbl20 = Gtk.Label(label=_lang.PDIALOGWIDTH)
        lbl20.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl20,0,9,1,1)
        self.pdialogw_spinbtn = Gtk.SpinButton.new_with_range(0,1000,1)
        self.pdialogw_spinbtn.set_value(DWIDTH)
        bgrid1.attach_next_to(self.pdialogw_spinbtn,lbl20,1,1,1)
        # dialog height
        lbl21 = Gtk.Label(label=_lang.PDIALOGHEIGHT)
        lbl21.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl21,0,10,1,1)
        self.pdialogh_spinbtn = Gtk.SpinButton.new_with_range(0,1000,1)
        self.pdialogh_spinbtn.set_value(DHEIGHT)
        bgrid1.attach_next_to(self.pdialogh_spinbtn,lbl21,1,1,1)
        # use the rubberband
        lbl22 = Gtk.Label(label=_lang.PUSERUBBERBAND)
        lbl22.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl22,0,11,1,1)
        self.userubberband_combo = Gtk.DropDown.new_from_strings([_lang.NO, _lang.YES])
        self.userubberband_combo.set_selected(USE_RUBBERBAND)
        bgrid1.attach_next_to(self.userubberband_combo,lbl22,1,1,1)
        # box internal spacing
        lbl23 = Gtk.Label(label=_lang.PBOX_INTERNAL_SPACING)
        lbl23.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl23,0,12,1,1)
        self.boxinternal_spinbtn = Gtk.SpinButton.new_with_range(0,40,1)
        self.boxinternal_spinbtn.set_value(BOX_INTERNAL_SPACING)
        bgrid1.attach_next_to(self.boxinternal_spinbtn,lbl23,1,1,1)
        # terminal name
        lbl110 = Gtk.Label(label=_lang.PTERMINAL)
        lbl110.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl110,0,13,1,1)
        self.buffer_terminal = Gtk.EntryBuffer.new(TERMINAL, -1)
        self.entry_terminal = Gtk.Entry.new_with_buffer(self.buffer_terminal)
        bgrid1.attach_next_to(self.entry_terminal,lbl110,1,1,1)
        # terminal argument
        lbl111 = Gtk.Label(label=_lang.PTERMINALARGS)
        lbl111.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl111,0,14,1,1)
        self.buffer_terminalargs = Gtk.EntryBuffer.new(TERMINAL_ARG, -1)
        self.entry_terminalargs = Gtk.Entry.new_with_buffer(self.buffer_terminalargs)
        bgrid1.attach_next_to(self.entry_terminalargs,lbl111,1,1,1)
        # use the thumbnailers
        lbl112 = Gtk.Label(label=_lang.PCANTHUMB)
        lbl112.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl112,0,15,1,1)
        self.canthumb_combo = Gtk.DropDown.new_from_strings([_lang.NO, _lang.YES])
        self.canthumb_combo.set_selected(CAN_THUMB)
        bgrid1.attach_next_to(self.canthumb_combo,lbl112,1,1,1)
        # use the thumbnailers not only for the home folder
        lbl113 = Gtk.Label(label=_lang.PCANTHUMBEVERYWHERE)
        lbl113.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl113,0,16,1,1)
        self.humbhome_combo = Gtk.DropDown.new_from_strings([_lang.NO, _lang.YES])
        self.humbhome_combo.set_selected(CAN_THUMB_EVERYWHERE)
        bgrid1.attach_next_to(self.humbhome_combo,lbl113,1,1,1)
        # thumbnail size to store
        lbl114 = Gtk.Label(label=_lang.PTHUMBSIZE)
        lbl114.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl114,0,17,1,1)
        self.thumbsize_combo = Gtk.DropDown.new_from_strings([_lang.PTNORMAL, _lang.PTLARGE, _lang.PTLARGEX, _lang.PTLARGEXX])
        self.thumbsize_combo.set_selected(THUMBNAIL_SIZE)
        bgrid1.attach_next_to(self.thumbsize_combo,lbl114,1,1,1)
        # disc to not show in the view
        lbl115 = Gtk.Label(label=_lang.PMEDIASKIP)
        lbl115.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl115,0,18,1,1)
        self.buffer_mediaskip = Gtk.EntryBuffer.new(MEDIA_SKIP_TMP, -1)
        self.entry_mediaskip = Gtk.Entry.new_with_buffer(self.buffer_mediaskip)
        bgrid1.attach(self.entry_mediaskip,0,19,2,1)
        self.entry_mediaskip.set_hexpand(True)
        self.entry_mediaskip.set_tooltip_text(_lang.PENTRYMEDIA)
        ########
        self.present()
    
    def on_apply(self, w):
        global WWIDTH # config_conf["wwidth"] # this program width
        global WHEIGHT # config_conf["wheight"] # this program height
        global LATERAL_PANEL_WIDTH # config_conf["panel_lateral_width"] # left panel width
        global DWIDTH # config_conf["dwidth"] # dialog width
        global DHEIGHT # config_conf["dheight"] # dialog height
        global PDWIDTH # config_conf["pwidth"] # property dialog width
        global USE_RUBBERBAND # config_conf["use_rubberband"] # enable the rubberband
        global ICON_SIZE # config_conf["icon_size"] # item icon size
        global SERVICE_ICON_SIZE # config_conf["service_icon_size"] # icons in the switcher and others
        global DRAG_ICON_SIZE # config_conf["drag_icon_size"] # the size of the icon while dragging
        global BOX_SIZE_W # config_conf["box_size_w"] # each item width
        global BOX_SIZE_H # config_conf["box_size_h"] # each item height
        global BOX_INTERNAL_SPACING # config_conf["box_internal_spacing"] # each surrounding item spacing
        global LINK_ICON_SIZE # config_conf["link_icon_size"] # link icon size
        global PANEL_ICON_SIZE # config_conf["panel_icon_size"] # lateral panel icon size
        global TRASH_ICON_SIZE # config_conf["trashview_icon_size"] # trashcan view
        global TERMINAL # config_conf["terminal"]
        global TERMINAL_ARG # config_conf["terminal_args"]
        global CAN_THUMB # config_conf["can_thumb"]
        global CAN_THUMB_EVERYWHERE # config_conf["can_thumb_everywhere"]
        global THUMBNAIL_SIZE # config_conf["thumbnail_size"]
        global MEDIA_SKIP_TMP # config_conf["media_skip"]
        global MEDIA_SKIP
        #
        WWIDTH = self._parent.get_width()
        config_conf["wwidth"] = self._parent.get_width()
        WHEIGHT = self._parent.get_height()
        config_conf["wheight"] = self._parent.get_height()
        LATERAL_PANEL_WIDTH = self._parent.main_paned.get_position()
        config_conf["panel_lateral_width"] = self._parent.main_paned.get_position()
        DWIDTH = int(self.pdialogw_spinbtn.get_value())
        config_conf["dwidth"] = int(self.pdialogw_spinbtn.get_value())
        DHEIGHT = int(self.pdialogh_spinbtn.get_value())
        config_conf["dheight"] = int(self.pdialogh_spinbtn.get_value())
        PDWIDTH = int(self.propdialogw_spinbtn.get_value())
        config_conf["pwidth"] = int(self.propdialogw_spinbtn.get_value())
        USE_RUBBERBAND = self.userubberband_combo.get_selected()
        config_conf["use_rubberband"] = self.userubberband_combo.get_selected()
        ICON_SIZE = int(self.iconsize_spinbtn.get_value())
        config_conf["icon_size"] = int(self.iconsize_spinbtn.get_value())
        # SERVICE_ICON_SIZE = self.serviceiconsize_spinbtn.get_digits()
        # config_conf["service_icon_size"] = self.serviceiconsize_spinbtn.get_digits()
        config_conf["service_icon_size"] = SERVICE_ICON_SIZE
        DRAG_ICON_SIZE = int(self.dragiconsize_spinbtn.get_value())
        config_conf["drag_icon_size"] = int(self.dragiconsize_spinbtn.get_value())
        BOX_SIZE_W = ICON_SIZE+int(self.cellw_spinbtn.get_value())
        config_conf["box_size_w"] = int(self.cellw_spinbtn.get_value())
        BOX_SIZE_H = ICON_SIZE+int(self.cellh_spinbtn.get_value())
        config_conf["box_size_h"] = int(self.cellh_spinbtn.get_value())
        BOX_INTERNAL_SPACING = int(self.boxinternal_spinbtn.get_value())
        config_conf["box_internal_spacing"] = int(self.boxinternal_spinbtn.get_value())
        LINK_ICON_SIZE = int(self.link_spinbtn.get_value())
        config_conf["link_icon_size"] = int(self.link_spinbtn.get_value())
        PANEL_ICON_SIZE = int(self.panel_spinbtn.get_value())
        config_conf["panel_icon_size"] = int(self.panel_spinbtn.get_value())
        TRASH_ICON_SIZE = int(self.trashviconsize_spinbtn.get_value())
        config_conf["trashview_icon_size"] = int(self.trashviconsize_spinbtn.get_value())
        TERMINAL = self.buffer_terminal.get_text()
        config_conf["terminal"] = self.buffer_terminal.get_text()
        TERMINAL_ARG = self.buffer_terminalargs.get_text()
        config_conf["terminal_args"] = self.buffer_terminalargs.get_text()
        CAN_THUMB = self.canthumb_combo.get_selected()
        config_conf["can_thumb"] = self.canthumb_combo.get_selected()
        CAN_THUMB_EVERYWHERE = self.humbhome_combo.get_selected()
        config_conf["can_thumb_everywhere"] = self.humbhome_combo.get_selected()
        THUMBNAIL_SIZE = self.thumbsize_combo.get_selected()
        config_conf["thumbnail_size"] = self.thumbsize_combo.get_selected()
        MEDIA_SKIP_TMP = self.buffer_mediaskip.get_text()
        config_conf["media_skip"] = self.buffer_mediaskip.get_text()
        MEDIA_SKIP = MEDIA_SKIP_TMP.split(";")
        #
        try:
            _ff =  open(os.path.join(HOME_CONFIG,"configs/config.json"), "w")
            json.dump(config_conf, _ff, indent = 4)
            _ff.close()
        except Exception as E:
            AlDial(self_main, str(E))
        #
        self.destroy()
    
    def on_close(self, w):
        self.destroy()
    
###################

class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # # (detailed_action_name, accels)
        # # self.set_accels_for_action("win.OpenWith", ["<Control>Z"])
        self.set_accels_for_action("win.Terminal", ["<Control>t"])
        # self.set_accels_for_action("win.Copy", ["<Control>C"])
        # self.set_accels_for_action("win.Cut", ["<Control>X"])
        # self.set_accels_for_action("win.Paste", ["<Control>V"])
        self.set_accels_for_action("win.Trash", ["<Control>r"])

    def do_activate(self):
        active_window = self.props.active_window
        if active_window:
            active_window.present()
        else:
            self.win = MainWindow(application=self)
            self.win.present()

app = MyApp(application_id="com.horizon.fm4",flags= Gio.ApplicationFlags.NON_UNIQUE)
app.run(None)
