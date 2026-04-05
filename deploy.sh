#!/bin/bash

# Script de despliegue para Relojería Milla de Oro - Precision Scroll App
# Este script configura la aplicación en un servidor con cPanel/SSH

echo "🚀 Iniciando despliegue de Relojería Milla de Oro - Precision Scroll App"
echo "======================================================================"

# Variables configurables
APP_NAME="relojeria-catalogo-app"
APP_PORT="8502"
DOMAIN="herramientas.relojeriamilladeoro.com"
APP_DIR="/home/\$USER/public_html/$DOMAIN"

# Verificar si estamos en un servidor con cPanel
if [ -d "/usr/local/cpanel" ]; then
    echo "✅ cPanel detectado"
    CPANEL_MODE=true
else
    echo "⚠️  cPanel no detectado - Modo servidor genérico"
    CPANEL_MODE=false
fi

# Función para instalar dependencias
install_dependencies() {
    echo "📦 Instalando dependencias del sistema..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv nginx
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y python3 python3-pip nginx
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y python3 python3-pip nginx
    else
        echo "❌ No se pudo detectar el gestor de paquetes"
        exit 1
    fi
}

# Función para configurar aplicación
setup_application() {
    echo "🔧 Configurando aplicación..."
    
    # Crear directorio de la aplicación
    mkdir -p $APP_DIR
    cd $APP_DIR
    
    # Clonar repositorio (o copiar archivos)
    if [ ! -d ".git" ]; then
        git clone https://github.com/dvwvitt/relojeria-catalogo-app.git .
    else
        git pull origin main
    fi
    
    # Crear entorno virtual
    python3 -m venv venv
    source venv/bin/activate
    
    # Instalar dependencias Python
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Configurar servicio systemd
    cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=Relojería Milla de Oro - Precision Scroll App
After=network.target

[Service]
Type=simple
User=\$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/streamlit run app.py --server.port=$APP_PORT --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Iniciar servicio
    sudo systemctl daemon-reload
    sudo systemctl enable $APP_NAME
    sudo systemctl start $APP_NAME
}

# Función para configurar Nginx como reverse proxy
setup_nginx() {
    echo "🌐 Configurando Nginx..."
    
    # Crear configuración de sitio
    cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://localhost:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Bloquear acceso a archivos sensibles
    location ~ /\. {
        deny all;
    }
    
    location ~* \.(log|sql|db)$ {
        deny all;
    }
}
EOF
    
    # Habilitar sitio
    ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    
    # Verificar configuración y reiniciar
    nginx -t
    sudo systemctl restart nginx
}

# Función para cPanel específico
setup_cpanel() {
    echo "🎛️  Configurando para cPanel..."
    
    # Nota: En cPanel normalmente se usa:
    # 1. Crear subdominio desde panel
    # 2. Subir archivos via FTP/File Manager
    # 3. Configurar .htaccess para proxy
    
    # Crear .htaccess para proxy
    cat > $APP_DIR/.htaccess << EOF
RewriteEngine On
RewriteRule ^(.*)$ http://localhost:$APP_PORT/\$1 [P,L]
EOF
    
    echo "📋 Instrucciones cPanel:"
    echo "1. Crear subdominio '$DOMAIN' desde cPanel"
    echo "2. Subir todos los archivos a $APP_DIR"
    echo "3. Ejecutar: cd $APP_DIR && python3 -m venv venv"
    echo "4. Ejecutar: source venv/bin/activate && pip install -r requirements.txt"
    echo "5. Ejecutar: nohup streamlit run app.py --server.port=$APP_PORT &"
}

# Menú principal
echo ""
echo "Selecciona una opción:"
echo "1) Instalación completa (servidor genérico)"
echo "2) Configuración para cPanel"
echo "3) Solo actualizar aplicación"
echo "4) Salir"
read -p "Opción: " choice

case $choice in
    1)
        install_dependencies
        setup_application
        setup_nginx
        echo "✅ Instalación completa finalizada"
        echo "🌍 Accede en: http://$DOMAIN"
        ;;
    2)
        setup_cpanel
        ;;
    3)
        cd $APP_DIR 2>/dev/null || { echo "❌ Directorio no encontrado"; exit 1; }
        git pull origin main
        source venv/bin/activate
        pip install -r requirements.txt
        sudo systemctl restart $APP_NAME
        echo "✅ Aplicación actualizada"
        ;;
    4)
        echo "👋 Saliendo..."
        exit 0
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "🎉 ¡Despliegue completado!"
echo "📊 Estado: sudo systemctl status $APP_NAME"
echo "📝 Logs: sudo journalctl -u $APP_NAME -f"