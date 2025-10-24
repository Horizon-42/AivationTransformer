#!/usr/bin/env python3
"""
快速安装和演示脚本
================

一键安装现代化交互框架并运行演示
"""

import subprocess
import sys
import os
from pathlib import Path

def install_packages():
    """安装必要的包"""
    
    packages = [
        'streamlit',
        'pydeck', 
        'plotly',
        'dash',
        'pyttsx3',  # TTS
        'flask',
        'flask-socketio'
    ]
    
    print("🚀 Installing modern interactive visualization packages...")
    print("📦 Installing:", ", ".join(packages))
    
    for package in packages:
        try:
            print(f"   Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"   ✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"   ⚠️ Failed to install {package}")
    
    print("\n✅ Installation complete!")

def create_simple_streamlit_demo():
    """创建一个简单的 Streamlit 演示"""
    
    demo_code = '''
import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="🛩️ Aviation Demo", page_icon="✈️")

st.title("🛩️ Interactive Aviation Demo")
st.markdown("**Click the buttons to see real-time Python interaction!**")

# 加拿大主要机场
airports = {
    'CYYZ': {'lat': 43.6777, 'lon': -79.6248, 'name': 'Toronto Pearson'},
    'CYVR': {'lat': 49.1967, 'lon': -123.1815, 'name': 'Vancouver Intl'},
    'CYUL': {'lat': 45.4706, 'lon': -73.7378, 'name': 'Montreal Trudeau'},
    'CYYC': {'lat': 51.1315, 'lon': -114.0109, 'name': 'Calgary Intl'},
}

# 侧边栏控制
with st.sidebar:
    st.header("🎛️ Flight Control")
    
    if st.button("🌤️ Update Weather"):
        st.success("Weather updated! (This is real Python execution)")
        st.rerun()
    
    departure = st.selectbox("From", list(airports.keys()))
    destination = st.selectbox("To", [k for k in airports.keys() if k != departure])
    
    if st.button("✈️ Start Flight Simulation"):
        st.session_state.flight_active = True
        st.success("Flight started!")

# 主要显示区域
col1, col2 = st.columns([2, 1])

with col1:
    # 创建机场数据
    airport_data = []
    for code, info in airports.items():
        airport_data.append({
            'code': code,
            'name': info['name'],
            'lat': info['lat'],
            'lon': info['lon'],
            'elevation': np.random.randint(0, 1000)  # 模拟高度
        })
    
    df = pd.DataFrame(airport_data)
    
    # 3D 地图
    layer = pdk.Layer(
        'ColumnLayer',
        data=df,
        get_position=['lon', 'lat'],
        get_elevation='elevation',
        elevation_scale=50,
        radius=20000,
        get_fill_color=[255, 165, 0, 140],
        pickable=True,
        auto_highlight=True,
    )
    
    view_state = pdk.ViewState(
        longitude=-106.3468,
        latitude=56.1304,
        zoom=3,
        pitch=50,
    )
    
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={'text': '{code}: {name}\\nElevation: {elevation}m'}
    )
    
    st.pydeck_chart(deck, use_container_width=True)

with col2:
    st.subheader("📊 Flight Status")
    
    # 实时状态更新
    if hasattr(st.session_state, 'flight_active') and st.session_state.flight_active:
        st.success("🛩️ Flight Active")
        
        # 模拟飞行进度
        progress = st.progress(0)
        status_text = st.empty()
        
        for i in range(100):
            progress.progress(i + 1)
            status_text.text(f'Flight progress: {i+1}%')
            time.sleep(0.01)
        
        st.success("✅ Flight completed!")
        st.session_state.flight_active = False
    else:
        st.info("✈️ Ready for departure")
    
    # 机场信息
    st.subheader("🛫 Airports")
    for code, info in airports.items():
        st.write(f"**{code}**: {info['name']}")

# 语音播报演示
if st.button("🔊 Weather Report (Text-to-Speech)"):
    weather_text = f"Current weather at {departure}: Clear skies, visibility 10 kilometers, wind calm, temperature 22 degrees Celsius."
    st.text_area("Weather Report", weather_text, height=100)
    
    # 尝试语音播报
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(weather_text)
        engine.runAndWait()
        st.success("🔊 Voice report played!")
    except:
        st.info("💡 Install pyttsx3 for voice functionality: pip install pyttsx3")

st.markdown("---")
st.markdown("**🎯 This demonstrates real-time Python interaction!**")
st.markdown("- ✅ Buttons directly execute Python code")
st.markdown("- ✅ Real-time UI updates with st.rerun()")  
st.markdown("- ✅ 3D visualization with PyDeck")
st.markdown("- ✅ Text-to-speech integration")
st.markdown("- ✅ Session state management")
'''
    
    with open('streamlit_demo.py', 'w') as f:
        f.write(demo_code)
    
    print("📝 Created streamlit_demo.py")

def create_comparison_demo():
    """创建框架对比演示脚本"""
    
    comparison_script = '''
#!/bin/bash
echo "🚀 Aviation Visualization Framework Demos"
echo "========================================"
echo ""
echo "1. 🎯 Streamlit + PyDeck (Recommended)"
echo "   python -m streamlit run streamlit_demo.py"
echo ""
echo "2. 🗺️ Current Folium Interactive Route Builder"
echo "   python interactive_route_example.py"
echo "   # Then open the generated HTML file"
echo ""
echo "3. 🌐 Flask + Folium Real-time Server (Advanced)"
echo "   python realtime_aviation_server.py"
echo "   # Then visit http://localhost:5000"
echo ""
echo "Choose your demo:"
read -p "Enter number (1-3): " choice

case $choice in
    1)
        echo "🎯 Starting Streamlit demo..."
        python -m streamlit run streamlit_demo.py
        ;;
    2)
        echo "🗺️ Creating Folium interactive map..."
        python interactive_route_example.py
        echo "📂 Open the generated HTML file in your browser"
        ;;
    3)
        echo "🌐 Starting Flask server..."
        python realtime_aviation_server.py
        ;;
    *)
        echo "❌ Invalid choice"
        ;;
esac
'''
    
    with open('demo_launcher.sh', 'w') as f:
        f.write(comparison_script)
    
    # Make executable
    os.chmod('demo_launcher.sh', 0o755)
    
    print("📝 Created demo_launcher.sh")

def main():
    """主函数"""
    
    print("🛩️ Aviation Interactive Framework Setup")
    print("=" * 42)
    
    choice = input("""
Choose an option:
1. 📦 Install packages only
2. 🚀 Install packages + create demos
3. 📝 Create demos only
4. 📚 Show framework comparison

Enter choice (1-4): """).strip()
    
    if choice in ['1', '2']:
        install_packages()
    
    if choice in ['2', '3']:
        print("\n🎬 Creating demo files...")
        create_simple_streamlit_demo()
        create_comparison_demo()
        
        print("""
✅ Demo files created!

🚀 Quick Start:
   python -m streamlit run streamlit_demo.py
   
🎯 Or use the launcher:
   bash demo_launcher.sh
   
📚 Read the comparison:
   cat FRAMEWORK_COMPARISON.md
""")
    
    if choice == '4':
        if Path('FRAMEWORK_COMPARISON.md').exists():
            with open('FRAMEWORK_COMPARISON.md', 'r') as f:
                print(f.read())
        else:
            print("❌ Framework comparison document not found")
    
    print("\n🎉 Setup complete!")

if __name__ == "__main__":
    main()
    