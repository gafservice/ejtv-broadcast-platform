#!/usr/bin/env bash
###############################################################################
#
# EJTV Broadcast Platform
#
# MediaMTX Health Check
#
# Archivo:
#     scripts/maintenance/mediamtx-status.sh
#
# Descripción:
#     Diagnóstico completo del servidor MediaMTX.
#
# Autor:
#     Gerardo Araya Fallas
#
# Proyecto:
#     EJTV Broadcast Platform
#
###############################################################################

set -e

APP_DIR="/opt/ejtv/mediamtx"
SERVICE="mediamtx"

CONFIG="${APP_DIR}/config/mediamtx.yml"
BINARIO="${APP_DIR}/bin/mediamtx"
VERSION_FILE="${APP_DIR}/releases/installed_versions.log"

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[1;34m"
NC="\033[0m"

ok(){
    echo -e "${GREEN}[ OK ]${NC} $1"
}

warn(){
    echo -e "${YELLOW}[WARN]${NC} $1"
}

fail(){
    echo -e "${RED}[FAIL]${NC} $1"
}

title(){

echo
echo "=============================================================="
echo " EJTV Broadcast Platform"
echo " MediaMTX Health Check"
echo "=============================================================="
echo

}

###############################################################################

system_info(){

echo "===================="
echo "SISTEMA"
echo "===================="

echo
echo "Hostname:"
hostnamectl --static

echo
echo "Sistema:"
lsb_release -ds

echo
echo "Kernel:"
uname -r

echo
echo "Arquitectura:"
uname -m

echo
echo "Fecha:"
date

echo
echo "Uptime:"
uptime -p

echo

}

###############################################################################

service_info(){

echo "===================="
echo "SERVICIO"
echo "===================="

systemctl status ${SERVICE} --no-pager

echo

}

###############################################################################

service_state(){

echo "===================="
echo "ESTADO"
echo "===================="

echo
echo "Habilitado:"
systemctl is-enabled ${SERVICE}

echo
echo "Activo:"
systemctl is-active ${SERVICE}

echo
echo "PID"

systemctl show ${SERVICE} \
--property MainPID

echo
echo "Memoria"

systemctl status ${SERVICE} \
--no-pager | grep Memory || true

echo

}

###############################################################################

version_info(){

echo "===================="
echo "VERSION"
echo "===================="

if [ -f "$BINARIO" ]; then

$BINARIO --version

ok "Binario encontrado"

else

fail "Binario no encontrado"

fi

echo

}

###############################################################################

config_info(){

echo "===================="
echo "CONFIGURACION"
echo "===================="

if [ -f "$CONFIG" ]; then

ok "Archivo encontrado"

ls -lah "$CONFIG"

else

fail "No existe archivo de configuración"

fi

echo

}

###############################################################################

directories(){

echo "===================="
echo "DIRECTORIOS"
echo "===================="

tree -L 2 ${APP_DIR}

echo

}

###############################################################################

ports(){

echo "===================="
echo "PUERTOS"
echo "===================="

ss -tuln | grep -E \
"8554|1935|8888|8889|8890|8892|8000|8001|8189"

echo

}

###############################################################################

process(){

echo "===================="
echo "PROCESO"
echo "===================="

ps -ef | grep mediamtx | grep -v grep

echo

}

###############################################################################

journal(){

echo "===================="
echo "ULTIMOS REGISTROS"
echo "===================="

journalctl -u mediamtx -n 20 --no-pager

echo

}

###############################################################################

disk(){

echo "===================="
echo "ESPACIO UTILIZADO"
echo "===================="

du -sh ${APP_DIR}

echo

}

###############################################################################

permissions(){

echo "===================="
echo "PERMISOS"
echo "===================="

ls -lah ${APP_DIR}

echo

}

###############################################################################

installed_version(){

echo "===================="
echo "REGISTRO VERSIONES"
echo "===================="

if [ -f "$VERSION_FILE" ]; then

cat "$VERSION_FILE"

else

warn "No existe registro"

fi

echo

}

###############################################################################

checklist(){

echo "===================="
echo "CHECKLIST"
echo "===================="

[ -f "$BINARIO" ] \
&& ok "Binario instalado" \
|| fail "Binario"

[ -f "$CONFIG" ] \
&& ok "Configuración" \
|| fail "Configuración"

systemctl is-enabled ${SERVICE} >/dev/null 2>&1 \
&& ok "Servicio habilitado" \
|| fail "Servicio"

systemctl is-active ${SERVICE} >/dev/null 2>&1 \
&& ok "Servicio activo" \
|| fail "Servicio"

[ -f "$VERSION_FILE" ] \
&& ok "Registro de versiones" \
|| warn "Registro"

echo

}

###############################################################################

footer(){

echo

echo "=============================================================="

if systemctl is-active mediamtx >/dev/null
then

echo
echo "RESULTADO GENERAL:"
echo
echo "SERVICIO OPERATIVO"
echo

else

echo
echo "RESULTADO GENERAL:"
echo
echo "ATENCION"
echo "Se detectaron problemas."
echo

fi

echo "=============================================================="

}

###############################################################################

title

system_info

service_info

service_state

version_info

config_info

directories

ports

process

journal

disk

permissions

installed_version

checklist

footer