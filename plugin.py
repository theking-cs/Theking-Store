# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import os, json, ssl
from urllib.request import urlopen, Request

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap

# Parche de seguridad para conexiones HTTPS
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

FEED_URL = "https://raw.githubusercontent.com/theking-cs/Theking-Store/main/feed.json"

class ThekingStore(Screen):
    skin = """
    <screen name="ThekingStore" position="center,center" size="1000,600" title="Theking-Store - Panel de Plugins" backgroundColor="#101010">
        <widget name="list" position="20,20" size="600,500" itemHeight="50" scrollbarMode="showOnDemand" />
        <widget name="description" position="640,80" size="330,350" font="Regular;22" foregroundColor="#FACC2E" backgroundColor="#101010" transparent="1" />
        <widget name="status" position="20,535" size="960,40" font="Regular;24" foregroundColor="#00FF7F" halign="center" backgroundColor="#101010" transparent="1" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.plugins_data = []
        
        self["list"] = MenuList([])
        self["description"] = Label("Selecciona un plugin para ver su descripción.")
        self["status"] = Label("Cargando lista desde GitHub...")
        
        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"], {
            "ok": self.installSelected,
            "cancel": self.close,
            "up": self.selectionChanged,
            "down": self.selectionChanged
        }, -1)
        
        self.onLayoutFinish.append(self.loadFeed)

    def loadFeed(self):
        try:
            req = Request(FEED_URL, headers={'User-Agent': 'Theking-Store'})
            response = urlopen(req, timeout=10)
            self.plugins_data = json.loads(response.read().decode('utf-8'))
            
            menu_items = []
            for p in self.plugins_data:
                name = p.get("name", "Plugin")
                version = p.get("version", "1.0")
                menu_items.append(("%s (v%s)" % (name, version), p))
                
            self["list"].setList(menu_items)
            self["status"].setText("OK: Instalar | EXIT: Salir")
            self.selectionChanged()
        except Exception as e:
            self["status"].setText("Error al cargar el feed.json")
            self.session.open(MessageBox, "No se pudo conectar con GitHub para descargar la lista de plugins.", MessageBox.TYPE_ERROR)

    def selectionChanged(self):
        current = self["list"].getCurrent()
        if current and len(current) > 1:
            p_info = current[1]
            desc = p_info.get("description", "Sin descripción.")
            repo = p_info.get("repo", "")
            text = "%s\n\nRepositorio:\n%s" % (desc, repo)
            self["description"].setText(text)

    def installSelected(self):
        current = self["list"].getCurrent()
        if not current:
            return
        p_info = current[1]
        repo_name = p_info.get("repo")
        plugin_name = p_info.get("name")
        
        if not repo_name:
            return

        # URL directa al install.sh del repositorio del plugin
        install_script_url = "https://raw.githubusercontent.com/theking-cs/%s/main/install.sh" % repo_name
        
        self.session.openWithCallback(
            self.confirmInstall,
            MessageBox,
            "¿Deseas instalar o actualizar %s?" % plugin_name,
            MessageBox.TYPE_YESNO
        )
        self.script_to_run = install_script_url

    def confirmInstall(self, result):
        if result and hasattr(self, "script_to_run"):
            self["status"].setText("Instalando plugin...")
            # Ejecuta la descarga y ejecución directa del install.sh en background mediante shell
            cmd = "wget -qO - %s | sh" % self.script_to_run
            res = os.system(cmd)
            if res == 0:
                self.session.open(MessageBox, "¡Instalación completada con éxito!\nSe reiniciará Enigma2.", MessageBox.TYPE_INFO, timeout=5)
                os.system("killall -9 enigma2")
            else:
                self.session.open(MessageBox, "Hubo un error durante la instalación.", MessageBox.TYPE_ERROR)
                self["status"].setText("Error en la instalación.")

def main(session, **kwargs):
    session.open(ThekingStore)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="Theking-Store",
            description="Tu tienda personalizada de plugins",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main,
            icon="plugin.png"
        )
    ]
