# -*- coding: utf-8 -*-
import gtk, gedit
from gistory import Gistory
       

class gistoryPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self.instances = {}
        
    def activate(self, window):
        self.instances[window] = PluginHelper(self, window)

    def deactivate(self, window):
        self.instances[window].deactivate()

    def update_ui(self, window):
        self.instances[window].update_ui()        
        

class PluginHelper:
    
    def __init__(self, plugin, window):
        self.window = window
        self.plugin = plugin

        self.ui_id = None
        
        panel = self.window.get_side_panel()
        self.gistory = Gistory(window)

        self.ui_id = panel.add_item(self.gistory, "Edit history", gtk.STOCK_EDIT)
        
        self.action_group = gtk.ActionGroup("gistoryActions")
        self.action_group.add_actions([('gistory_next', gtk.STOCK_EDIT, 'Goto next edit', '<Ctrl>period', '', self.next)])
        self.action_group.add_actions([('gistory_prev', gtk.STOCK_EDIT, 'Goto previous edit', '<Ctrl>comma', '', self.prev)])
        self.manager = self.window.get_ui_manager()
        self.manager.insert_action_group(self.action_group, -1) 
        
        ui_str="""<ui>
            <menubar name="MenuBar">
              <menu name="EditMenu" action="Edit">
                <separator/>
                <menuitem name="gistory_next" action="gistory_next"/>
                <menuitem name="gistory_prev" action="gistory_prev"/>
              </menu>
            </menubar>
            </ui>
            """    
        self._ui_id = self.manager.add_ui_from_string(ui_str)

    def deactivate(self):
        panel = self.window.get_side_panel()
        panel.remove_item(self.gistory)
        manager = self.window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self.action_group)        

        self.window = None
        self.plugin = None

    def update_ui(self):
        pass

    def prev(self, action):
        self.gistory._prev()
        
    def next(self, action):
        self.gistory._next()

