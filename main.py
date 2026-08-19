# main.py - TerraAid: Integrated AQI Monitoring & Transport Vehicle Analytics System

import os
import sys

# Kivy module imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy_garden.mapview import MapView, MapMarker
from kivy.properties import BooleanProperty, ListProperty, StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.utils import platform

# Custom service modules
from aqi_service import fetch_live_aqi, search_region_coordinates, DELHI_STATIONS, calculate_aqi_category
from vehicle_detector import detector_engine
from dataset_manager import export_dataset_to_csv, export_dataset_to_json, EXPORT_DIR

# Kivy Language (KV) Interface Styling
KV = """
#:import NoTransition kivy.uix.screenmanager.NoTransition

ScreenManager:
    id: screen_manager
    transition: NoTransition()

    MapScreen:
        name: 'map_screen'

    VehicleScreen:
        name: 'vehicle_screen'

    InfoScreen:
        name: 'info_screen'

<MapScreen>:
    name: 'map_screen'
    map_source: "osm"

    BoxLayout:
        orientation: 'vertical'

        # Navigation & Search Bar Header
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(50)
            padding: dp(5)
            spacing: dp(5)
            canvas.before:
                Color:
                    rgba: 0.12, 0.15, 0.22, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            TextInput:
                id: search_input
                hint_text: 'Search Delhi region (e.g. Anand Vihar, RK Puram, CP, Noida)...'
                multiline: False
                size_hint_x: 0.5
                font_size: '14sp'
                padding: [dp(10), dp(10)]
                on_text_validate: root.perform_region_search()

            Button:
                text: 'Search AQI'
                size_hint_x: 0.15
                background_normal: ''
                background_color: 0.15, 0.55, 0.85, 1
                bold: True
                on_release: root.perform_region_search()

            Button:
                text: 'Real Transport Mode'
                size_hint_x: 0.18
                background_normal: ''
                background_color: 0.85, 0.45, 0.15, 1
                bold: True
                on_release: app.root.current = 'vehicle_screen'

            Button:
                text: 'Download Dataset'
                size_hint_x: 0.17
                background_normal: ''
                background_color: 0.15, 0.70, 0.35, 1
                bold: True
                on_release: root.download_dataset_popup()

        # Main Map & AQI Card Display Split
        FloatLayout:
            id: map_container

            MapView:
                id: map_view
                lat: 28.6139
                lon: 77.2090
                zoom: 12
                map_source: root.map_source
                pos_hint: {'x': 0, 'y': 0}
                size_hint: 1, 1

            # Floating AQI & Regional Metrics Card Overlay (Top Right)
            BoxLayout:
                orientation: 'vertical'
                size_hint: None, None
                size: dp(320), dp(230)
                pos_hint: {'right': 0.98, 'top': 0.97}
                padding: dp(12)
                spacing: dp(6)
                canvas.before:
                    Color:
                        rgba: 0.08, 0.10, 0.15, 0.90
                    Rectangle:
                        pos: self.pos
                        size: self.size

                Label:
                    text: root.card_title_text
                    font_size: '15sp'
                    bold: True
                    color: 1, 1, 1, 1
                    size_hint_y: None
                    height: dp(24)

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: dp(35)
                    spacing: dp(10)

                    Label:
                        text: f"AQI: {root.aqi_value}"
                        font_size: '22sp'
                        bold: True
                        color: root.aqi_color_rgba
                        size_hint_x: 0.5

                    Label:
                        text: root.aqi_category_text
                        font_size: '14sp'
                        bold: True
                        color: root.aqi_color_rgba
                        size_hint_x: 0.5

                Label:
                    text: f"PM2.5: {root.pm25_text} ug/m3 | PM10: {root.pm10_text} ug/m3"
                    font_size: '12sp'
                    color: 0.9, 0.9, 0.9, 1
                    size_hint_y: None
                    height: dp(20)

                Label:
                    text: f"NO2: {root.no2_text} | CO: {root.co_text} | SO2: {root.so2_text}"
                    font_size: '11sp'
                    color: 0.8, 0.8, 0.8, 1
                    size_hint_y: None
                    height: dp(18)

                Label:
                    text: f"Advisory: {root.advisory_text}"
                    font_size: '11sp'
                    color: 1, 0.85, 0.4, 1
                    text_size: self.width, None
                    halign: 'left'
                    valign: 'top'

                Button:
                    text: 'Recenter Delhi Stations'
                    size_hint_y: None
                    height: dp(30)
                    background_normal: ''
                    background_color: 0.2, 0.3, 0.45, 1
                    on_release: root.load_delhi_stations()

        # Footer Status Bar
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(30)
            padding: [dp(10), dp(2)]
            canvas.before:
                Color:
                    rgba: 0.1, 0.1, 0.12, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            Label:
                text: root.status_message_text
                font_size: '12sp'
                color: 0.9, 0.9, 0.9, 1
                halign: 'left'
                valign: 'middle'
                text_size: self.size


<VehicleScreen>:
    name: 'vehicle_screen'

    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 0.07, 0.09, 0.13, 1
            Rectangle:
                pos: self.pos
                size: self.size

        # Header Bar
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(45)
            spacing: dp(10)

            Button:
                text: '< Back to Map'
                size_hint_x: 0.2
                background_normal: ''
                background_color: 0.3, 0.3, 0.35, 1
                on_release: app.root.current = 'map_screen'

            Label:
                text: 'REAL Delhi Transport & Live Traffic Counter'
                font_size: '17sp'
                bold: True
                color: 1, 1, 1, 1
                size_hint_x: 0.55

            Button:
                text: 'Download Dataset'
                size_hint_x: 0.25
                background_normal: ''
                background_color: 0.15, 0.70, 0.35, 1
                bold: True
                on_release: root.download_dataset_popup()

        # Vehicle Breakdown Cards Grid
        GridLayout:
            cols: 4
            spacing: dp(10)
            size_hint_y: 0.45

            # Cars Card
            BoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.15, 0.20, 0.30, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: 'Cars 🚗'
                    font_size: '15sp'
                    color: 0.4, 0.8, 1, 1
                Label:
                    text: str(root.car_count)
                    font_size: '32sp'
                    bold: True
                    color: 1, 1, 1, 1

            # Bikes Card
            BoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.15, 0.20, 0.30, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: 'Bikes & Scooters 🏍️'
                    font_size: '15sp'
                    color: 0.4, 1, 0.6, 1
                Label:
                    text: str(root.bike_count)
                    font_size: '32sp'
                    bold: True
                    color: 1, 1, 1, 1

            # Auto-Rickshaws Card
            BoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.15, 0.20, 0.30, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: 'Auto-Rickshaws 🛺'
                    font_size: '15sp'
                    color: 1, 0.85, 0.3, 1
                Label:
                    text: str(root.auto_count)
                    font_size: '32sp'
                    bold: True
                    color: 1, 1, 1, 1

            # E-Rickshaws Card
            BoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.15, 0.20, 0.30, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: 'E-Rickshaws ⚡'
                    font_size: '15sp'
                    color: 0.3, 0.9, 0.9, 1
                Label:
                    text: str(root.erickshaw_count)
                    font_size: '32sp'
                    bold: True
                    color: 1, 1, 1, 1

            # Heavy Trucks Card
            BoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.15, 0.20, 0.30, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: 'Heavy Trucks 🚛'
                    font_size: '15sp'
                    color: 1, 0.4, 0.4, 1
                Label:
                    text: str(root.truck_count)
                    font_size: '32sp'
                    bold: True
                    color: 1, 1, 1, 1

            # Buses Card
            BoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.15, 0.20, 0.30, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: 'Buses / Minibuses 🚌'
                    font_size: '15sp'
                    color: 0.9, 0.6, 1, 1
                Label:
                    text: str(root.bus_count)
                    font_size: '32sp'
                    bold: True
                    color: 1, 1, 1, 1

            # LCV / Tempo Card
            BoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.15, 0.20, 0.30, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: 'Light Commercial (LCV) 🚐'
                    font_size: '14sp'
                    color: 0.9, 0.8, 0.5, 1
                Label:
                    text: str(root.lcv_count)
                    font_size: '32sp'
                    bold: True
                    color: 1, 1, 1, 1

            # Total Volume Card
            BoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                canvas.before:
                    Color:
                        rgba: 0.25, 0.35, 0.50, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: 'Total Real Vehicles 📊'
                    font_size: '15sp'
                    bold: True
                    color: 1, 1, 1, 1
                Label:
                    text: str(root.total_count)
                    font_size: '34sp'
                    bold: True
                    color: 0.3, 1, 0.5, 1

        # Control & Stream Action Panel
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)

            Button:
                text: 'Fetch REAL Live Traffic API Data (OSM & OSRM)'
                background_normal: ''
                background_color: 0.2, 0.55, 0.85, 1
                bold: True
                on_release: root.fetch_real_traffic_api_data()

            Button:
                text: 'Process Traffic Stream / OpenCV AI Detection'
                background_normal: ''
                background_color: 0.7, 0.3, 0.7, 1
                bold: True
                on_release: root.run_live_vision_ai()

        # Environmental Impact Panel
        BoxLayout:
            orientation: 'vertical'
            padding: dp(10)
            spacing: dp(5)
            canvas.before:
                Color:
                    rgba: 0.12, 0.14, 0.18, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            Label:
                text: f"Live Traffic Speed: {root.speed_text} km/h | Congestion Index: {root.congestion_text} | Source: {root.source_text}"
                font_size: '13sp'
                color: 0.4, 0.9, 1, 1
                bold: True

            Label:
                text: f"Heavy Vehicle Share: {root.heavy_share_text} | Est. Vehicle PM2.5 Contribution: {root.pm25_impact_text} | CO2: {root.co2_text} kg/hr"
                font_size: '12sp'
                color: 0.9, 0.9, 0.9, 1


<InfoScreen>:
    name: 'info_screen'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(10)

        Label:
            text: 'About TerraAid Project'
            font_size: '22sp'
            bold: True
            size_hint_y: None
            height: dp(40)

        ScrollView:
            Label:
                text: 'TerraAid is a comprehensive environmental & transport monitoring platform.\\n\\nFeatures:\\n1. Real-time Air Quality Index (AQI) for Delhi NCR stations and worldwide regions via OpenAQ.\\n2. REAL Traffic API & Vehicle Classifier fetching live speed, congestion indices, and vehicle counts.\\n3. Dataset Download Engine allowing one-click export of AQI and transport tallies to CSV and JSON formats.\\n\\nDeveloper: TerraAid Team'
                text_size: self.width, None
                valign: 'top'

        Button:
            text: 'Back to Map'
            size_hint_y: None
            height: dp(45)
            on_release: app.root.current = 'map_screen'
"""

class MapScreen(Screen):
    map_source = StringProperty("osm")
    card_title_text = StringProperty("Delhi Region AQI")
    aqi_value = StringProperty("245")
    aqi_category_text = StringProperty("Very Poor")
    aqi_color_rgba = ListProperty([0.8, 0.2, 0.2, 1])
    pm25_text = StringProperty("245")
    pm10_text = StringProperty("380")
    no2_text = StringProperty("85")
    co_text = StringProperty("1.8")
    so2_text = StringProperty("22")
    advisory_text = StringProperty("Wear N95 mask outdoors.")
    status_message_text = StringProperty("TerraAid Ready. Active Region: Delhi NCR.")

    station_markers = []

    def on_enter(self, *args):
        Clock.schedule_once(lambda dt: self.load_delhi_stations(), 0.5)

    def load_delhi_stations(self):
        map_view = self.ids.map_view
        
        for m in self.station_markers:
            map_view.remove_marker(m)
        self.station_markers.clear()

        for st in DELHI_STATIONS:
            marker = MapMarker(lat=st["lat"], lon=st["lon"])
            map_view.add_marker(marker)
            self.station_markers.append(marker)

        map_view.center_on(28.6139, 77.2090)
        self.update_aqi_display("Anand Vihar, Delhi", 28.6469, 77.3160)
        self.status_message_text = f"Loaded {len(DELHI_STATIONS)} Delhi NCR AQI monitoring stations."

    def perform_region_search(self):
        query = self.ids.search_input.text.strip()
        if not query:
            query = "Delhi"

        lat, lon, display_name = search_region_coordinates(query)
        self.ids.map_view.center_on(lat, lon)
        self.update_aqi_display(display_name, lat, lon)

    def update_aqi_display(self, location_name, lat, lon):
        data = fetch_live_aqi(lat, lon)
        self.card_title_text = location_name[:28]
        self.aqi_value = str(data["aqi"])
        self.aqi_category_text = data["category"]
        self.aqi_color_rgba = data["color"]
        self.pm25_text = str(data["pm25"])
        self.pm10_text = str(data["pm10"])
        self.no2_text = str(data["no2"])
        self.co_text = str(data["co"])
        self.so2_text = str(data["so2"])
        self.advisory_text = data["advisory"]
        self.status_message_text = f"AQI updated for {location_name} via {data['source']}."

    def download_dataset_popup(self):
        csv_path = export_dataset_to_csv()
        json_path = export_dataset_to_json()

        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        lbl = Label(
            text=f"Dataset successfully exported and ready for download!\n\nCSV File Path:\n{csv_path}\n\nJSON File Path:\n{json_path}",
            font_size='13sp',
            text_size=(380, None),
            halign='left'
        )
        content.add_widget(lbl)

        btn = Button(text="OK / Close", size_hint_y=None, height=40, background_color=(0.2, 0.7, 0.4, 1))
        content.add_widget(btn)

        popup = Popup(title="Dataset Download Complete", content=content, size_hint=(None, None), size=(420, 320))
        btn.bind(on_release=popup.dismiss)
        popup.open()


class VehicleScreen(Screen):
    car_count = NumericProperty(385)
    bike_count = NumericProperty(320)
    auto_count = NumericProperty(100)
    erickshaw_count = NumericProperty(55)
    truck_count = NumericProperty(27)
    bus_count = NumericProperty(18)
    lcv_count = NumericProperty(36)
    total_count = NumericProperty(941)

    speed_text = StringProperty("24.5")
    congestion_text = StringProperty("1.35")
    source_text = StringProperty("Live OSRM & OpenStreetMap API")
    heavy_share_text = StringProperty("4.8%")
    pm25_impact_text = StringProperty("+126.0 ug/m3")
    co2_text = StringProperty("150.5")

    def on_enter(self, *args):
        self.fetch_real_traffic_api_data()

    def fetch_real_traffic_api_data(self):
        info = detector_engine.fetch_real_traffic_flow(28.6139, 77.2090, "Delhi Central Corridor")
        c = info["counts"]
        self.car_count = c["Cars"]
        self.bike_count = c["Bikes & Motorcycles"]
        self.auto_count = c["Auto-Rickshaws"]
        self.erickshaw_count = c["E-Rickshaws"]
        self.truck_count = c["Heavy Trucks"]
        self.bus_count = c["Buses / Minibuses"]
        self.lcv_count = c["Light Commercial Vehicles (Tempo/Van)"]
        self.total_count = info["total_vehicles"]

        self.speed_text = str(info["real_avg_speed_kmh"])
        self.congestion_text = str(info["real_congestion_index"])
        self.source_text = info["data_source"]
        self.heavy_share_text = f"{info['heavy_vehicle_share_percent']}%"
        self.pm25_impact_text = f"+{info['estimated_pm25_impact_ugm3']} ug/m3"
        self.co2_text = str(info['estimated_co2_kg_per_hr'])

    def run_live_vision_ai(self):
        info = detector_engine.process_live_vision_detection()
        c = info["counts"]
        self.car_count = c["Cars"]
        self.bike_count = c["Bikes & Motorcycles"]
        self.auto_count = c["Auto-Rickshaws"]
        self.erickshaw_count = c["E-Rickshaws"]
        self.truck_count = c["Heavy Trucks"]
        self.bus_count = c["Buses / Minibuses"]
        self.lcv_count = c["Light Commercial Vehicles (Tempo/Van)"]
        self.total_count = info["total_vehicles"]

        self.source_text = info["source"]
        self.heavy_share_text = f"{info['heavy_vehicle_share_percent']}%"
        self.pm25_impact_text = f"+{info['estimated_pm25_impact_ugm3']} ug/m3"
        self.co2_text = str(info['estimated_co2_kg_per_hr'])

    def download_dataset_popup(self):
        csv_path = export_dataset_to_csv()
        json_path = export_dataset_to_json()

        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        lbl = Label(
            text=f"Dataset successfully exported and ready for download!\n\nCSV File Path:\n{csv_path}\n\nJSON File Path:\n{json_path}",
            font_size='13sp',
            text_size=(380, None),
            halign='left'
        )
        content.add_widget(lbl)

        btn = Button(text="OK / Close", size_hint_y=None, height=40, background_color=(0.2, 0.7, 0.4, 1))
        content.add_widget(btn)

        popup = Popup(title="Dataset Download Complete", content=content, size_hint=(None, None), size=(420, 320))
        btn.bind(on_release=popup.dismiss)
        popup.open()


class InfoScreen(Screen):
    pass


class TerraAidApp(App):
    def build(self):
        self.title = "TerraAid - REAL Delhi AQI & Live Traffic Transport Analytics"
        return Builder.load_string(KV)

    def on_start(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA,
                    Permission.INTERNET,
                    Permission.ACCESS_FINE_LOCATION,
                    Permission.ACCESS_COARSE_LOCATION,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])
            except Exception as e:
                print(f"Android permission request error: {e}")

if __name__ == '__main__':
    TerraAidApp().run()