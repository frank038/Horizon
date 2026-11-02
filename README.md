# Horizon
File manager for Linux with the most common features.

May have some unknown issues.

Requirements:
- python3
- Gtk4
- Udisks
- GnomeDesktop (for thumbnailers)

Features:
- recycle bin
- manages mass storage devices
- bookmarks: drag and drop any folder; right mouse click to remove them
- custom scripts (the selected items are passed as argument: each item is separated by a newline, and the list terminates with a newline)
- drag and drop support
- some shortcuts
- a separated language file, very easy to modify or translate into your language; the right file is automatically loaded if found: the file must be in the form LOCALE_OF_YOUR_LANGUAGE.py; if any is found the default en.py will be used
- can be used in portable mode, or can be installed (after creating a proper package o by using other installation methods): the installation directories are /usr/share for the main folder HorizonFM4, and /usr/bin for the script needed to execute the main program; in the folder FILES_FOR_INSTALLATION are the necessary files
- very small, uses only the most common python stuff
- has a graphical setting application for all the supported options
- modern visual thanks to the Gtk4 toolkit.

Behaviour: the thumbnails are generated and/or loaded in sync mode, that means they are all generated before the files and folders will appear.

![My image](https://github.com/frank038/Horizon/blob/main/screenshot.png)
