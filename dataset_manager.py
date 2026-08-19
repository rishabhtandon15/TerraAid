# dataset_manager.py - Export & Download Dataset Module for TerraAid

import csv
import json
import os
import time

EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")

def ensure_export_dir():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    return EXPORT_DIR

def generate_sample_dataset():
    """
    Generates a comprehensive dataset containing Delhi NCR region AQI readings
    and Vehicle Transport Breakdown metrics.
    """
    from aqi_service import DELHI_STATIONS, calculate_aqi_category
    from vehicle_detector import detector_engine

    records = []
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    for st in DELHI_STATIONS:
        aqi_info = calculate_aqi_category(st["pm25"])
        veh_info = detector_engine.get_regional_vehicle_density(st["name"], st["lat"], st["lon"])
        
        row = {
            "Timestamp": timestamp,
            "Station_ID": st["station_id"],
            "Location_Name": st["name"],
            "Zone": st["zone"],
            "Latitude": st["lat"],
            "Longitude": st["lon"],
            "AQI_Value": aqi_info["aqi"],
            "AQI_Category": aqi_info["category"],
            "PM2.5_ug_m3": st["pm25"],
            "PM10_ug_m3": st["pm10"],
            "NO2_ug_m3": st["no2"],
            "CO_mg_m3": st["co"],
            "SO2_ug_m3": st["so2"],
            "O3_ug_m3": st["o3"],
            "Total_Vehicles_Count": veh_info["total_vehicles"],
            "Cars_Count": veh_info["counts"]["Cars"],
            "Bikes_Motorcycles_Count": veh_info["counts"]["Bikes & Motorcycles"],
            "Auto_Rickshaws_Count": veh_info["counts"]["Auto-Rickshaws"],
            "E_Rickshaws_Count": veh_info["counts"]["E-Rickshaws"],
            "Heavy_Trucks_Count": veh_info["counts"]["Heavy Trucks"],
            "Buses_Count": veh_info["counts"]["Buses / Minibuses"],
            "LCV_Tempo_Count": veh_info["counts"]["Light Commercial Vehicles (Tempo/Van)"],
            "Heavy_Vehicle_Share_Percent": veh_info["heavy_vehicle_share_percent"],
            "Estimated_CO2_Kg_Per_Hr": veh_info["estimated_co2_kg_per_hr"],
            "Estimated_PM2.5_Vehicle_Impact": veh_info["estimated_pm25_impact_ugm3"]
        }
        records.append(row)

    return records


def export_dataset_to_csv(custom_filename=None):
    """
    Exports the complete AQI & Transport Vehicle Dataset to a CSV file.
    Returns the absolute filepath of the generated CSV dataset.
    """
    export_dir = ensure_export_dir()
    if not custom_filename:
        filename = f"TerraAid_Delhi_AQI_Transport_Dataset_{int(time.time())}.csv"
    else:
        filename = custom_filename if custom_filename.endswith(".csv") else f"{custom_filename}.csv"

    filepath = os.path.join(export_dir, filename)

    records = generate_sample_dataset()
    if not records:
        return None

    fieldnames = list(records[0].keys())

    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"[DatasetManager] Dataset exported successfully to CSV: {filepath}")
    return filepath


def export_dataset_to_json(custom_filename=None):
    """
    Exports the complete AQI & Transport Vehicle Dataset to a JSON file.
    Returns the absolute filepath of the generated JSON dataset.
    """
    export_dir = ensure_export_dir()
    if not custom_filename:
        filename = f"TerraAid_Delhi_AQI_Transport_Dataset_{int(time.time())}.json"
    else:
        filename = custom_filename if custom_filename.endswith(".json") else f"{custom_filename}.json"

    filepath = os.path.join(export_dir, filename)

    records = generate_sample_dataset()

    data_payload = {
        "dataset_title": "TerraAid - Delhi AQI and Transport Vehicle Analytics Dataset",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_records": len(records),
        "data": records
    }

    with open(filepath, mode="w", encoding="utf-8") as jsonfile:
        json.dump(data_payload, jsonfile, indent=4)

    print(f"[DatasetManager] Dataset exported successfully to JSON: {filepath}")
    return filepath
