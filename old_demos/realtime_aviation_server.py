#!/usr/bin/env python3
"""
Flask + Folium 实时交互演示
============================

展示如何让 Folium 地图与 Python 后端实时交互，
包括实时天气数据获取和路径规划。
"""

from flask import Flask, render_template, jsonify, request
import folium
import json
import sys
from pathlib import Path
from datetime import datetime
import threading
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from METAR_convert.storage.sqlite_repository import SQLiteWeatherRepository
except ImportError:
    print("❌ SQLAlchemy not available, using mock data")


class RealTimeAviationServer:
    """实时航空天气服务器，支持 Folium 地图与 Python 后端交互"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.repo = None
        self.flight_simulation = {
            'active': False,
            'current_position': None,
            'route': [],
            'speed': 500  # km/h
        }
        
        # 初始化数据库
        try:
            self.repo = SQLiteWeatherRepository("weather_data/weather.db")
        except:
            print("⚠️ Using mock weather data")
            
        self._setup_routes()
    
    def _setup_routes(self):
        """设置 Flask 路由"""
        
        @self.app.route('/')
        def index():
            return self.create_interactive_map()
        
        @self.app.route('/api/weather/<station_code>')
        def get_weather(station_code):
            """实时获取天气数据 API"""
            try:
                if self.repo:
                    weather_data = self.repo.query_weather_data([station_code], hours_back=1)
                    if weather_data:
                        latest = weather_data[0]
                        return jsonify({
                            'station': station_code,
                            'weather': {
                                'visibility': getattr(latest, 'visibility_meters', 'N/A'),
                                'wind_speed': getattr(latest, 'wind_speed_knots', 'N/A'),
                                'temperature': getattr(latest, 'temperature_celsius', 'N/A'),
                                'conditions': getattr(latest, 'weather_phenomena', 'Clear'),
                                'timestamp': getattr(latest, 'observation_time', datetime.now()).isoformat()
                            }
                        })
                
                # 模拟数据
                return jsonify({
                    'station': station_code,
                    'weather': {
                        'visibility': '10000',
                        'wind_speed': '15',
                        'temperature': '22',
                        'conditions': 'Clear',
                        'timestamp': datetime.now().isoformat()
                    }
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/route/optimize', methods=['POST'])
        def optimize_route():
            """路径优化 API"""
            data = request.json
            stations = data.get('stations', [])
            
            # 简单的路径优化算法（实际项目中可以使用更复杂的算法）
            optimized = self._optimize_flight_route(stations)
            
            return jsonify({
                'original': stations,
                'optimized': optimized['route'],
                'total_distance': optimized['distance'],
                'estimated_time': optimized['time']
            })
        
        @self.app.route('/api/flight/start', methods=['POST'])
        def start_flight_simulation():
            """开始飞行模拟"""
            data = request.json
            route = data.get('route', [])
            
            if len(route) < 2:
                return jsonify({'error': 'Need at least 2 waypoints'}), 400
            
            self.flight_simulation['route'] = route
            self.flight_simulation['current_position'] = route[0]
            self.flight_simulation['active'] = True
            
            # 在后台线程中运行飞行模拟
            threading.Thread(target=self._simulate_flight, daemon=True).start()
            
            return jsonify({'status': 'Flight simulation started'})
        
        @self.app.route('/api/flight/position')
        def get_flight_position():
            """获取当前飞行位置"""
            return jsonify({
                'active': self.flight_simulation['active'],
                'position': self.flight_simulation['current_position'],
                'route': self.flight_simulation['route']
            })
        
        @self.app.route('/api/audio/weather/<station_code>')
        def get_weather_audio(station_code):
            """生成天气语音播报"""
            # 这里可以集成 TTS (Text-to-Speech) 引擎
            weather_text = self._generate_weather_speech(station_code)
            
            return jsonify({
                'station': station_code,
                'speech_text': weather_text,
                'audio_url': f'/audio/{station_code}.mp3'  # 实际项目中生成音频文件
            })
    
    def _optimize_flight_route(self, stations):
        """简单的路径优化算法"""
        # 这里可以实现更复杂的算法，如最短路径、考虑天气等
        import random
        
        optimized_route = stations.copy()
        random.shuffle(optimized_route[1:-1])  # 保持起点和终点，优化中间点
        
        # 计算距离（简化计算）
        total_distance = len(stations) * 200  # 假设平均 200km
        estimated_time = total_distance / self.flight_simulation['speed']
        
        return {
            'route': optimized_route,
            'distance': total_distance,
            'time': estimated_time
        }
    
    def _simulate_flight(self):
        """后台飞行模拟"""
        route = self.flight_simulation['route']
        
        for i in range(len(route) - 1):
            current = route[i]
            next_point = route[i + 1]
            
            # 模拟飞行过程（插值计算中间位置）
            steps = 20  # 20个中间步骤
            for step in range(steps):
                if not self.flight_simulation['active']:
                    return
                
                progress = step / steps
                # 简单线性插值
                lat = current['lat'] + (next_point['lat'] - current['lat']) * progress
                lon = current['lon'] + (next_point['lon'] - current['lon']) * progress
                
                self.flight_simulation['current_position'] = {'lat': lat, 'lon': lon}
                time.sleep(0.5)  # 每0.5秒更新一次位置
        
        self.flight_simulation['active'] = False
    
    def _generate_weather_speech(self, station_code):
        """生成天气语音播报文本"""
        # 这里可以集成你的天气数据和 TTS
        return f"Station {station_code}: Current weather conditions are clear skies, visibility 10 kilometers, wind from 270 degrees at 15 knots, temperature 22 degrees Celsius."
    
    def create_interactive_map(self):
        """创建支持实时交互的地图"""
        
        # 创建基础地图
        canada_center = [56.1304, -106.3468]
        map_html = folium.Map(
            location=canada_center,
            zoom_start=4,
            tiles='OpenStreetMap'
        )
        
        # 添加主要机场
        airports = {
            'CYYZ': {'lat': 43.6777, 'lon': -79.6248, 'name': 'Toronto Pearson'},
            'CYVR': {'lat': 49.1967, 'lon': -123.1815, 'name': 'Vancouver Intl'},
            'CYUL': {'lat': 45.4706, 'lon': -73.7378, 'name': 'Montreal Trudeau'},
            'CYYC': {'lat': 51.1315, 'lon': -114.0109, 'name': 'Calgary Intl'},
        }
        
        for code, info in airports.items():
            folium.Marker(
                [info['lat'], info['lon']],
                popup=f"{code}: {info['name']}",
                tooltip=f"Click for real-time weather",
                icon=folium.Icon(color='blue', icon='plane')
            ).add_to(map_html)
        
        # 添加实时交互 JavaScript
        realtime_js = """
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script>
        var flightMarker = null;
        var flightPath = null;
        
        // 实时获取天气数据
        function getRealtimeWeather(stationCode) {
            $.get('/api/weather/' + stationCode, function(data) {
                var weather = data.weather;
                var message = `Station: ${data.station}\\n` +
                             `Visibility: ${weather.visibility}m\\n` +
                             `Wind: ${weather.wind_speed} knots\\n` +
                             `Temperature: ${weather.temperature}°C\\n` +
                             `Conditions: ${weather.conditions}\\n` +
                             `Time: ${weather.timestamp}`;
                alert(message);
                
                // 播放语音播报
                playWeatherAudio(stationCode);
            });
        }
        
        // 路径优化
        function optimizeRoute(stations) {
            $.post('/api/route/optimize', 
                JSON.stringify({stations: stations}),
                function(data) {
                    console.log('Optimized route:', data);
                    alert(`Route optimized! Distance: ${data.total_distance}km, Time: ${data.estimated_time.toFixed(1)}h`);
                },
                'json'
            ).fail(function() {
                alert('Route optimization failed');
            });
        }
        
        // 开始飞行模拟
        function startFlightSimulation(route) {
            $.post('/api/flight/start',
                JSON.stringify({route: route}),
                function(data) {
                    console.log('Flight started:', data);
                    startPositionTracking();
                },
                'json'
            );
        }
        
        // 实时位置跟踪
        function startPositionTracking() {
            var trackingInterval = setInterval(function() {
                $.get('/api/flight/position', function(data) {
                    if (!data.active) {
                        clearInterval(trackingInterval);
                        return;
                    }
                    
                    // 更新飞机位置
                    updateFlightPosition(data.position);
                });
            }, 1000); // 每秒更新
        }
        
        // 更新飞机位置标记
        function updateFlightPosition(position) {
            if (flightMarker) {
                map.removeLayer(flightMarker);
            }
            
            flightMarker = L.marker([position.lat, position.lon], {
                icon: L.divIcon({
                    html: '✈️',
                    className: 'flight-marker',
                    iconSize: [20, 20]
                })
            }).addTo(map);
        }
        
        // 语音播报
        function playWeatherAudio(stationCode) {
            $.get('/api/audio/weather/' + stationCode, function(data) {
                // 使用 Web Speech API 播放语音
                if ('speechSynthesis' in window) {
                    var utterance = new SpeechSynthesisUtterance(data.speech_text);
                    utterance.rate = 0.8;
                    utterance.pitch = 1.0;
                    speechSynthesis.speak(utterance);
                }
            });
        }
        
        // 为地图标记添加点击事件
        map.on('click', function(e) {
            // 可以在这里添加更多交互功能
            console.log('Map clicked at:', e.latlng);
        });
        
        </script>
        
        <style>
        .flight-marker {
            font-size: 16px;
            text-align: center;
        }
        
        .realtime-panel {
            position: fixed;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            font-family: Arial, sans-serif;
        }
        </style>
        
        <div class="realtime-panel">
            <h4>🛩️ Real-time Aviation Control</h4>
            <button onclick="getRealtimeWeather('CYYZ')">Get CYYZ Weather</button><br><br>
            <button onclick="optimizeRoute([{lat:43.6777,lon:-79.6248},{lat:49.1967,lon:-123.1815}])">Optimize Route</button><br><br>
            <button onclick="startFlightSimulation([{lat:43.6777,lon:-79.6248},{lat:49.1967,lon:-123.1815}])">Start Flight Sim</button>
        </div>
        """
        
        map_html.get_root().html.add_child(folium.Element(realtime_js))
        
        # 返回 HTML 字符串
        return map_html._repr_html_()
    
    def run(self, debug=True, port=5000):
        """启动服务器"""
        print(f"🚀 Starting Real-time Aviation Server on http://localhost:{port}")
        print("🎯 Features:")
        print("   • Real-time weather data API")
        print("   • Flight route optimization") 
        print("   • Flight simulation with position tracking")
        print("   • Voice weather reports")
        print("   • Full Python backend integration")
        
        self.app.run(debug=debug, port=port)


if __name__ == "__main__":
    server = RealTimeAviationServer()
    server.run()