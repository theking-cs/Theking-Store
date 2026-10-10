#!/bin/sh
echo "********************************************************"
echo "* Instalando Theking-Store                            *"
echo "********************************************************"

PLUGIN_NAME="ThekingStore"
PLUGIN_PATH="/usr/lib/enigma2/python/Plugins/Extensions/$PLUGIN_NAME"

# Limpiar instalaciones previas o temporales
rm -rf $PLUGIN_PATH
rm -rf /tmp/Theking-Store.zip
rm -rf /tmp/Theking-Store-*

echo "> Descargando Theking-Store desde GitHub..."
wget --no-check-certificate https://github.com/theking-cs/Theking-Store/archive/refs/heads/main.zip -O /tmp/Theking-Store.zip

echo "> Extrayendo archivos..."
unzip -q /tmp/Theking-Store.zip -d /tmp/

# Buscar la carpeta descomprimida dinámicamente
EXTRACTED_DIR=$(ls -d /tmp/Theking-Store-* | grep -v '\.zip$')

if [ -d "$EXTRACTED_DIR" ]; then
    echo "> Instalando en el sistema..."
    mv "$EXTRACTED_DIR" $PLUGIN_PATH
else
    echo "[ERROR] No se pudo encontrar la carpeta descomprimida."
    exit 1
fi

# Permisos
chmod -R 755 $PLUGIN_PATH

# Limpieza
rm -rf /tmp/Theking-Store.zip

echo "********************************************************"
echo "* INSTALACIÓN COMPLETADA - REINICIANDO ENIGMA2       *"
echo "********************************************************"
killall -9 enigma2

exit 0
