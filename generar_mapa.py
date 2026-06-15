import pandas as pd
import json
import re

# Coordenadas por distrito (versión simplificada)
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
    "CALLAO": [-12.055, -77.133]
}

def get_coords(distrito):
    for key, coords in COORDENADAS.items():
        if key in str(distrito).upper():
            return coords
    return [-12.0464, -77.0428]

def generar_mapa():
    df = pd.read_excel("Bloomberg_Remates_Organizado.xlsx")
    
    # Debug: imprimir nombres de columnas
    print("Columnas encontradas:", df.columns.tolist())
    
    remates_json = []
    for _, row in df.iterrows():
        # Usar los nombres correctos de columnas de tu scraper
        distrito = row["Distrito Judicial"]
        codigo = row["Código de Remate"]
        precio_raw = row["Precio Base"]
        convocatoria = row["Convocatoria"]
        
        coords = get_coords(distrito)
        
        # Extraer número del precio
        precio_str = str(precio_raw).replace(',', '')
        precio_num = float(re.sub(r'[^\d.]', '', precio_str)) if re.search(r'[\d.]+', precio_str) else 0
        
        # Determinar moneda
        moneda = "$" if "$" in str(precio_raw) else "S/."
        
        remates_json.append({
            "cod": codigo,
            "pre": precio_num,
            "mon": moneda,
            "dis": distrito,
            "lat": coords[0],
            "lng": coords[1],
            "conv": convocatoria
        })
    
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