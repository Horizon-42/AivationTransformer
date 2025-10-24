
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
