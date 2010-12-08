# -*- coding: utf-8 -*-
import gtk, gedit
import math

class Gistory(gtk.VBox):
    def __init__(self, geditwindow):
        gtk.VBox.__init__(self)

        self.geditwindow = geditwindow
        
        self.nav_mark = -1  # navigation point
        self.marks = {} # TextMarks hash
        self.near_limit = 5 # rows range to consider 'near'
        self.scroll_margin = 5 # rows margin to scroll view
        self.already_working = False    # avoid 'change' event recursion

        # create the gui
        # TODO: use glade to do this
        
        # bottom box
        
        button_prev = gtk.Button() 
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_GO_BACK,gtk.ICON_SIZE_BUTTON)
        button_prev.set_image( img )
        button_prev.connect("clicked", self.button_prev_click)
        
        button_next = gtk.Button() 
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_GO_FORWARD,gtk.ICON_SIZE_BUTTON)
        button_next.set_image( img )
        button_next.connect("clicked", self.button_next_click)

        bottom_box = gtk.HBox(False, 0)
        bottom_box.pack_start(button_prev, False, False)
        bottom_box.pack_start(button_next, False, False)        

        self.pack_start(bottom_box, False, False)        
        
        # the list
        
        # Format:  ID (COUNT)  |  FILE (without path)  |  LINE  |  FILE (with path)
        self.edit_data = gtk.ListStore(str, str, str)
        self.points_list = gtk.TreeView(self.edit_data)
        tree_selection = self.points_list.get_selection()
        tree_selection.set_mode(gtk.SELECTION_SINGLE)
        tree_selection.connect("changed", self.view_point)

        cell_line_number = gtk.TreeViewColumn("Line")
        cell_filename = gtk.TreeViewColumn("File")

        self.points_list.append_column(cell_line_number)
        self.points_list.append_column(cell_filename)

        text_renderer_filename = gtk.CellRendererText()
        text_renderer_line_number = gtk.CellRendererText()

        cell_filename.pack_start(text_renderer_filename, True)
        cell_line_number.pack_start(text_renderer_line_number, True)

        cell_filename.add_attribute(text_renderer_filename, "text", 1)
        cell_line_number.add_attribute(text_renderer_line_number, "text", 2)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.add(self.points_list)

        self.pack_start(scrolled_window)
        
        self.show_all()        
        
        # Set up tab monitoring to keep the list up to date
        
        self.geditwindow.connect("tab_added",self._tab_added)
        

    # open the file at the edit point
    def view_point(self, widget):
        if self.already_working: # avoid recursion
            return        
        tree_selection = self.points_list.get_selection()
        (model, iterator) = tree_selection.get_selected()
        if (iterator):
            id_num = int(model.get_value(iterator, 0))
            self._show(id_num)

    # show the given mark id, updating the nav_mark
    def _show(self, id_num):
        self.already_working = True # avoid recursion when changing things
        
        self.nav_mark = id_num # update navigation
        mark = self.marks[id_num]
        doc = mark.get_buffer()
        uri = doc.get_uri()
        line = doc.get_iter_at_mark(mark).get_line()
        iterator = self.edit_data.get_iter(len(self.edit_data) - id_num)
        self.edit_data.set_value(iterator, 2, str(line + 1) ) # update shown line to the current line of this mark
        tab = self.geditwindow.get_tab_from_uri(uri)
        if tab:
            self.geditwindow.set_active_tab(tab)
        else:
            tab = self.geditwindow.create_tab_from_uri(uri, gedit.encoding_get_current(), line, False, True)
        
        # try to scroll to line anyways
        doc = tab.get_document()
        doc.goto_line(line)
        
        ## FIXME: didn't work better than simple scroll_to_cursor
#        (start, end) = doc.get_bounds()
#        view = self.geditwindow.get_active_view()
#        view.scroll_to_iter(end, 0.0)
#        x = doc.get_iter_at_line_offset(line-self.scroll_margin, 0) # some lines before the right one, coming from the end
#        view.scroll_to_iter(x, 0.0)
        
        view = self.geditwindow.get_active_view()
        view.scroll_to_cursor()
        view.scroll_to_cursor()
        view.scroll_to_cursor()
        
        #update selection on the list
        self.points_list.set_cursor(len(self.edit_data) - id_num)
        
        self.already_working = False # release the lock
    
    # add each new tab to the watched list
    def _tab_added(self, window, tab):
        doc = tab.get_document()
        doc.connect("changed",self._update)
        # signals: ('changed', 'insert-text', 'insert-pixbuf', 'insert-child-anchor', 
        #   'delete-range', 'modified-changed', 'mark-set', 'mark-deleted', 
        #   'apply-tag', 'remove-tag', 'begin-user-action', 'end-user-action', 'paste-done')
        
    # record any edit activity
    def _update(self, doc):
        iterator=doc.get_iter_at_mark( doc.get_insert() )
        current_line= iterator.get_line()
        
        last_line = -10 # ensure recording position if none in list
        iter_first = self.edit_data.get_iter_first()
        if iter_first:
            last_line = int(self.edit_data.get_value(iter_first,2)) - 1               
            
        # add if it's not near the last one
        if math.fabs(current_line - last_line) > self.near_limit:
            self._add(current_line, doc, iterator)           
            self.nav_mark = 0 # reset navigation         
    
    # add the given position in the given doc to the list, saving a new mark too
    def _add(self, line, doc, iterator):
        name =  doc.get_short_name_for_display()
        uri = doc.get_uri()
        id_num = len(self.edit_data) + 1
        self.edit_data.prepend( ( id_num, name, line + 1 ) ) 
        mark = doc.create_mark(str(id_num),iterator,False)
        self.marks[id_num] = mark
        
    def button_next_click(self,button):
        self._next()
        
    def button_prev_click(self,button):
        self._prev()
        
    def _prev(self):
        if self.nav_mark > 2 and self.nav_mark <= len(self.edit_data):
            self._show(self.nav_mark - 1)            
        else:
            self._show(1)        
            
    def _next(self):
        if self.nav_mark > 0 and self.nav_mark < len(self.edit_data):
            self._show(self.nav_mark + 1)            
        else:
            self._show(len(self.edit_data))

