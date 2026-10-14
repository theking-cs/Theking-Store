# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import os, json, ssl, urllib.request
from urllib.request import urlopen, Request

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Console import Console  # <-- Pantalla de consola nativa de Enigma2
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
ICONS_DIR = "/tmp/theking_icons"

class ThekingStore(Screen):
    skin = """
    <screen name="ThekingStore" position="center,center" size="1200,650" title="Theking-Store - Panel de Plugins Pro" backgroundColor="#0b0f19">
        <!-- Fondo general y cabecera decorativa -->
        <eLabel position="0,0" size="1200,70" backgroundColor="#161b22" zPosition="-2"/>
        <widget name="title_label" position="30,15" size="1140,40" font="Regular;28" foregroundColor="#58a6ff" backgroundColor="#161b22" transparent="1" valign="center" />

        <!-- Lista de Plugins (Izquierda) -->
        <widget name="list" position="30,90" size="650,500" itemHeight="60" scrollbarMode="showOnDemand" backgroundColor="#111620" foregroundColor="#ffffff" selectionBackgroundColor="#1f6feb" selectionForegroundColor="#ffffff" transparent="0" />

        <!-- Panel de Detalles e Icono (Derecha) -->
        <eLabel position="710,90" size="460,500" backgroundColor="#161b22" zPosition="-1" />
        <widget name="plugin_icon" position="840,110" size="200,200" alphatest="on" scale="1" />
        <widget name="description" position="730,330" size="420,240" font="Regular;22" foregroundColor="#c9d1d9" backgroundColor="#161b22" transparent="1" />

        <!-- Barra de Estado Inferior -->
        <eLabel position="0,605" size="1200,45" backgroundColor="#161b22" zPosition="-2"/>
        <widget name="status" position="30,612" size="1140,30" font="Regular;20" foregroundColor="#3fb950" backgroundColor="#161b22" transparent="1" valign="center" halign="center" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.plugins_data = []
        
        if not os.path.exists(ICONS_DIR):
            os.makedirs(ICONS_DIR)

        self["title_label"] = Label("Theking-Store  |  Panel by Zoubair91")
        self["list"] = MenuList([])
        self["plugin_icon"] = Pixmap()
        self["description"] = Label("Selecciona un plugin para ver su información y descripción detallada.")
        self["status"] = Label("Conectando con GitHub...")
        
        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"], {
            "ok": self.installSelected,
            "cancel": self.close,
            "up": self.keyUp,
            "down": self.keyDown,
            "left": self.keyLeft,
            "right": self.keyRight
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
            self["status"].setText("OK: Instalar / Actualizar  |  EXIT: Salir")
            self.selectionChanged()
        except Exception as e:
            self["status"].setText("Error al cargar el feed.json")
            self.session.open(MessageBox, "No se pudo conectar con GitHub para obtener el catálogo.", MessageBox.TYPE_ERROR)

    def keyUp(self):
        self["list"].up()
        self.selectionChanged()

    def keyDown(self):
        self["list"].down()
        self.selectionChanged()

    def keyLeft(self):
        self["list"].pageUp()
        self.selectionChanged()

    def keyRight(self):
        self["list"].pageDown()
        self.selectionChanged()

    def selectionChanged(self):
        current = self["list"].getCurrent()
        if current and len(current) > 1:
            p_info = current[1]
            desc = p_info.get("description", "Sin descripción disponible.")
            repo = p_info.get("repo", "")
            icon_url = p_info.get("icon", "")
            
            text = "Repositorio: %s\n\n%s" % (repo, desc)
            self["description"].setText(text)
            
            if icon_url:
                icon_name = "%s.png" % repo
                icon_path = os.path.join(ICONS_DIR, icon_name)
                try:
                    if not os.path.exists(icon_path):
                        urllib.request.urlretrieve(icon_url, icon_path)
                    
                    if os.path.exists(icon_path):
                        pixmap = LoadPixmap(icon_path)
                        if pixmap:
                            self["plugin_icon"].instance.setPixmap(pixmap)
                except:
                    pass

    def installSelected(self):
        current = self["list"].getCurrent()
        if not current:
            return
        p_info = current[1]
        repo_name = p_info.get("repo")
        plugin_name = p_info.get("name")
        
        if not repo_name:
            return

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
            self["status"].setText("Abriendo consola de instalación...")
            # Lanza la consola nativa de Enigma2 ejecutando el script en directo
            cmd = "wget -qO - %s | sh" % self.script_to_run
            self.session.openWithCallback(
                self.installFinished,
                Console,
                title="Instalando plugin...",
                cmdlist=[cmd]
            )

    def installFinished(self, *args, **kwargs):
        self.session.openWithCallback(
            self.restartEnigma,
            MessageBox,
            "¡Instalación finalizada!\n¿Deseas reiniciar Enigma2 ahora para aplicar los cambios?",
            MessageBox.TYPE_YESNO
        )

    def restartEnigma(self, result):
        if result:
            os.system("killall -9 enigma2")
        else:
            self["status"].setText("Instalación completada.")

def main(session, **kwargs):
    session.open(ThekingStore)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="Theking-Store",
            description="Tu tienda moderna de plugins",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main,
            icon="plugin.png"
        )
    ]
