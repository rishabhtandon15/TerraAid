# TerraAid: Air Quality Index (AQI) & Transport Vehicle Analytics - Data Sources & Technical Documentation

**Author**: TerraAid Development Team  
**System**: TerraAid Delhi AQI & Vehicle Transport System  

---

## 1. Executive Summary

**TerraAid** is an integrated environmental and urban transport intelligence application. It provides real-time monitoring of **Air Quality Index (AQI)** alongside **Vehicular Transport Density and Classification** across Delhi NCR and global regions. 

This document details the exact APIs, dataset registries, mathematical equations, computer vision models, and data pipelines used to power the application.

---

## 2. Air Quality Index (AQI) Data Sources & Methodology

### 2.1 Live Public APIs

1. **OpenAQ Global Air Quality REST API**
   - **Endpoint**: `https://api.openaq.org/v2/latest`
   - **Function**: Queries real-time ground monitoring sensors for $PM_{2.5}$, $PM_{10}$, $NO_2$, $CO$, $SO_2$, and $O_3$ concentrations.
   - **Parameters**: `coordinates={lat},{lon}`, `radius=10000` (10 km bounding circle).

2. **OpenStreetMap Nominatim Reverse Geocoding API**
   - **Endpoint**: `https://nominatim.openstreetmap.org/search`
   - **Function**: Resolves location name queries (*e.g., "Anand Vihar", "Noida", "Connaught Place"*) into spatial latitude and longitude coordinates.

### 2.2 Delhi CPCB Monitoring Network Registry

When offline or when API endpoints are unreachable, TerraAid utilizes an integrated geospatial registry mapping 11 official Central Pollution Control Board (CPCB) monitoring stations across Delhi NCR:

| Station ID | Station Name | Zone | Latitude | Longitude |
|:---|:---|:---|:---|:---|
| `DEL_001` | Anand Vihar | East Delhi | 28.6469 | 77.3160 |
| `DEL_002` | RK Puram | South Delhi | 28.5644 | 77.1729 |
| `DEL_003` | ITO | Central Delhi | 28.6317 | 77.2410 |
| `DEL_004` | Punjabi Bagh | West Delhi | 28.6683 | 77.1167 |
| `DEL_005` | Connaught Place (Mandir Marg) | Central Delhi | 28.6328 | 77.2197 |
| `DEL_006` | Dwarka Sector 8 | South-West Delhi | 28.5708 | 77.0715 |
| `DEL_007` | Rohini | North-West Delhi | 28.7325 | 77.1197 |
| `DEL_008` | Okhla Phase 2 | South-East Delhi | 28.5308 | 77.2711 |
| `DEL_009` | IGI Airport T3 | South-West Delhi | 28.5562 | 77.0999 |
| `NCR_010` | Sector 62, Noida | Noida NCR | 28.6245 | 77.3649 |
| `NCR_011` | Cyber City, Gurugram | Gurugram NCR | 28.4950 | 77.0895 |

### 2.3 CPCB AQI Calculation Formula & Spectrum

Indian CPCB AQI standard uses a segmented linear breakpoint function based on $PM_{2.5}$ concentration ($\mu g/m^3$):

$$AQI(C) = \frac{I_{high} - I_{low}}{C_{high} - C_{low}} \times (C - C_{low}) + I_{low}$$

#### AQI Breakpoint Categories:

- **Good (0 - 50)**: $PM_{2.5} \le 30 \mu g/m^3$ (Green)
- **Satisfactory (51 - 100)**: $PM_{2.5} \in (30, 60]$ (Light Green)
- **Moderate (101 - 200)**: $PM_{2.5} \in (60, 90]$ (Yellow)
- **Poor (201 - 300)**: $PM_{2.5} \in (90, 120]$ (Orange)
- **Very Poor (301 - 400)**: $PM_{2.5} \in (120, 250]$ (Red)
- **Severe (401 - 500)**: $PM_{2.5} > 250 \mu g/m^3$ (Maroon)

---

## 3. Transport & Vehicle Data Sources & Methodology

### 3.1 Live Traffic APIs

1. **OSRM (Open Source Routing Machine) Driving Speed API**
   - **Endpoint**: `https://router.project-osrm.org/route/v1/driving/{lon},{lat};{lon_offset},{lat_offset}`
   - **Function**: Measures real-time vehicle travel duration over a 2 km road segment.
   - **Metrics Extracted**:
     $$\text{Live Speed (km/h)} = \frac{\text{Distance (m)}}{\text{Duration (s)}} \times 3.6$$
     $$\text{Congestion Index} = \frac{\text{Free Flow Speed (45 km/h)}}{\text{Live Speed (km/h)}}$$

2. **OpenStreetMap Highway Infrastructure Classification**
   - Categorizes surrounding road networks (*motorway, trunk, primary, secondary*) to determine lane capacity and baseline vehicular density.

### 3.2 Computer Vision AI Detection Engine

1. **Model**: Ultralytics **YOLOv8** (`yolov8n.pt` neural network) trained on COCO dataset.
2. **Indian Vehicle Classifier**:
   - Detects standard bounding boxes for `car`, `motorcycle`, `bus`, `truck`.
   - Uses geometric aspect ratio ($\text{Width} / \text{Height}$) and area heuristics to separate **Auto-Rickshaws**, **E-Rickshaws**, **Two-Wheelers**, **Light Commercial Vehicles (LCV/Tempos)**, and **Heavy Trucks**.

### 3.3 Environmental Vehicular Impact Model

- **Hourly $CO_2$ Rate**:
  $$\text{Vehicular } CO_2 \text{ (kg/hr)} = \text{Total Vehicles} \times 0.16$$

- **Vehicular $PM_{2.5}$ Contribution**:
  $$\Delta PM_{2.5} \text{ (\mu g/m}^3\text{)} = (\text{Heavy Trucks} \times 2.1) + (\text{Cars} \times 0.18)$$

---

## 4. Dataset Downloader & Export Schemas

The **"Download Dataset"** engine compiles records into CSV (`.csv`) and JSON (`.json`) files in `c:/TerraAidProject/TerraAid/exports/`.

### Exported Dataset Fields:
- `Timestamp`, `Station_ID`, `Location_Name`, `Zone`, `Latitude`, `Longitude`
- `AQI_Value`, `AQI_Category`, `PM2.5_ug_m3`, `PM10_ug_m3`, `NO2_ug_m3`, `CO_mg_m3`, `SO2_ug_m3`, `O3_ug_m3`
- `Total_Vehicles_Count`, `Cars_Count`, `Bikes_Motorcycles_Count`, `Auto_Rickshaws_Count`, `E_Rickshaws_Count`, `Heavy_Trucks_Count`, `Buses_Count`, `LCV_Tempo_Count`
- `Heavy_Vehicle_Share_Percent`, `Estimated_CO2_Kg_Per_Hr`, `Estimated_PM2.5_Vehicle_Impact`
