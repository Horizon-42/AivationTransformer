#!/usr/bin/env python3
"""
Streamlit + PyDeck 实时航空可视化
===============================

使用 Streamlit 和 PyDeck 创建真正的实时交互式航空天气可视化，
支持飞行轨迹模拟和实时语音播报。
"""

import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 设置页面配置
st.set_page_config(
    page_title="🛩️ Real-time Aviation Control",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository
except ImportError:
    st.warning("❌ Weather database not available, using simulation data")


class RealTimeAviationApp:
    """实时航空应用 - 支持完整的 Python 交互"""
    
    def __init__(self):
        self.airports = {
            'CYYZ': {'lat': 43.6777, 'lon': -79.6248, 'name': 'Toronto Pearson', 'elevation': 173},
            'CYVR': {'lat': 49.1967, 'lon': -123.1815, 'name': 'Vancouver Intl', 'elevation': 4},
            'CYUL': {'lat': 45.4706, 'lon': -73.7378, 'name': 'Montreal Trudeau', 'elevation': 36},
            'CYYC': {'lat': 51.1315, 'lon': -114.0109, 'name': 'Calgary Intl', 'elevation': 1099},
            'CYOW': {'lat': 45.3192, 'lon': -75.6692, 'name': 'Ottawa Macdonald-Cartier', 'elevation': 114},
            'CYWG': {'lat': 49.9100, 'lon': -97.2398, 'name': 'Winnipeg Richardson', 'elevation': 239},
            'CYEG': {'lat': 51.3089, 'lon': -113.5803, 'name': 'Edmonton Intl', 'elevation': 723},
            'CYHZ': {'lat': 44.8807, 'lon': -63.5086, 'name': 'Halifax Stanfield', 'elevation': 145}
        }
        
        # 初始化会话状态
        if 'flight_active' not in st.session_state:
            st.session_state.flight_active = False
        if 'selected_route' not in st.session_state:
            st.session_state.selected_route = []
        if 'current_position' not in st.session_state:
            st.session_state.current_position = None
        if 'weather_data' not in st.session_state:
            st.session_state.weather_data = {}
    
    def generate_weather_data(self, station_code):
        """生成实时天气数据（模拟或真实）"""
        # 模拟实时天气数据
        import random
        
        conditions = ['Clear', 'Partly Cloudy', 'Overcast', 'Rain', 'Snow']
        
        weather = {
            'station': station_code,
            'visibility': random.randint(1000, 10000),
            'wind_speed': random.randint(5, 25),
            'wind_direction': random.randint(0, 359),
            'temperature': random.randint(-10, 30),
            'conditions': random.choice(conditions),
            'ceiling': random.randint(200, 3000),
            'timestamp': datetime.now()
        }
        
        # 存储到会话状态
        st.session_state.weather_data[station_code] = weather
        return weather
    
    def get_flight_category(self, visibility, ceiling):
        """根据能见度和云底高度确定飞行类别"""
        if visibility >= 8000 and ceiling >= 1000:
            return 'VFR', '#22c55e'  # Green
        elif visibility >= 5000 and ceiling >= 500:
            return 'MVFR', '#eab308'  # Yellow
        elif visibility >= 1600 and ceiling >= 200:
            return 'IFR', '#ef4444'   # Red
        else:
            return 'LIFR', '#7c2d12'  # Dark Red
    
    def create_airport_dataframe(self):
        """创建机场数据框架"""
        data = []
        
        for code, info in self.airports.items():
            # 获取天气数据
            weather = self.generate_weather_data(code)
            category, color = self.get_flight_category(weather['visibility'], weather['ceiling'])
            
            data.append({
                'code': code,
                'name': info['name'],
                'lat': info['lat'],
                'lon': info['lon'],
                'elevation': info['elevation'],
                'visibility': weather['visibility'],
                'wind_speed': weather['wind_speed'],
                'temperature': weather['temperature'],
                'conditions': weather['conditions'],
                'category': category,
                'color': color
            })
        
        return pd.DataFrame(data)
    
    def create_3d_map(self, airport_df, flight_path=None):
        """创建 3D 地图可视化"""
        
        # 机场图层
        airports_layer = pdk.Layer(
            'ScatterplotLayer',
            data=airport_df,
            get_position=['lon', 'lat'],
            get_color='color',
            get_radius=20000,
            radius_scale=1,
            radius_min_pixels=5,
            radius_max_pixels=50,
            pickable=True,
            auto_highlight=True
        )
        
        # 机场标签图层
        text_layer = pdk.Layer(
            'TextLayer',
            data=airport_df,
            get_position=['lon', 'lat'],
            get_text='code',
            get_size=12,
            get_color=[255, 255, 255, 200],
            get_angle=0,
            get_text_anchor='"middle"',
            get_alignment_baseline='"center"'
        )
        
        layers = [airports_layer, text_layer]
        
        # 飞行路径图层
        if flight_path is not None and len(flight_path) > 1:
            path_layer = pdk.Layer(
                'PathLayer',
                data=[{'path': [[row['lon'], row['lat']] for _, row in flight_path.iterrows()]}],
                get_path='path',
                get_width=5,
                get_color=[255, 107, 53, 200],
                width_scale=1000,
                pickable=True
            )
            layers.append(path_layer)
        
        # 当前飞机位置
        if st.session_state.current_position:
            pos = st.session_state.current_position
            aircraft_layer = pdk.Layer(
                'IconLayer',
                data=pd.DataFrame([pos]),
                get_position=['lon', 'lat'],
                get_icon_data=[{
                    'url': 'https://img.icons8.com/color/48/000000/airplane-mode-on.png',
                    'width': 48,
                    'height': 48,
                    'anchorY': 24,
                    'anchorX': 24
                }],
                get_size=4,
                size_scale=10,
                pickable=True
            )
            layers.append(aircraft_layer)
        
        # 创建地图
        view_state = pdk.ViewState(
            longitude=-106.3468,
            latitude=56.1304,
            zoom=3,
            pitch=50,
            bearing=0
        )
        
        return pdk.Deck(
            map_style='mapbox://styles/mapbox/satellite-streets-v11',
            initial_view_state=view_state,
            layers=layers,
            tooltip={
                'html': '<b>{code}</b><br/>'
                       'Name: {name}<br/>'
                       'Weather: {conditions}<br/>'
                       'Visibility: {visibility}m<br/>'
                       'Wind: {wind_speed} knots<br/>'
                       'Category: <b>{category}</b>',
                'style': {'backgroundColor': 'steelblue', 'color': 'white'}
            }
        )
    
    def simulate_flight(self, route):
        """模拟飞行过程"""
        if len(route) < 2:
            return
        
        st.session_state.flight_active = True
        
        # 创建飞行路径的插值点
        flight_points = []
        
        for i in range(len(route) - 1):
            start = route.iloc[i]
            end = route.iloc[i + 1]
            
            # 在两点间创建 20 个插值点
            for step in range(20):
                progress = step / 20
                lat = start['lat'] + (end['lat'] - start['lat']) * progress
                lon = start['lon'] + (end['lon'] - start['lon']) * progress
                
                flight_points.append({
                    'lat': lat,
                    'lon': lon,
                    'segment': i,
                    'progress': progress
                })
        
        return flight_points
    
    def text_to_speech(self, text):
        """文本转语音播报"""
        # 在 Streamlit 中使用浏览器的 Web Speech API
        st.markdown(f"""
        <script>
        if ('speechSynthesis' in window) {{
            var utterance = new SpeechSynthesisUtterance("{text}");
            utterance.rate = 0.8;
            utterance.pitch = 1.0;
            speechSynthesis.speak(utterance);
        }}
        </script>
        """, unsafe_allow_html=True)
    
    def run(self):
        """运行应用"""
        
        st.title("🛩️ Real-time Aviation Weather Control Center")
        st.markdown("**Interactive flight planning with real-time weather and voice reports**")
        
        # 侧边栏控制面板
        with st.sidebar:
            st.header("🎛️ Flight Control Panel")
            
            # 天气更新
            if st.button("🌤️ Update Weather Data"):
                st.session_state.weather_data = {}
                st.rerun()
            
            st.subheader("✈️ Flight Planning")
            
            # 路径选择
            available_airports = list(self.airports.keys())
            
            departure = st.selectbox("Departure Airport", available_airports, key="departure")
            destination = st.selectbox("Destination Airport", available_airports, key="destination", index=1)
            
            # 中途停留点
            waypoints = st.multiselect("Waypoints (optional)", 
                                     [code for code in available_airports 
                                      if code not in [departure, destination]],
                                     key="waypoints")
            
            # 构建路径
            if st.button("📍 Plan Route"):
                route_codes = [departure] + waypoints + [destination]
                route_data = []
                for code in route_codes:
                    airport = self.airports[code]
                    route_data.append({
                        'code': code,
                        'name': airport['name'],
                        'lat': airport['lat'],
                        'lon': airport['lon']
                    })
                st.session_state.selected_route = pd.DataFrame(route_data)
                st.success(f"Route planned: {' → '.join(route_codes)}")
            
            # 飞行模拟
            if len(st.session_state.selected_route) >= 2:
                if st.button("🚀 Start Flight Simulation"):
                    st.session_state.flight_active = True
                    st.success("Flight simulation started!")
                
                if st.button("⏹️ Stop Flight"):
                    st.session_state.flight_active = False
                    st.session_state.current_position = None
                
                # 飞行速度控制
                flight_speed = st.slider("Flight Speed (km/h)", 200, 800, 500)
            
            # 语音播报
            st.subheader("🔊 Voice Reports")
            selected_station = st.selectbox("Select station for weather report", available_airports)
            
            if st.button("📢 Generate Voice Report"):
                if selected_station in st.session_state.weather_data:
                    weather = st.session_state.weather_data[selected_station]
                    report = f"""Station {selected_station}: Current weather conditions are {weather['conditions'].lower()}, 
                    visibility {weather['visibility']} meters, wind from {weather['wind_direction']} degrees 
                    at {weather['wind_speed']} knots, temperature {weather['temperature']} degrees Celsius."""
                    
                    st.text_area("Weather Report", report, height=100)
                    self.text_to_speech(report)
        
        # 主要内容区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 创建机场数据
            airport_df = self.create_airport_dataframe()
            
            # 飞行路径
            flight_path = None
            if len(st.session_state.selected_route) >= 2:
                flight_path = st.session_state.selected_route
            
            # 飞行模拟
            if st.session_state.flight_active and flight_path is not None:
                flight_points = self.simulate_flight(flight_path)
                
                # 模拟飞行进度
                if 'flight_step' not in st.session_state:
                    st.session_state.flight_step = 0
                
                if st.session_state.flight_step < len(flight_points):
                    current_point = flight_points[st.session_state.flight_step]
                    st.session_state.current_position = current_point
                    st.session_state.flight_step += 1
                    
                    # 自动刷新
                    time.sleep(1)
                    st.rerun()
                else:
                    st.session_state.flight_active = False
                    st.success("✅ Flight completed!")
            
            # 创建和显示地图
            deck = self.create_3d_map(airport_df, flight_path)
            st.pydeck_chart(deck, use_container_width=True)
        
        with col2:
            st.subheader("📊 Flight Status")
            
            # 显示当前路径
            if len(st.session_state.selected_route) >= 2:
                st.write("**Current Route:**")
                for i, row in st.session_state.selected_route.iterrows():
                    st.write(f"{i+1}. {row['code']} - {row['name']}")
            
            # 飞行状态
            if st.session_state.flight_active:
                st.success("🛩️ Flight Active")
                if st.session_state.current_position:
                    pos = st.session_state.current_position
                    st.write(f"**Position:** {pos['lat']:.4f}, {pos['lon']:.4f}")
            else:
                st.info("✈️ Flight Inactive")
            
            # 天气状况表格
            st.subheader("🌤️ Current Weather")
            
            # 显示天气数据
            weather_display = []
            for code, info in self.airports.items():
                if code in st.session_state.weather_data:
                    weather = st.session_state.weather_data[code]
                    category, _ = self.get_flight_category(weather['visibility'], weather['ceiling'])
                    weather_display.append({
                        'Station': code,
                        'Conditions': weather['conditions'],
                        'Visibility': f"{weather['visibility']}m",
                        'Wind': f"{weather['wind_speed']}kt",
                        'Temp': f"{weather['temperature']}°C",
                        'Category': category
                    })
            
            if weather_display:
                st.dataframe(pd.DataFrame(weather_display), use_container_width=True)
        
        # 自动刷新控制
        if st.session_state.flight_active:
            time.sleep(0.5)
            st.rerun()


def main():
    """主函数"""
    app = RealTimeAviationApp()
    app.run()


if __name__ == "__main__":
    main()