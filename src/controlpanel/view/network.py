# Copyright (C) 2008, OLPC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import gtk
import gobject
import gettext
_ = lambda msg: gettext.dgettext('sugar', msg)

from sugar.graphics import style
from sugar.graphics.icon import Icon

from controlpanel.sectionview import SectionView
from controlpanel.inlinealert import InlineAlert

ICON = 'module-network'
TITLE = _('Network')

class Network(SectionView):
    def __init__(self, model, alerts):
        SectionView.__init__(self)

        self.emit('valid_section', True)
                
        self._jabber_sid = 0
        self._jabber_valid = True
        self._radio_valid = True
        self.restart_alerts = alerts

        self._model = model
        self._jabber = self._model.get_jabber()

        self.set_border_width(style.DEFAULT_SPACING * 2)
        self.set_spacing(style.DEFAULT_SPACING)
        group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        self._radio_alert_box = gtk.HBox(spacing=style.DEFAULT_SPACING)
        self._jabber_alert_box = gtk.HBox(spacing=style.DEFAULT_SPACING)

        separator_wireless = gtk.HSeparator()
        self.pack_start(separator_wireless, expand=False)
        separator_wireless.show()

        label_wireless = gtk.Label(_('Wireless'))
        label_wireless.set_alignment(0, 0)
        self.pack_start(label_wireless, expand=False)
        label_wireless.show()
        box_wireless = gtk.VBox()
        box_wireless.set_border_width(style.DEFAULT_SPACING * 2)
        box_wireless.set_spacing(style.DEFAULT_SPACING)
        box_radio = gtk.HBox(spacing=style.DEFAULT_SPACING)
        label_radio = gtk.Label(_('Radio:'))
        label_radio.set_alignment(1, 0.5)
        label_radio.modify_fg(gtk.STATE_NORMAL, 
                              style.COLOR_SELECTION_GREY.get_gdk_color())
        box_radio.pack_start(label_radio, expand=False)
        group.add_widget(label_radio)
        label_radio.show()        
        button = gtk.CheckButton()
        button.set_alignment(0, 0)
        button.connect('toggled', self.__radio_toggled_cb)
        box_radio.pack_start(button, expand=False)
        button.show()
        box_wireless.pack_start(box_radio, expand=False)
        box_radio.show()

        icon_radio = Icon(icon_name='emblem-warning',
                          fill_color=style.COLOR_SELECTION_GREY.get_svg(),
                          stroke_color=style.COLOR_WHITE.get_svg())
        self._radio_alert = InlineAlert(icon=icon_radio)
        icon_radio.show()
        label_radio_error = gtk.Label()
        group.add_widget(label_radio_error)
        self._radio_alert_box.pack_start(label_radio_error, expand=False)
        label_radio_error.show()
        self._radio_alert_box.pack_start(self._radio_alert, expand=False)
        box_wireless.pack_end(self._radio_alert_box, expand=False)
        self._radio_alert_box.show()
        try:                        
            self._radio_state = self._model.get_radio()        
        except Exception, detail:
            self._radio_alert.props.msg = detail                    
            self._radio_alert.show()
        if 'radio' in self.restart_alerts:
            self._radio_alert.props.msg = self._restart_msg
            self._radio_alert.show()

        self.pack_start(box_wireless, expand=False)
        box_wireless.show()

        separator_mesh = gtk.HSeparator()
        self.pack_start(separator_mesh, False)
        separator_mesh.show()

        label_mesh = gtk.Label(_('Mesh'))
        label_mesh.set_alignment(0, 0)
        self.pack_start(label_mesh, expand=False)
        label_mesh.show()
        box_mesh = gtk.VBox()
        box_mesh.set_border_width(style.DEFAULT_SPACING * 2)
        box_mesh.set_spacing(style.DEFAULT_SPACING)

        box_server = gtk.HBox(spacing=style.DEFAULT_SPACING)
        label_server = gtk.Label(_('Server:'))
        label_server.set_alignment(1, 0.5)
        label_server.modify_fg(gtk.STATE_NORMAL, 
                               style.COLOR_SELECTION_GREY.get_gdk_color())
        box_server.pack_start(label_server, expand=False)
        group.add_widget(label_server)
        label_server.show()        
        self._entry = gtk.Entry()
        self._entry.set_alignment(0)
        self._entry.modify_bg(gtk.STATE_INSENSITIVE, 
                        style.COLOR_WHITE.get_gdk_color())
        self._entry.modify_base(gtk.STATE_INSENSITIVE, 
                          style.COLOR_WHITE.get_gdk_color())          
        self._entry.set_size_request(int(gtk.gdk.screen_width() / 3), -1)
        self._entry.set_text(self._jabber)
        self._entry.connect('changed', self.__jabber_changed_cb)
        box_server.pack_start(self._entry, expand=False)
        self._entry.show()      
        box_mesh.pack_start(box_server, expand=False)
        box_server.show()
        
        icon_jabber = Icon(icon_name='emblem-warning',
                           fill_color=style.COLOR_SELECTION_GREY.get_svg(),
                           stroke_color=style.COLOR_WHITE.get_svg())
        self._jabber_alert = InlineAlert(icon=icon_jabber)
        icon_jabber.show()
        label_jabber_error = gtk.Label()
        group.add_widget(label_jabber_error)
        self._jabber_alert_box.pack_start(label_jabber_error, expand=False)
        label_jabber_error.show()
        self._jabber_alert_box.pack_start(self._jabber_alert, expand=False)
        box_mesh.pack_end(self._jabber_alert_box, expand=False)
        self._jabber_alert_box.show()
        if 'jabber' in self.restart_alerts:
            self._jabber_alert.props.msg = self._restart_msg
            self._jabber_alert.show()

        self.pack_start(box_mesh, expand=False)
        box_mesh.show()

    def undo(self):
        self._model.set_jabber(self._jabber)

        self._entry.set_text(self._jabber)

        self._jabber_valid = True
        self._radio_valid = True
        self.restart = False
        self.restart_alerts = []

    def __radio_toggled_cb(self, widget, data=None): 
        radio_state = ('off', 'on')[widget.get_active()]
        try:
            self._model.set_radio(radio_state)
        except Exception, detail:
            self._radio_alert.props.msg = detail
            self._radio_valid = False
        else:
            self._radio_alert.props.msg = self._restart_msg
            self._radio_valid = True            
            if radio_state != self._radio_state:                
                self.restart = True
                self.restart_alerts.append('radio')                
            else:
                self.restart = False

        if self._radio_valid and self._jabber_valid:
            self.emit('valid_section', True)
        else:    
            self.emit('valid_section', False)

        if not self._radio_alert.props.visible or \
                radio_state != self._jabber:                
            self._radio_alert.show()
        else:    
            self._radio_alert.hide()

        return False

    def __jabber_changed_cb(self, widget, data=None):        
        if self._jabber_sid:
            gobject.source_remove(self._jabber_sid)
        self._jabber_sid = gobject.timeout_add(1000, 
                                               self.__jabber_timeout_cb, widget)
                
    def __jabber_timeout_cb(self, widget):        
        self._jabber_sid = 0
        try:
            self._model.set_jabber(widget.get_text())
        except ValueError, detail:
            self._jabber_alert.props.msg = detail
            self._jabber_valid = False
        else:
            self._jabber_alert.props.msg = self._restart_msg
            self._jabber_valid = True            
            if widget.get_text() != self._jabber:                
                self.restart = True
                self.restart_alerts.append('jabber')
            else:
                self.restart = False

        if self._jabber_valid and self._radio_valid:
            self.emit('valid_section', True)
        else:    
            self.emit('valid_section', False)

        if not self._jabber_alert.props.visible or \
                widget.get_text() != self._jabber:                
            self._jabber_alert.show()
        else:    
            self._jabber_alert.hide()

        return False
