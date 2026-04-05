# Relojería Milla de Oro - Precision Scroll

Aplicación Streamlit para procesar catálogos PDF de relojería, extraer referencias, precios e imágenes, y generar pedidos.

## 🚀 Características

- **Procesamiento de PDF**: Extrae automáticamente referencias, precios e imágenes de catálogos PDF
- **Interfaz visual**: Muestra productos con imágenes y precios
- **Sistema de pedidos**: Permite seleccionar cantidades y generar reportes
- **Exportación**: Genera PDF con resumen de pedido
- **Filtrado**: Búsqueda rápida por referencia de producto

## 📋 Requisitos

- Python 3.8+
- Streamlit
- PyMuPDF (fitz)
- Pillow
- FPDF2
- Pandas

## 🛠️ Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd app2
```

2. Crear entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## 🚀 Uso

1. Ejecutar la aplicación:
```bash
streamlit run app.py
```

2. Subir un catálogo PDF en formato de la aplicación
3. Navegar por los productos y seleccionar cantidades
4. Ver resumen en la barra lateral
5. Exportar pedido como PDF

## 📁 Estructura del Proyecto

```
app2/
├── app.py              # Aplicación principal Streamlit
├── requirements.txt    # Dependencias de Python
├── README.md          # Documentación
├── .gitignore         # Archivos a ignorar en Git
└── .venv/             # Entorno virtual (no se sube a Git)
```

## 🎯 Funcionalidades Principales

### 1. Procesamiento de Catálogos
- Extracción automática de imágenes y texto
- Detección de referencias y precios
- Organización por filas y columnas

### 2. Interfaz de Usuario
- Grid de productos con imágenes
- Contadores de cantidad
- Filtrado por referencia
- Resumen visual en tiempo real

### 3. Gestión de Pedidos
- Selección de cantidades
- Cálculo automático de subtotales
- Aplicación de IVA y costos de envío
- Exportación a PDF profesional

## 📊 Tecnologías Utilizadas

- **Streamlit**: Framework para aplicaciones web en Python
- **PyMuPDF**: Procesamiento avanzado de PDF
- **Pillow**: Manipulación de imágenes
- **FPDF2**: Generación de PDF
- **Pandas**: Análisis de datos

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama de características (`git checkout -b feature/AmazingFeature`)
3. Commit de cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ✉️ Contacto

Relojería Milla de Oro - [@alejandro_hernandz](https://t.me/alejandro_hernandz)

---
Desarrollado para optimizar el proceso de pedidos de la relojería