#!/bin/bash
# VBR Pastas — duplo clique abre a tela no navegador.
#
# Entra na pasta do programa, escolhe um Python que sirva e sobe o servidor.
# A janela fica aberta enquanto a tela estiver no ar; fechar a janela para o
# programa.

cd "$(dirname "$0")" || exit 1

if [ ! -x "$0" ]; then
  echo "Este atalho ainda não está marcado como executável. Uma vez só, no Terminal:"
  echo "  chmod +x \"$0\""
  echo
fi

# O python3 do sistema (/usr/bin) é 3.9, velho demais para o modelo.py. E as
# bibliotecas do Google foram instaladas num Python só. Preferimos o que tem
# as duas coisas; na falta, um 3.10+ qualquer — a demonstração (--falso)
# funciona sem as bibliotecas.
escolher_python() {
  local reserva=""
  for c in python3 \
           /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
           /usr/local/bin/python3 \
           /opt/homebrew/bin/python3; do
    command -v "$c" >/dev/null 2>&1 || continue
    "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null || continue
    if "$c" -c 'import googleapiclient' 2>/dev/null; then
      echo "$c"; return
    fi
    [ -z "$reserva" ] && reserva="$c"
  done
  echo "$reserva"
}

PY="$(escolher_python)"
if [ -z "$PY" ]; then
  echo "Não achei um Python 3.10 ou mais novo neste Mac. Instale em python.org e tente de novo."
  read -r -p "Aperte Enter para fechar. "
  exit 1
fi

exec "$PY" servidor.py "$@"
