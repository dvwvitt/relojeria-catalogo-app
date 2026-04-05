import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageOps
import io
import os
import re
import math
from fpdf import FPDF
import tempfile
import uuid
import pandas as pd
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Relojería Milla de Oro - Precision Scroll",
    page_icon="⌚",
    layout="wide"
)

# --- ESTILOS MODERNOS (Surgical UX) ---
st.markdown("""
<style>
    .main { background-color: #fcfcfc; }
    .stButton>button { border-radius: 8px; font-weight: 600; transition: all 0.3s ease; }
    .btn-inc { background-color: #d4af37 !important; color: white !important; }
    .btn-dec { background-color: #f4f4f4 !important; color: #333 !important; }
    .product-card {
        border: none; padding: 15px; border-radius: 12px;
        background: transparent; text-align: center;
    }
    .qty-display { font-size: 1.5em; font-weight: bold; padding: 0 15px; color: #d4af37; }
    .price-tag { color: #28a745 !important; font-weight: bold; font-size: 1.4em; } 
    .ref-tag { color: white !important; font-size: 0.9em; font-weight: bold; margin-bottom: 5px; } 
    [data-testid="stAppDeployButton"] { display: none !important; }
    .st-emotion-cache-18ni7ap { visibility: hidden !important; }
    .block-container { padding-top: 3.5rem !important; }
    
    /* 🚀 TOOLTIP VISUAL QUIRÚRGICO 🚀 */
    .tooltip-wrapper {
        position: relative;
        display: block;
        width: 100%;
        cursor: pointer;
        padding: 10px 0;
        border-bottom: 1px solid #444;
        color: white !important;
        pointer-events: auto !important; /* Asegurar eventos de ratón */
    }
    
    /* 📦 Ventana de resumen (Scroll Independiente y Visible) 📦 */
    .custom-scroll-container {
        height: 380px;
        overflow-y: scroll !important; /* Forzado */
        overflow-x: visible !important;
        padding: 10px;
        border: 1px solid #555;
        background-color: transparent; 
        border-radius: 10px;
        position: relative;
        z-index: 10;
        pointer-events: auto !important; /* 👈 CRUCIAL para que el scroll funcione */
    }
    
    /* Estilo del Scrollbar (Estilo macOS Visible) */
    .custom-scroll-container::-webkit-scrollbar {
        width: 8px;
    }
    .custom-scroll-container::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    .custom-scroll-container::-webkit-scrollbar-thumb {
        background: rgba(212, 175, 55, 0.5); /* Color dorado translúcido */
        border-radius: 10px;
    }
    .custom-scroll-container::-webkit-scrollbar-thumb:hover {
        background: rgba(212, 175, 55, 0.8);
    }
    
    .tooltip-content {
        display: none;
        width: 110px; /* Imagen más pequeña como pidió el usuario */
        background-color: white;
        border-radius: 8px;
        padding: 5px;
        position: absolute;
        z-index: 100000;
        left: 20px;    /* Cerca de la referencia */
        top: 80%;      /* Inmediatamente hacia abajo */
        box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        border: 1px solid #d4af37;
        pointer-events: none;
    }
    .tooltip-wrapper:hover .tooltip-content {
        display: block;
    }
    .tooltip-img {
        width: 100px; /* Tamaño reducido */
        height: 100px;
        border-radius: 4px;
        object-fit: cover;
        display: block;
        margin: 0 auto;
    }
    
    /* Solo permitimos desbordamiento en los bloques de la barra lateral que contienen el resumen */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        overflow: visible !important;
    }

    .finance-total { font-size: 1.25em; color: #d4af37; border-top: 1px solid #333; padding-top: 8px; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN ---
for key in ['productos', 'cantidades', 'pedido_final', 'temp_dir', 'finanzas']:
    if key not in st.session_state:
        if key == 'cantidades': st.session_state[key] = {}
        elif key == 'temp_dir': st.session_state[key] = tempfile.mkdtemp()
        elif key == 'finanzas': st.session_state[key] = {"tasa": 1.0, "envio": 0.0, "iva": 0.0}
        else: st.session_state[key] = []

# --- UTILIDADES ---

@st.cache_data(show_spinner=False)
def get_b64(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception: return ""

def get_centroid(rect): return (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
def dist(p1, p2): return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

@st.cache_data(show_spinner=False)
def process_catalog_m1(pdf_bytes, temp_path):
    doc, items = fitz.open(stream=pdf_bytes, filetype="pdf"), []
    ref_pattern, price_pattern = re.compile(r'\b[A-Z0-9-]{4,15}\b'), re.compile(r'\$\s*\d+\.\d{2}')
    BLACKLIST = {"COLOURS", "COLORS", "MODEL", "MODELO", "REF", "SIZE", "PAGE", "PAGINA"}
    for page_idx in range(len(doc)):
        page = doc[page_idx]; h = page.rect.height; ymin, ymax = h*0.10, h*0.88
        text_dict = page.get_text("dict"); refs, prices = [], []
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        yc = (span["bbox"][1]+span["bbox"][3])/2
                        if yc < ymin or yc > ymax: continue
                        txt = span["text"].strip().upper()
                        if txt in BLACKLIST: continue
                        if ref_pattern.match(txt) and len(txt) >= 4: refs.append({"t": txt, "c": get_centroid(span["bbox"])})
                        if price_pattern.search(txt): prices.append({"t": txt, "c": get_centroid(span["bbox"])})
        raw = []
        for i in page.get_images(full=True):
            xr = i[0]; rs = page.get_image_rects(xr)
            if rs: raw.append({"xr": xr, "c": get_centroid(rs[0]), "base": doc.extract_image(xr)})
        if not raw: continue
        raw.sort(key=lambda x: x["c"][1]); rows = []
        if raw:
            curr = [raw[0]]
            for i in range(1, len(raw)):
                if abs(raw[i]["c"][1] - curr[0]["c"][1]) < 50: curr.append(raw[i])
                else: rows.append(curr); curr = [raw[i]]
            rows.append(curr)
        for row in rows:
            row.sort(key=lambda x: x["c"][0]); rr, rp = "N/A", "$0.00"
            for img in row:
                if img["base"]["width"] < 60: continue
                if refs:
                    close = min(refs, key=lambda r: dist(img["c"], r["c"]))
                    if dist(img["c"], close["c"]) < 95: rr = close["t"]
                if prices:
                    close = min(prices, key=lambda p: dist(img["c"], p["c"]))
                    if dist(img["c"], close["c"]) < 95: rp = close["t"]
                pil = Image.open(io.BytesIO(img["base"]["image"]))
                pil = ImageOps.fit(pil, (300, 300), Image.Resampling.LANCZOS)
                fpath = os.path.join(temp_path, f"i_{page_idx}_{img['xr']}_{uuid.uuid4().hex[:6]}.png")
                pil.save(fpath)
                items.append({
                    "id": f"{page_idx}_{img['xr']}_{uuid.uuid4().hex[:4]}",
                    "ref": rr, "price_str": rp, "price_val": (re.sub(r'[^\d.]', '', rp) or "0.0"), "img": fpath
                })
    return items

# --- EXPORT ---

def generate_report(pedido, fin):
    pdf = FPDF(); pdf.add_page(); pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, 'RELOJERÍA MILLA DE ORO - PEDIDO', 0, 1, 'C'); pdf.ln(5)
    cols = [40, 40, 20, 40, 40]
    pdf.set_font('Helvetica', 'B', 9)
    for h, w in zip(['Ref', 'Img', 'Cant', 'P.U', 'Sub'], cols): pdf.cell(w, 8, h, 1, 0, 'C')
    pdf.ln(); sub_g = 0; pdf.set_font('Helvetica', '', 9)
    for r in pedido:
        pv = float(r['price_val']); s = r['cantidad'] * pv; sub_g += s
        pdf.cell(cols[0], 35, r['ref'], 1, 0, 'C')
        pdf.image(r['img'], pdf.get_x()+5, pdf.get_y()+2, 30, 30)
        pdf.cell(cols[1], 35, '', 1, 0); pdf.cell(cols[2], 35, str(r['cantidad']), 1, 0, 'C')
        pdf.cell(cols[3], 35, f"${pv:.2f}", 1, 0, 'C'); pdf.cell(cols[4], 35, f"${s:.2f}", 1, 0, 'C'); pdf.ln(35)
    
    iva = sub_g * (fin['iva']/100); total = sub_g + iva + fin['envio']
    pdf.ln(5); pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(sum(cols[:-1]), 8, 'SUBTOTAL:', 0, 0, 'R'); pdf.cell(cols[-1], 8, f"${sub_g:.2f}", 0, 1, 'C')
    pdf.cell(sum(cols[:-1]), 8, f'IVA ({fin["iva"]}%):', 0, 0, 'R'); pdf.cell(cols[-1], 8, f"${iva:.2f}", 0, 1, 'C')
    pdf.cell(sum(cols[:-1]), 8, 'ENVÍO:', 0, 0, 'R'); pdf.cell(cols[-1], 8, f"${fin['envio']:.2f}", 0, 1, 'C')
    pdf.set_text_color(40, 167, 69); pdf.cell(sum(cols[:-1]), 10, 'TOTAL USD:', 0, 0, 'R'); pdf.cell(cols[-1], 10, f"${total:.2f}", 0, 1, 'C')
    return bytes(pdf.output())

# --- SIDEBAR ---

with st.sidebar:
    st.header("🛒 Selección")
    sel, sub_i, units = [], 0.0, 0
    for p in st.session_state.productos:
        q = st.session_state.cantidades.get(p['id'], 0)
        if q > 0:
            units += q; pv = float(p['price_val']); sub_i += (q * pv); sel.append({**p, "cantidad": q, "pv": pv})
    
    if sel:
        total_p = sub_i + (sub_i * st.session_state.finanzas['iva']/100) + st.session_state.finanzas['envio']
        st.markdown(f"<div class='finance-total'>TOTAL: ${total_p:,.2f} USD</div>", unsafe_allow_html=True)
        st.markdown(f"**Unidades:** {units}")
        st.divider()
        
        # 🟢 HTML UNIFICADO 🟢
        html_out = '<div class="custom-scroll-container">'
        for i in reversed(sel):
            b64 = get_b64(i['img'])
            html_out += f"""
            <div class="tooltip-wrapper">
                <strong>{i['ref']}</strong> ({i['cantidad']} un.) 
                <span class="tooltip-content">
                    <img src="data:image/png;base64,{b64}" class="tooltip-img">
                    <br><small>{i['ref']} - ${i['pv']:.2f}</small>
                </span>
                <br><small>{i['cantidad']} x {i['price_str']}</small>
            </div>"""
        html_out += '</div>'
        st.markdown(html_out, unsafe_allow_html=True)
        
        st.divider()
        if st.button("✅ Confirmar", type="primary", use_container_width=True): st.session_state.pedido_final = sel.copy(); st.toast("Ok.")
        with st.expander("⚙️ Ajustes"):
            st.session_state.finanzas['envio'] = st.number_input("Coste Envío", min_value=0.0, value=st.session_state.finanzas['envio'])
            st.session_state.finanzas['iva'] = st.number_input("IVA/Impuestos %", min_value=0.0, value=st.session_state.finanzas['iva'])

    if st.session_state.pedido_final:
        st.divider()
        if st.button("📄 Exportar Reporte", use_container_width=True):
            pdf = generate_report(st.session_state.pedido_final, st.session_state.finanzas)
            st.download_button("⬇️ Descargar PDF", pdf, "Cotizacion.pdf", "application/pdf", use_container_width=True)

# --- MAIN UI ---

t1, t2 = st.tabs(["📦 Catálogo", "📊 Informe"])
with t1:
    up = st.file_uploader("Subir Catálogo PDF", type="pdf")
    if up and not st.session_state.productos:
        st.session_state.productos = process_catalog_m1(up.read(), st.session_state.temp_dir)
        for p in st.session_state.productos: st.session_state.cantidades[p['id']] = 0
        st.rerun()

    if st.session_state.productos:
        search = st.text_input("🔍 Filtrar modelos", "").upper()
        disp = [p for p in st.session_state.productos if search in p['ref'].upper()]
        for i in range(0, len(disp), 4):
            cols = st.columns(4)
            for idx, item in enumerate(disp[i:i+4]):
                with cols[idx]:
                    st.markdown(f"<div class='product-card'><div class='ref-tag'>{item['ref']}</div><div class='price-tag'>{item['price_str']}</div></div>", unsafe_allow_html=True)
                    st.image(item['img'], use_container_width=True)
                    c1, c2, c3 = st.columns([1, 2, 1])
                    curr = st.session_state.cantidades.get(item['id'], 0)
                    if c1.button("−", key=f"d_{item['id']}"):
                        if curr > 0: st.session_state.cantidades[item['id']] = curr - 1; st.rerun()
                    c2.markdown(f"<center>{curr}</center>", unsafe_allow_html=True)
                    if c3.button("+", key=f"i_{item['id']}"): st.session_state.cantidades[item['id']] = curr + 1; st.rerun()

with t2:
    if st.session_state.productos:
        st.metric("📦 Artículos Totales", len(st.session_state.productos))
        st.metric("💰 Valor Inventario", f"${sum(float(p['price_val']) for p in st.session_state.productos):,.2f}")
        st.dataframe(pd.DataFrame(st.session_state.productos).groupby('ref').agg(Count=('id','count'), Value=('price_val','sum')).reset_index(), use_container_width=True)
