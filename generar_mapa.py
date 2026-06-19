import pandas as pd
import json
import re
import os

# Coordenadas por distrito
COORDENADAS = {
    "LIMA": [-12.0464, -77.0428],
    "AREQUIPA": [-16.3988, -71.5369],
    "PIURA": [-5.194, -80.632],
    "TRUJILLO": [-8.112, -79.028],
    "CHICLAYO": [-6.771, -79.841],
    "ICA": [-14.064, -75.728],
    "TACNA": [-18.014, -70.249],
    "MOQUEGUA": [-17.196, -70.935],
    "CUSCO": [-13.532, -71.967],
    "SAN MARTIN": [-6.5, -76.36],
    "LORETO": [-3.75, -73.25],
    "JUNIN": [-11.15, -76.0],
    "HUANUCO": [-9.927, -76.242],
    "CALLAO": [-12.055, -77.133],
    "SULLANA": [-4.9, -80.68],
    "LAMBAYEQUE": [-6.771, -79.841],
    "LA LIBERTAD": [-8.112, -79.028],
    "ANCASH": [-9.074, -78.594],
    "APURIMAC": [-13.65, -73.367],
    "AYACUCHO": [-13.15, -74.2],
    "CAJAMARCA": [-7.167, -78.5],
    "PASCO": [-10.8, -75.85],
    "PUNO": [-15.833, -70.0],
    "UCAYALI": [-8.383, -74.533],
    "MADRE DE DIOS": [-12.5, -69.0],
    "AMAZONAS": [-6.23, -77.87],
    "TUMBES": [-3.567, -80.45],
    "SAN JUAN DE MIRAFLORES": [-12.16, -76.97],
    "VILLA EL SALVADOR": [-12.155, -76.96],
    "SANTIAGO DE SURCO": [-12.135, -77.008],
    "SAN BORJA": [-12.106, -76.998],
    "MIRAFLORES": [-12.121, -77.026],
    "SAN ISIDRO": [-12.099, -77.032],
    "SAN MARTIN DE PORRES": [-11.98, -77.09],
    "LOS OLIVOS": [-11.97, -77.07],
    "COMAS": [-11.93, -77.05],
    "INDEPENDENCIA": [-11.99, -77.04],
    "SAN JUAN DE LURIGANCHO": [-12.0, -76.96],
    "CARABAYLLO": [-11.85, -77.04],
    "PUENTE PIEDRA": [-11.92, -77.07],
    "VENTANILLA": [-11.883, -77.117],
    "CHACLACAYO": [-11.99, -76.77],
    "SANTA ANITA": [-12.05, -76.97],
    "MAGDALENA DEL MAR": [-12.092, -77.062],
    "SURQUILLO": [-12.118, -77.038],
    "LA VICTORIA": [-12.067, -77.033],
    "CHORRILLOS": [-12.181, -77.02],
    "BARRANCA": [-10.75, -77.76],
    "RIMAC": [-12.035, -77.045],
    "BREÑA": [-12.06, -77.055],
    "JESUS MARIA": [-12.071, -77.049],
    "LINCE": [-12.082, -77.041],
    "LA MOLINA": [-12.079, -76.925],
    "PAUCARPATA": [-16.417, -71.5],
    "NUEVO IMPERIAL": [-13.133, -76.333],
    "SUNAMPE": [-13.45, -76.15],
    "ACARI": [-15.417, -74.617],
    "VICTOR LARCO HERRERA": [-8.133, -79.05]
}

def extraer_distrito(texto):
    """Extrae el distrito del texto de la ficha interna"""
    if not texto:
        return "LIMA"
    
    match = re.search(r'Distrito Judicial\s*\|\s*([A-ZÑÁÉÍÓÚ\s]+)', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    match = re.search(r'DISTRITO DE ([A-ZÑÁÉÍÓÚ\s]+)', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return "LIMA"

def get_coords(distrito):
    for key, coords in COORDENADAS.items():
        if key in str(distrito).upper():
            return coords
    return [-12.0464, -77.0428]

def generar_mapa():
    # Ver qué archivos existen
    print("Archivos en el directorio:", os.listdir())
    
    # Buscar el archivo Excel
    excel_files = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not excel_files:
        print("❌ No se encontró ningún archivo Excel")
        return
    
    excel_file = excel_files[0]
    print(f"📂 Usando archivo: {excel_file}")
    
    df = pd.read_excel(excel_file)
    
    print("Columnas encontradas:", df.columns.tolist())
    
    remates_json = []
    
    for _, row in df.iterrows():
        codigo = row.get("Código de Remate", "")
        precio_raw = row.get("Precio Base", "")
        ficha_interna = row.get("Información Ficha Interna (Completa)", "")
        
        distrito = extraer_distrito(ficha_interna)
        convocatoria = "1ra"
        if "SEGUNDA" in str(ficha_interna).upper():
            convocatoria = "2da"
        elif "TERCERA" in str(ficha_interna).upper():
            convocatoria = "3ra"
        
        coords = get_coords(distrito)
        
        precio_str = str(precio_raw).replace(',', '').strip()
        precio_num = 0
        match = re.search(r'([\d]+\.\d{2})', precio_str)
        if match:
            precio_num = float(match.group(1))
        else:
            match2 = re.search(r'(\d+)', precio_str)
            if match2:
                precio_num = float(match2.group(1))
        
        moneda = "$" if "$" in str(precio_raw) else "S/."
        
        if precio_num > 0 and codigo:
            remates_json.append({
                "cod": codigo,
                "pre": precio_num,
                "mon": moneda,
                "dis": distrito,
                "lat": coords[0],
                "lng": coords[1],
                "conv": convocatoria
            })
    
    print(f"✅ {len(remates_json)} remates procesados")
    
    # Plantilla HTML
    html_template = '''<!DOCTYPE html>
<html>
<head>
    <title>REMAJU - Mapa de Remates</title>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:system-ui;background:#1a1a2e;}
        #map{height:100vh;width:100%;}
        .controls{position:absolute;top:20px;right:20px;z-index:1000;background:rgba(0,0,0,0.85);border-radius:16px;padding:15px;color:white;}
        .controls button{width:100%;padding:8px;margin:5px 0;border:none;border-radius:8px;cursor:pointer;background:#2c3e66;color:white;font-weight:bold;}
        .controls button.active{background:#e74c3c;}
        .stats{position:absolute;bottom:20px;left:20px;z-index:1000;background:rgba(0,0,0,0.85);border-radius:16px;padding:12px 20px;color:white;font-size:12px;}
        .legend{position:absolute;bottom:20px;right:20px;z-index:1000;background:rgba(0,0,0,0.85);border-radius:12px;padding:10px;color:white;font-size:11px;}
        .legend .color-bar{display:flex;gap:2px;margin-top:5px;}
        .legend .color{width:30px;height:12px;}
        .legend .color.low{background:#00ff00;}
        .legend .color.med{background:#ffff00;}
        .legend .color.high{background:#ff0000;}
    </style>
</head>
<body>
<div id="map"></div>
<div class="controls">
    <h3>🔥 Mapa de Remates</h3>
    <button id="btnHeat" class="active">🌡️ Mapa de Calor</button>
    <button id="btnMarkers">📍 Marcadores</button>
    <button id="btnReset">🗺️ Reset Vista</button>
</div>
<div class="stats" id="stats"></div>
<div class="legend">
    <div>🔥 Intensidad de Remates</div>
    <div class="color-bar">
        <div class="color low"></div>
        <div class="color med"></div>
        <div class="color high"></div>
    </div>
    <div>Baja → Media → Alta</div>
</div>
<script>
const remates = REPLACE_DATA;

const map = L.map("map").setView([-9.19, -75.0152], 5.5);
L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",{
    attribution:"&copy; OpenStreetMap"
}).addTo(map);

const heatData = remates.map(r => [r.lat, r.lng, 0.7]);
let heatLayer = null;
let markerGroup = null;

function getColor(precio){
    if(precio>200000)return "#e74c3c";
    if(precio>80000)return "#f39c12";
    if(precio>30000)return "#3498db";
    return "#2ecc71";
}

function createMarkers(){
    const markers = [];
    remates.forEach(r => {
        const icon = L.divIcon({
            html: `<div style="background:${getColor(r.pre)};width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid white;font-size:10px;font-weight:bold;color:white;">${r.mon}</div>`,
            iconSize:[26,26]
        });
        const m = L.marker([r.lat, r.lng], {icon: icon});
        m.bindPopup(`<b>${r.cod}</b><br><b>${r.dis}</b><br><b>${r.mon} ${r.pre.toLocaleString()}</b><br><b>Conv: ${r.conv}</b>`);
        markers.push(m);
    });
    return markers;
}

function showHeat(){
    if(heatLayer)map.removeLayer(heatLayer);
    if(markerGroup)map.removeLayer(markerGroup);
    heatLayer = L.heatLayer(heatData,{radius:25,blur:15,gradient:{0.2:"#00ff00",0.5:"#ffff00",0.8:"#ff0000"}});
    heatLayer.addTo(map);
}

function showMarkers(){
    if(heatLayer)map.removeLayer(heatLayer);
    if(markerGroup)map.removeLayer(markerGroup);
    markerGroup = L.layerGroup(createMarkers());
    markerGroup.addTo(map);
}

document.getElementById("btnHeat").onclick = () => {showHeat();};
document.getElementById("btnMarkers").onclick = () => {showMarkers();};
document.getElementById("btnReset").onclick = () => {map.setView([-9.19, -75.0152], 5.5);};
showHeat();

const total = remates.length;
const avg = remates.reduce((a,b)=>a+b.pre,0)/total;
document.getElementById("stats").innerHTML = `📊 Total Remates: ${total} | 💰 Promedio: ${Math.round(avg).toLocaleString()} | 🏢 Distritos: ${new Set(remates.map(r=>r.dis)).size}`;
</script>
</body>
</html>'''
    
    html_final = html_template.replace("REPLACE_DATA", json.dumps(remates_json, ensure_ascii=False))
    
    with open("mapa_remates.html", "w", encoding="utf-8") as f:
        f.write(html_final)
    
    print(f"✅ Mapa generado: mapa_remates.html con {len(remates_json)} remates")

if __name__ == "__main__":
    generar_mapa()
