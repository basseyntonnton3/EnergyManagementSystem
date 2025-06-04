from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import io
import plotly.utils
import plotly.io as pio
from functools import wraps
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import requests
from dotenv import load_dotenv
import pycountry
import pytz
import time
from geography import get_continents, get_countries, get_states
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # Secure secret key

# Configure static file serving
app.static_folder = 'static'
app.static_url_path = '/static'

# Data storage paths
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CONSUMPTIONS_FILE = os.path.join(DATA_DIR, 'consumptions.json')
CONTROLS_FILE = os.path.join(DATA_DIR, 'controls.json')
LOCATIONS_FILE = os.path.join(DATA_DIR, 'locations.json')
ABOUT_FILE = os.path.join(DATA_DIR, 'about.json')
FEATURES_FILE = os.path.join(DATA_DIR, 'features.json')

# Initialize data storage
data = {
    'users': [],
    'consumptions': [],
    'controls': [],
    'locations': [],
    'about': {
        'mission': "To revolutionize energy management by providing innovative, sustainable solutions that optimize energy consumption, reduce costs, and minimize environmental impact for businesses and communities across Nigeria.",
        'vision': "To become the leading energy management platform in Africa, driving the transition to sustainable energy practices and creating a greener future for generations to come.",
        'stats': [
            {'number': '100+', 'label': 'Businesses Served'},
            {'number': '30%', 'label': 'Average Energy Savings'},
            {'number': '24/7', 'label': 'Monitoring & Support'},
            {'number': '50+', 'label': 'Cities Covered'}
        ],
        'team': [
            {'name': 'John Doe', 'position': 'CEO & Founder', 'image': 'team1.jpg'},
            {'name': 'Jane Smith', 'position': 'CTO', 'image': 'team2.jpg'},
            {'name': 'Mike Johnson', 'position': 'Head of Operations', 'image': 'team3.jpg'}
        ]
    },
    'features': {
        'main_features': [
            {
                'icon': 'chart-line',
                'title': 'Real-time Monitoring',
                'description': 'Track energy consumption in real-time with detailed analytics and customizable dashboards. Get instant alerts for unusual patterns and potential issues.'
            },
            {
                'icon': 'solar-panel',
                'title': 'Renewable Integration',
                'description': 'Seamlessly integrate solar, wind, and other renewable energy sources into your energy mix. Optimize usage based on availability and cost.'
            },
            {
                'icon': 'robot',
                'title': 'AI-Powered Optimization',
                'description': 'Leverage artificial intelligence to predict energy needs and automatically adjust systems for maximum efficiency and cost savings.'
            },
            {
                'icon': 'mobile-alt',
                'title': 'Mobile Access',
                'description': 'Monitor and control your energy systems from anywhere using our mobile app. Receive notifications and make adjustments on the go.'
            },
            {
                'icon': 'shield-alt',
                'title': 'Security & Compliance',
                'description': 'Enterprise-grade security with end-to-end encryption. Stay compliant with industry regulations and standards.'
            },
            {
                'icon': 'chart-pie',
                'title': 'Advanced Analytics',
                'description': 'Deep insights into your energy usage patterns with customizable reports and predictive analytics for better decision-making.'
            }
        ],
        'benefits': [
            {
                'icon': 'check-circle',
                'title': 'Cost Reduction',
                'description': 'Significant savings through optimized energy usage and reduced waste'
            },
            {
                'icon': 'leaf',
                'title': 'Sustainability',
                'description': 'Reduce your carbon footprint and contribute to a greener future'
            },
            {
                'icon': 'clock',
                'title': 'Time Savings',
                'description': 'Automated processes and real-time monitoring save valuable time'
            },
            {
                'icon': 'chart-bar',
                'title': 'Performance Insights',
                'description': 'Data-driven decisions to improve overall energy efficiency'
            }
        ]
    }
}

# Initialize LangChain
llm = ChatOpenAI(
    temperature=0.7,
    openai_api_key=os.getenv('OPENAI_API_KEY')
)

# Weather API configuration
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
if not WEATHER_API_KEY:
    raise ValueError("OPENWEATHER_API_KEY environment variable is not set")
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5"

# Continent data structure
CONTINENTS = [
    {
        'name': 'Africa',
        'icon': 'fa-globe-africa',
        'description': 'Explore weather conditions across the diverse landscapes of Africa'
    },
    {
        'name': 'Asia',
        'icon': 'fa-globe-asia',
        'description': 'Discover weather patterns across the vast continent of Asia'
    },
    {
        'name': 'Europe',
        'icon': 'fa-globe-europe',
        'description': 'Check weather conditions throughout European countries'
    },
    {
        'name': 'North America',
        'icon': 'fa-globe-americas',
        'description': 'View weather information for North American regions'
    },
    {
        'name': 'South America',
        'icon': 'fa-globe-americas',
        'description': 'Explore weather patterns across South American countries'
    },
    {
        'name': 'Oceania',
        'icon': 'fa-globe-oceania',
        'description': 'Check weather conditions in Oceania and Pacific islands'
    },
    {
        'name': 'Antarctica',
        'icon': 'fa-snowflake',
        'description': 'View weather information for Antarctic regions'
    }
]

def load_data():
    """Load data from JSON files"""
    global data
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        # Load users
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                data['users'] = json.load(f)
        else:
            # Create default users if users file doesn't exist
            default_users = [
                {
                    'id': 1,
                    'username': 'admin',
                    'password': generate_password_hash('admin'),
                    'role': 'admin',
                    'locations': ['Building A', 'Building B', 'Building C']
                },
                {
                    'id': 2,
                    'username': 'staff1',
                    'password': generate_password_hash('staff1'),
                    'role': 'staff',
                    'power_pack_id': 'PP001',
                    'locations': ['Building A']
                },
                {
                    'id': 3,
                    'username': 'staff2',
                    'password': generate_password_hash('staff2'),
                    'role': 'staff',
                    'power_pack_id': 'PP002',
                    'locations': ['Building B']
                }
            ]
            data['users'] = default_users
            with open(USERS_FILE, 'w') as f:
                json.dump(default_users, f)

        # Load locations
        if os.path.exists(LOCATIONS_FILE):
            with open(LOCATIONS_FILE, 'r') as f:
                data['locations'] = json.load(f)
        else:
            # Initialize with default locations
            default_locations = [
                {
                    'id': 'Building A',
                    'name': 'Building A',
                    'address': '123 Main St',
                    'power_capacity': 10000,  # in watts
                    'devices': ['PP001', 'INV001', 'INV002']
                },
                {
                    'id': 'Building B',
                    'name': 'Building B',
                    'address': '456 Oak Ave',
                    'power_capacity': 15000,  # in watts
                    'devices': ['PP002', 'INV003', 'INV004']
                },
                {
                    'id': 'Building C',
                    'name': 'Building C',
                    'address': '789 Pine Rd',
                    'power_capacity': 20000,  # in watts
                    'devices': ['PP003', 'INV005', 'INV006']
                }
            ]
            data['locations'] = default_locations
            with open(LOCATIONS_FILE, 'w') as f:
                json.dump(default_locations, f)

        # Load consumptions with mock data if empty
        if os.path.exists(CONSUMPTIONS_FILE):
            with open(CONSUMPTIONS_FILE, 'r') as f:
                data['consumptions'] = json.load(f)
        else:
            mock_consumptions = generate_mock_data()
            data['consumptions'] = mock_consumptions
            with open(CONSUMPTIONS_FILE, 'w') as f:
                json.dump(mock_consumptions, f)

        # Load controls
        if os.path.exists(CONTROLS_FILE):
            with open(CONTROLS_FILE, 'r') as f:
                data['controls'] = json.load(f)
        else:
            default_controls = []
            with open(CONTROLS_FILE, 'w') as f:
                json.dump(default_controls, f)

        # Load about data
        if os.path.exists(ABOUT_FILE):
            with open(ABOUT_FILE, 'r') as f:
                data['about'] = json.load(f)
        else:
            # Use default about data from initialization
            with open(ABOUT_FILE, 'w') as f:
                json.dump(data['about'], f)

        # Load features data
        if os.path.exists(FEATURES_FILE):
            with open(FEATURES_FILE, 'r') as f:
                data['features'] = json.load(f)
        else:
            # Use default features data from initialization
            with open(FEATURES_FILE, 'w') as f:
                json.dump(data['features'], f)

    except Exception as e:
        print(f"Error loading data: {e}")
        # Keep the default data structures in case of error
        data = {
            'users': [],
            'consumptions': [],
            'controls': [],
            'locations': [],
            'about': data['about'],  # Keep default about data
            'features': data['features']  # Keep default features data
        }

def generate_mock_data():
    """Generate mock consumption data for the last 24 hours"""
    mock_data = []
    now = datetime.now()
    locations = ['Building A', 'Building B', 'Building C']
    devices = {
        'Building A': ['PP001', 'INV001', 'INV002'],
        'Building B': ['PP002', 'INV003', 'INV004'],
        'Building C': ['PP003', 'INV005', 'INV006']
    }
    
    for i in range(24):
        time = now - timedelta(hours=i)
        for location in locations:
            for device in devices[location]:
                mock_data.append({
                    'timestamp': time.isoformat(),
                    'value': 50 + (i % 10) * 5,  # Random-like values between 50-100
                    'consumption': 45 + (i % 8) * 4,  # Random-like consumption
                    'location': location,
                    'device_id': device,
                    'device_type': 'power_pack' if device.startswith('PP') else 'inverter'
                })
    
    return mock_data

def save_data():
    """Save data to JSON files"""
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        with open(USERS_FILE, 'w') as f:
            json.dump(data['users'], f)
        with open(CONSUMPTIONS_FILE, 'w') as f:
            json.dump(data['consumptions'], f)
        with open(CONTROLS_FILE, 'w') as f:
            json.dump(data['controls'], f)
    except Exception as e:
        print(f"Error saving data: {e}")
        return False
    return True

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def landing():
    """Render the landing page"""
    return render_template('landing.html')

@app.route('/about')
def about():
    """Render the about page"""
    return render_template('about.html')

@app.route('/features')
def features():
    """Render the features page"""
    return render_template('features.html')

@app.route('/test-logo')
def test_logo():
    """Test route to verify logo file access"""
    try:
        with open('static/images/gocity.png', 'rb') as f:
            return send_file(f, mimetype='image/png')
    except Exception as e:
        return str(e), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user
        user = next((user for user in data['users'] 
                    if user['username'] == username), None)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard page"""
    return render_template('dashboard.html', 
                         username=session.get('username'),
                         role=session.get('role'))

def get_user_data(user_id):
    """Get data specific to a user based on their role"""
    user = next((u for u in data['users'] if u['id'] == user_id), None)
    if not user:
        return None
        
    if user['role'] == 'admin':
        # Admins see all data
        workspace_data = {
            'consumptions': [c for c in data['consumptions'] if not c['device_id'].startswith('PP')],
            'controls': [c for c in data['controls'] if not c['device_id'].startswith('PP')],
            'locations': data['locations']
        }
        
        portable_data = {
            'consumptions': [c for c in data['consumptions'] if c['device_id'].startswith('PP')],
            'controls': [c for c in data['controls'] if c['device_id'].startswith('PP')],
            'locations': data['locations']
        }
        
        return {
            'workspace_data': workspace_data,
            'portable_data': portable_data,
            'all_consumptions': data['consumptions'],
            'all_controls': data['controls'],
            'all_locations': data['locations'],
            'view_mode': session.get('admin_view_mode', 'workspace')  # Default to workspace view
        }
    else:
        # Staff see only their power pack data
        power_pack_id = user.get('power_pack_id')
        user_locations = user.get('locations', [])
        
        return {
            'consumptions': [
                c for c in data['consumptions']
                if (c['device_id'] == power_pack_id or c['location'] in user_locations)
            ],
            'controls': [
                c for c in data['controls']
                if c['user_id'] == user_id
            ],
            'locations': [
                l for l in data['locations']
                if l['id'] in user_locations
            ]
        }

@app.route('/api/real-time-data')
@login_required
def get_real_time_data():
    """Get real-time energy consumption data"""
    try:
        user_data = get_user_data(session['user_id'])
        if not user_data:
            return jsonify({'error': 'User not found'}), 404

        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        recent_consumptions = [
            c for c in user_data['consumptions']
            if datetime.fromisoformat(c['timestamp']) > yesterday
        ]
        
        active_controls = [
            c for c in user_data['controls']
            if c.get('status') == 'active'
        ]
        
        # Calculate metrics
        current_power = sum(c.get('value', 0) for c in recent_consumptions[-3:]) / 3 if recent_consumptions else 0
        daily_consumption = sum(c.get('consumption', 0) for c in recent_consumptions)
        active_locations = len(set(c.get('location') for c in recent_consumptions))
        total_runtime = len(set(c['timestamp'].split('T')[0] for c in recent_consumptions))
        
        return jsonify({
            'consumptions': recent_consumptions,
            'controls': active_controls,
            'locations': user_data['locations'],
            'current_power': round(current_power, 2),
            'total_runtime': total_runtime,
            'daily_consumption': round(daily_consumption, 2),
            'active_locations': active_locations,
            'role': session.get('role')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<format>')
@login_required
def download_data(format):
    """Download data in various formats"""
    try:
        # Get the last 24 hours of consumption data
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        recent_consumptions = [
            c for c in data['consumptions']
            if datetime.fromisoformat(c['timestamp']) > yesterday
        ] if data['consumptions'] else []

        if format == 'csv':
            df = pd.DataFrame(recent_consumptions)
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'energy_data_{now.strftime("%Y%m%d")}.csv'
            )
            
        elif format == 'excel':
            df = pd.DataFrame(recent_consumptions)
            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'energy_data_{now.strftime("%Y%m%d")}.xlsx'
            )
            
        elif format == 'json':
            return jsonify({
                'consumptions': recent_consumptions,
                'timestamp': now.isoformat(),
                'metrics': {
                    'current_power': sum(c.get('value', 0) for c in recent_consumptions[-3:]) / 3 if recent_consumptions else 0,
                    'daily_consumption': sum(c.get('consumption', 0) for c in recent_consumptions),
                    'active_locations': len(set(c.get('location') for c in recent_consumptions))
                }
            })
            
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-consumption', methods=['POST'])
@login_required
def add_consumption():
    """Add new consumption data"""
    if not request.is_json:
        return jsonify({'error': 'Content type must be application/json'}), 400
    
    try:
        consumption = request.json
        required_fields = ['value', 'consumption', 'location']
        
        # Validate required fields
        if not all(field in consumption for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Validate data types
        if not isinstance(consumption['value'], (int, float)):
            return jsonify({'error': 'Value must be a number'}), 400
        if not isinstance(consumption['consumption'], (int, float)):
            return jsonify({'error': 'Consumption must be a number'}), 400
        if not isinstance(consumption['location'], str):
            return jsonify({'error': 'Location must be a string'}), 400
            
        consumption['timestamp'] = datetime.now().isoformat()
        consumption['user_id'] = session['user_id']
        
        data['consumptions'].append(consumption)
        if save_data():
            return jsonify({'status': 'success', 'data': consumption})
        else:
            return jsonify({'error': 'Failed to save data'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/set-control', methods=['POST'])
@login_required
def set_control():
    """Set energy control parameters"""
    if not request.is_json:
        return jsonify({'error': 'Content type must be application/json'}), 400
    
    try:
        control = request.json
        required_fields = ['mode', 'value', 'device_id']
        
        # Validate required fields
        if not all(field in control for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Validate mode
        if control['mode'] not in ['time', 'wattage']:
            return jsonify({'error': 'Invalid mode'}), 400
            
        # Validate value based on mode
        if control['mode'] == 'time':
            hours = float(control.get('hours', 0))
            minutes = float(control.get('minutes', 0))
            seconds = float(control.get('seconds', 0))
            total_hours = hours + (minutes / 60) + (seconds / 3600)
            
            if not 0 <= total_hours <= 24:
                return jsonify({'error': 'Total time must be between 0 and 24 hours'}), 400
                
            control['value'] = total_hours
            
        elif control['mode'] == 'wattage':
            if not 0 <= float(control['value']):
                return jsonify({'error': 'Wattage must be positive'}), 400
            
        # Verify user has access to the device
        user = next((u for u in data['users'] if u['id'] == session['user_id']), None)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if user['role'] != 'admin':
            # Staff can only control their assigned power pack
            if control['device_id'] != user.get('power_pack_id'):
                return jsonify({'error': 'Unauthorized to control this device'}), 403
            
        control['timestamp'] = datetime.now().isoformat()
        control['user_id'] = session['user_id']
        control['status'] = 'active'
        
        # Deactivate any existing controls for this device
        for existing_control in data['controls']:
            if existing_control['device_id'] == control['device_id']:
                existing_control['status'] = 'inactive'
        
        data['controls'].append(control)
        if save_data():
            return jsonify({'status': 'success', 'data': control})
        else:
            return jsonify({'error': 'Failed to save data'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/remove-control/<int:control_id>', methods=['DELETE'])
@login_required
def remove_control(control_id):
    """Remove a control setting"""
    try:
        # Find and remove the control
        control = next((c for c in data['controls'] if c.get('id') == control_id), None)
        
        if control and (session.get('role') == 'admin' or control.get('user_id') == session.get('user_id')):
            data['controls'] = [c for c in data['controls'] if c.get('id') != control_id]
            if save_data():
                return jsonify({'status': 'success'})
            else:
                return jsonify({'error': 'Failed to save data'}), 500
        
        return jsonify({'error': 'Control not found or unauthorized'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    return redirect(url_for('landing'))

@app.route('/api/set-theme', methods=['POST'])
def set_theme():
    """Set user theme preference"""
    if not request.is_json:
        return jsonify({'error': 'Content type must be application/json'}), 400
    
    theme = request.json.get('theme')
    if theme not in ['light', 'dark', 'system']:
        return jsonify({'error': 'Invalid theme value'}), 400
    
    session['theme'] = theme
    return jsonify({'status': 'success', 'theme': theme})

@app.route('/api/get-theme')
def get_theme():
    """Get user theme preference"""
    return jsonify({'theme': session.get('theme', 'system')})

@app.route('/api/set-admin-view', methods=['POST'])
@login_required
def set_admin_view():
    """Set admin view mode (workspace/portable)"""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    if not request.is_json:
        return jsonify({'error': 'Content type must be application/json'}), 400
        
    view_mode = request.json.get('view_mode')
    if view_mode not in ['workspace', 'portable']:
        return jsonify({'error': 'Invalid view mode'}), 400
        
    session['admin_view_mode'] = view_mode
    return jsonify({'status': 'success', 'view_mode': view_mode})

@app.route('/api/about')
def get_about_data():
    """API endpoint to get about page data"""
    about_data = {
        'mission': "To revolutionize energy management by providing innovative, sustainable solutions that optimize energy consumption, reduce costs, and minimize environmental impact for businesses and communities across Nigeria.",
        'vision': "To become the leading energy management platform in Africa, driving the transition to sustainable energy practices and creating a greener future for generations to come.",
        'stats': [
            {'number': '100+', 'label': 'Businesses Served'},
            {'number': '30%', 'label': 'Average Energy Savings'},
            {'number': '24/7', 'label': 'Monitoring & Support'},
            {'number': '50+', 'label': 'Cities Covered'}
        ],
        'team': [
            {'name': 'John Doe', 'position': 'CEO & Founder', 'image': 'team1.jpg'},
            {'name': 'Jane Smith', 'position': 'CTO', 'image': 'team2.jpg'},
            {'name': 'Mike Johnson', 'position': 'Head of Operations', 'image': 'team3.jpg'}
        ]
    }
    return jsonify(about_data)

@app.route('/api/features')
def get_features_data():
    """API endpoint to get features page data"""
    features_data = {
        'main_features': [
            {
                'icon': 'chart-line',
                'title': 'Real-time Monitoring',
                'description': 'Track energy consumption in real-time with detailed analytics and customizable dashboards. Get instant alerts for unusual patterns and potential issues.'
            },
            {
                'icon': 'solar-panel',
                'title': 'Renewable Integration',
                'description': 'Seamlessly integrate solar, wind, and other renewable energy sources into your energy mix. Optimize usage based on availability and cost.'
            },
            {
                'icon': 'robot',
                'title': 'AI-Powered Optimization',
                'description': 'Leverage artificial intelligence to predict energy needs and automatically adjust systems for maximum efficiency and cost savings.'
            },
            {
                'icon': 'mobile-alt',
                'title': 'Mobile Access',
                'description': 'Monitor and control your energy systems from anywhere using our mobile app. Receive notifications and make adjustments on the go.'
            },
            {
                'icon': 'shield-alt',
                'title': 'Security & Compliance',
                'description': 'Enterprise-grade security with end-to-end encryption. Stay compliant with industry regulations and standards.'
            },
            {
                'icon': 'chart-pie',
                'title': 'Advanced Analytics',
                'description': 'Deep insights into your energy usage patterns with customizable reports and predictive analytics for better decision-making.'
            }
        ],
        'benefits': [
            {
                'icon': 'check-circle',
                'title': 'Cost Reduction',
                'description': 'Significant savings through optimized energy usage and reduced waste'
            },
            {
                'icon': 'leaf',
                'title': 'Sustainability',
                'description': 'Reduce your carbon footprint and contribute to a greener future'
            },
            {
                'icon': 'clock',
                'title': 'Time Savings',
                'description': 'Automated processes and real-time monitoring save valuable time'
            },
            {
                'icon': 'chart-bar',
                'title': 'Performance Insights',
                'description': 'Data-driven decisions to improve overall energy efficiency'
            }
        ]
    }
    return jsonify(features_data)

@app.route('/api/countries')
def get_countries():
    """Get list of all countries"""
    try:
        countries = [
            {
                'name': country.name,
                'code': country.alpha_2,
                'currency': getattr(country, 'currency', None),
                'flag': f"https://flagcdn.com/w40/{country.alpha_2.lower()}.png"
            }
            for country in pycountry.countries
        ]
        return jsonify(sorted(countries, key=lambda x: x['name']))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/timezones')
def get_timezones():
    try:
        timezones = []
        for country in pycountry.countries:
            try:
                # Get continent information
                continent = pycountry.countries.get(alpha_2=country.alpha_2).continent
                if not continent:
                    continent = "Other"
                
                # Get time zones for the country
                country_tz = pycountry.countries.get(alpha_2=country.alpha_2).timezones
                for tz_name in country_tz:
                    tz = pytz.timezone(tz_name)
                    offset = tz.utcoffset(datetime.now())
                    offset_hours = offset.total_seconds() / 3600
                    offset_str = f"UTC{offset_hours:+03.0f}:00"
                    
                    timezones.append({
                        'value': tz_name,
                        'label': f"{country.name} - {tz_name}",
                        'countryCode': country.alpha_2,
                        'countryName': country.name,
                        'continent': continent,
                        'offset': offset_str
                    })
            except Exception as e:
                print(f"Error processing country {country.name}: {str(e)}")
                continue
        
        # Sort timezones by continent and country name
        timezones.sort(key=lambda x: (x['continent'], x['countryName']))
        return jsonify(timezones)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/weather')
def weather():
    continents = [
        {'name': 'North America', 'code': 'NA'},
        {'name': 'South America', 'code': 'SA'},
        {'name': 'Europe', 'code': 'EU'},
        {'name': 'Africa', 'code': 'AF'},
        {'name': 'Asia', 'code': 'AS'},
        {'name': 'Oceania', 'code': 'OC'}
    ]
    return render_template('weather.html', continents=continents)

@app.route('/api/countries/<continent>')
def api_countries(continent):
    """API endpoint to get countries for a continent."""
    countries = get_countries(continent)
    return jsonify(countries)

@app.route('/api/states/<continent>/<country_code>')
def api_states(continent, country_code):
    """API endpoint to get states for a country"""
    try:
        # Get country subdivisions using pycountry
        subdivisions = pycountry.subdivisions.get(country_code=country_code)
        
        if not subdivisions:
            # If no subdivisions found, try to get states from the JSON file as fallback
            try:
                with open('data/states.json', 'r') as f:
                    states_data = json.load(f)
                country_states = states_data.get(country_code, [])
                return jsonify(country_states)
            except Exception:
                return jsonify([])
        
        # Format subdivisions data
        formatted_states = []
        for subdivision in subdivisions:
            formatted_states.append({
                'name': subdivision.name,
                'code': subdivision.code.split('-')[1]  # Remove country code prefix
            })
        
        # Sort states by name
        formatted_states.sort(key=lambda x: x['name'])
        return jsonify(formatted_states)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cities/<continent>/<country_code>/<state_code>')
def get_cities(continent, country_code, state_code):
    """API endpoint to get cities for a state"""
    try:
        # Try to get cities from the JSON file first
        try:
            with open('data/cities.json', 'r') as f:
                cities_data = json.load(f)
            country_cities = cities_data.get(country_code, {})
            state_cities = country_cities.get(state_code, [])
            if state_cities:
                return jsonify(state_cities)
        except Exception:
            pass

        # If no cities found in JSON, use a fallback list of major cities
        major_cities = {
            'US': {
                'AL': ['Birmingham', 'Montgomery', 'Mobile', 'Huntsville', 'Tuscaloosa', 'Auburn'],
                'AK': ['Anchorage', 'Fairbanks', 'Juneau', 'Wasilla', 'Sitka', 'Kodiak'],
                'AZ': ['Phoenix', 'Tucson', 'Mesa', 'Scottsdale', 'Glendale', 'Tempe', 'Chandler'],
                'CA': ['Los Angeles', 'San Francisco', 'San Diego', 'Sacramento', 'San Jose', 'Fresno', 'Long Beach', 'Oakland'],
                'CO': ['Denver', 'Colorado Springs', 'Aurora', 'Fort Collins', 'Lakewood', 'Thornton'],
                'CT': ['Bridgeport', 'New Haven', 'Hartford', 'Stamford', 'Waterbury', 'Norwalk'],
                'FL': ['Miami', 'Orlando', 'Tampa', 'Jacksonville', 'St. Petersburg', 'Hialeah', 'Fort Lauderdale', 'Tallahassee'],
                'GA': ['Atlanta', 'Augusta', 'Columbus', 'Macon', 'Savannah', 'Athens'],
                'IL': ['Chicago', 'Aurora', 'Rockford', 'Joliet', 'Naperville', 'Springfield'],
                'IN': ['Indianapolis', 'Fort Wayne', 'Evansville', 'South Bend', 'Carmel', 'Bloomington'],
                'MA': ['Boston', 'Worcester', 'Springfield', 'Cambridge', 'Lowell', 'Brockton'],
                'MI': ['Detroit', 'Grand Rapids', 'Warren', 'Sterling Heights', 'Lansing', 'Ann Arbor'],
                'MN': ['Minneapolis', 'St. Paul', 'Rochester', 'Duluth', 'Bloomington', 'Brooklyn Park'],
                'NY': ['New York City', 'Buffalo', 'Rochester', 'Syracuse', 'Yonkers', 'Albany'],
                'OH': ['Columbus', 'Cleveland', 'Cincinnati', 'Toledo', 'Akron', 'Dayton'],
                'PA': ['Philadelphia', 'Pittsburgh', 'Allentown', 'Erie', 'Reading', 'Scranton'],
                'TX': ['Houston', 'Dallas', 'Austin', 'San Antonio', 'Fort Worth', 'El Paso', 'Arlington', 'Corpus Christi'],
                'WA': ['Seattle', 'Spokane', 'Tacoma', 'Vancouver', 'Bellevue', 'Kent']
            },
            'CA': {
                'ON': ['Toronto', 'Ottawa', 'Hamilton', 'London', 'Windsor', 'Kitchener', 'Mississauga', 'Brampton'],
                'BC': ['Vancouver', 'Victoria', 'Surrey', 'Burnaby', 'Richmond', 'Abbotsford', 'Coquitlam'],
                'AB': ['Calgary', 'Edmonton', 'Red Deer', 'Lethbridge', 'St. Albert', 'Medicine Hat'],
                'QC': ['Montreal', 'Quebec City', 'Laval', 'Gatineau', 'Longueuil', 'Sherbrooke'],
                'NS': ['Halifax', 'Sydney', 'Truro', 'New Glasgow', 'Glace Bay', 'Kentville']
            },
            'GB': {
                'ENG': ['London', 'Manchester', 'Birmingham', 'Liverpool', 'Leeds', 'Sheffield', 'Bristol', 'Newcastle'],
                'SCT': ['Edinburgh', 'Glasgow', 'Aberdeen', 'Dundee', 'Inverness', 'Perth'],
                'WLS': ['Cardiff', 'Swansea', 'Newport', 'Bangor', 'St. Davids', 'St. Asaph'],
                'NIR': ['Belfast', 'Derry', 'Lisburn', 'Newry', 'Bangor', 'Craigavon']
            },
            'AU': {
                'NSW': ['Sydney', 'Newcastle', 'Wollongong', 'Maitland', 'Coffs Harbour', 'Wagga Wagga'],
                'VIC': ['Melbourne', 'Geelong', 'Ballarat', 'Bendigo', 'Shepparton', 'Melton'],
                'QLD': ['Brisbane', 'Gold Coast', 'Sunshine Coast', 'Townsville', 'Cairns', 'Toowoomba'],
                'WA': ['Perth', 'Bunbury', 'Geraldton', 'Albany', 'Kalgoorlie', 'Broome'],
                'SA': ['Adelaide', 'Mount Gambier', 'Whyalla', 'Murray Bridge', 'Port Augusta', 'Port Pirie']
            },
            'IN': {
                'MH': ['Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik', 'Aurangabad'],
                'KA': ['Bangalore', 'Mysore', 'Hubli', 'Mangalore', 'Belgaum', 'Gulbarga'],
                'TN': ['Chennai', 'Coimbatore', 'Madurai', 'Salem', 'Tiruchirappalli', 'Tirunelveli'],
                'GJ': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar', 'Jamnagar'],
                'DL': ['New Delhi', 'Delhi Cantonment', 'New Delhi Cantonment']
            },
            'CN': {
                'BJ': ['Beijing', 'Tongzhou', 'Changping', 'Daxing', 'Fangshan', 'Mentougou'],
                'SH': ['Shanghai', 'Pudong', 'Huangpu', 'Xuhui', 'Changning', 'Jing\'an'],
                'GD': ['Guangzhou', 'Shenzhen', 'Dongguan', 'Foshan', 'Zhuhai', 'Shantou'],
                'JS': ['Nanjing', 'Suzhou', 'Wuxi', 'Changzhou', 'Nantong', 'Yangzhou'],
                'ZJ': ['Hangzhou', 'Ningbo', 'Wenzhou', 'Shaoxing', 'Jinhua', 'Huzhou']
            },
            'BR': {
                'SP': ['São Paulo', 'Campinas', 'Santos', 'São José dos Campos', 'Ribeirão Preto', 'Sorocaba'],
                'RJ': ['Rio de Janeiro', 'Niterói', 'São Gonçalo', 'Duque de Caxias', 'Nova Iguaçu', 'São João de Meriti'],
                'MG': ['Belo Horizonte', 'Uberlândia', 'Contagem', 'Juiz de Fora', 'Betim', 'Montes Claros'],
                'RS': ['Porto Alegre', 'Caxias do Sul', 'Pelotas', 'Canoas', 'Santa Maria', 'Novo Hamburgo'],
                'PR': ['Curitiba', 'Londrina', 'Maringá', 'Ponta Grossa', 'Cascavel', 'São José dos Pinhais']
            }
        }

        # Get cities for the specified state
        country_cities = major_cities.get(country_code, {})
        state_cities = country_cities.get(state_code, [])

        # Format cities data
        formatted_cities = []
        for city in state_cities:
            formatted_cities.append({
                'name': city,
                'code': city.lower().replace(' ', '_')
            })

        return jsonify(formatted_cities)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/select-continent')
def select_continent():
    return render_template('continent_selection.html', continents=CONTINENTS)

@app.route('/weather/<continent>')
def continent_weather(continent):
    # Get countries for the selected continent
    countries = get_countries(continent)
    return render_template('weather.html', continent=continent, countries=countries)

@app.route('/api/weather/<continent>/<country_code>/<city_name>')
def get_weather(continent, country_code, city_name):
    """API endpoint to get weather data for a city"""
    try:
        # Make API request to get weather data
        current_weather_url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': f"{city_name},{country_code}",
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(current_weather_url, params=params)
        current_data = response.json()

        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch weather data'}), 400

        # Get 5-day forecast
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast"
        forecast_response = requests.get(forecast_url, params=params)
        forecast_data = forecast_response.json()

        if forecast_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch forecast data'}), 400

        # Process current weather data
        current_weather = {
            'temperature': round(current_data['main']['temp']),
            'condition': current_data['weather'][0]['main'],
            'humidity': current_data['main']['humidity'],
            'wind_speed': round(current_data['wind']['speed'] * 3.6)  # Convert m/s to km/h
        }

        # Process forecast data
        forecast = []
        current_date = None
        daily_forecast = {'high': -float('inf'), 'low': float('inf'), 'conditions': set()}
        
        for item in forecast_data['list']:
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            
            if current_date and date != current_date:
                forecast.append({
                    'date': datetime.strptime(current_date, '%Y-%m-%d').strftime('%A'),
                    'high': round(daily_forecast['high']),
                    'low': round(daily_forecast['low']),
                    'condition': max(daily_forecast['conditions'], key=daily_forecast['conditions'].count)
                })
                daily_forecast = {'high': -float('inf'), 'low': float('inf'), 'conditions': set()}
            
            current_date = date
            daily_forecast['high'] = max(daily_forecast['high'], item['main']['temp_max'])
            daily_forecast['low'] = min(daily_forecast['low'], item['main']['temp_min'])
            daily_forecast['conditions'].add(item['weather'][0]['main'])
        
        # Add the last day
        if current_date:
            forecast.append({
                'date': datetime.strptime(current_date, '%Y-%m-%d').strftime('%A'),
                'high': round(daily_forecast['high']),
                'low': round(daily_forecast['low']),
                'condition': max(daily_forecast['conditions'], key=daily_forecast['conditions'].count)
            })
        
        return jsonify({
            'current': current_weather,
            'forecast': forecast[:5]  # Return only 5 days
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather/custom/<city_name>')
def get_custom_city_weather(city_name):
    """API endpoint to get weather data for a custom city"""
    try:
        country_code = request.args.get('country')
        
        # Check if API key is configured
        if not WEATHER_API_KEY:
            print("Error: Weather API key not configured")
            return jsonify({'error': 'Weather API key not configured. Please set OPENWEATHER_API_KEY environment variable.'}), 500

        # Make API request to get weather data for the custom city
        current_weather_url = f"{WEATHER_API_URL}/weather"
        params = {
            'q': f"{city_name},{country_code}" if country_code else city_name,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        
        print(f"Making weather API request to: {current_weather_url}")
        print(f"With parameters: {params}")
        
        current_response = requests.get(current_weather_url, params=params)
        print(f"Weather API response status: {current_response.status_code}")
        
        if current_response.status_code != 200:
            error_data = current_response.json()
            error_message = error_data.get('message', 'Unknown error')
            print(f"Weather API error: {error_message}")
            return jsonify({'error': f'Weather API error: {error_message}'}), current_response.status_code
        
        current_data = current_response.json()
        
        # Get forecast data
        forecast_url = f"{WEATHER_API_URL}/forecast"
        print(f"Making forecast API request to: {forecast_url}")
        
        forecast_response = requests.get(forecast_url, params=params)
        print(f"Forecast API response status: {forecast_response.status_code}")
        
        if forecast_response.status_code != 200:
            error_data = forecast_response.json()
            error_message = error_data.get('message', 'Unknown error')
            print(f"Forecast API error: {error_message}")
            return jsonify({'error': f'Forecast API error: {error_message}'}), forecast_response.status_code
            
        forecast_data = forecast_response.json()
        
        # Process current weather data
        try:
            current_weather = {
                'temperature': round(current_data['main']['temp']),
                'condition': current_data['weather'][0]['main'],
                'description': current_data['weather'][0]['description'],
                'humidity': current_data['main']['humidity'],
                'wind_speed': round(current_data['wind']['speed'] * 3.6),  # Convert m/s to km/h
                'pressure': current_data['main']['pressure'],
                'visibility': current_data['visibility'],
                'feels_like': round(current_data['main']['feels_like']),
                'temp_min': round(current_data['main']['temp_min']),
                'temp_max': round(current_data['main']['temp_max']),
                'clouds': current_data['clouds']['all'],
                'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%H:%M'),
                'sunset': datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%H:%M'),
                'country': current_data['sys']['country'],
                'city': current_data['name']
            }
        except KeyError as e:
            print(f"Error processing current weather data: {str(e)}")
            return jsonify({'error': 'Error processing weather data'}), 500
        
        # Process forecast data
        try:
            forecast = []
            current_date = None
            daily_forecast = {
                'high': -float('inf'),
                'low': float('inf'),
                'conditions': {},
                'descriptions': {}
            }
            
            for item in forecast_data['list']:
                date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
                
                if current_date and date != current_date:
                    # Get most common condition and description
                    most_common_condition = max(daily_forecast['conditions'].items(), key=lambda x: x[1])[0]
                    most_common_description = max(daily_forecast['descriptions'].items(), key=lambda x: x[1])[0]
                    
                    forecast.append({
                        'date': datetime.strptime(current_date, '%Y-%m-%d').strftime('%A'),
                        'high': round(daily_forecast['high']),
                        'low': round(daily_forecast['low']),
                        'condition': most_common_condition,
                        'description': most_common_description
                    })
                    daily_forecast = {
                        'high': -float('inf'),
                        'low': float('inf'),
                        'conditions': {},
                        'descriptions': {}
                    }
                
                current_date = date
                daily_forecast['high'] = max(daily_forecast['high'], item['main']['temp_max'])
                daily_forecast['low'] = min(daily_forecast['low'], item['main']['temp_min'])
                
                # Count conditions and descriptions
                condition = item['weather'][0]['main']
                description = item['weather'][0]['description']
                daily_forecast['conditions'][condition] = daily_forecast['conditions'].get(condition, 0) + 1
                daily_forecast['descriptions'][description] = daily_forecast['descriptions'].get(description, 0) + 1
            
            # Add the last day
            if current_date:
                most_common_condition = max(daily_forecast['conditions'].items(), key=lambda x: x[1])[0]
                most_common_description = max(daily_forecast['descriptions'].items(), key=lambda x: x[1])[0]
                
                forecast.append({
                    'date': datetime.strptime(current_date, '%Y-%m-%d').strftime('%A'),
                    'high': round(daily_forecast['high']),
                    'low': round(daily_forecast['low']),
                    'condition': most_common_condition,
                    'description': most_common_description
                })
        except KeyError as e:
            print(f"Error processing forecast data: {str(e)}")
            return jsonify({'error': 'Error processing forecast data'}), 500
        
        return jsonify({
            'current': current_weather,
            'forecast': forecast[:5]  # Return only 5 days
        })
    except Exception as e:
        print(f"Weather API error: {str(e)}")
        return jsonify({'error': f'Failed to fetch weather data: {str(e)}'}), 500

def get_countries(continent=None):
    """Get list of countries, optionally filtered by continent"""
    try:
        # Load countries data from the JSON file
        with open('data/countries.json', 'r', encoding='utf-8') as f:
            countries_data = json.load(f)

        # Filter countries by continent if specified
        if continent:
            countries_data = [country for country in countries_data if country.get('continent') == continent]

        # Format country data
        countries = []
        for country in countries_data:
            countries.append({
                'name': country['name'],
                'code': country['code'],
                'currency': country.get('currency', ''),
                'flag': f"https://flagcdn.com/w80/{country['code'].lower()}.png"
            })

        # Sort countries by name
        countries.sort(key=lambda x: x['name'])
        return countries

    except Exception as e:
        print(f"Error loading countries: {str(e)}")
        return []

@app.route('/cities/<continent>/<country_code>/<state_code>')
def show_cities(continent, country_code, state_code):
    """Show cities for a state"""
    try:
        # Get country and state names
        country = pycountry.countries.get(alpha_2=country_code)
        country_name = country.name if country else country_code
        
        # Get cities for the state
        cities = get_cities(continent, country_code, state_code)
        if isinstance(cities, tuple):  # Error response
            cities = []
            
        # Get state name from the first city's state code
        state_name = state_code
        if cities and len(cities) > 0:
            state_name = cities[0].get('state_name', state_code)
            
        return render_template('cities.html',
                             continent=continent,
                             country_code=country_code,
                             country_name=country_name,
                             state_code=state_code,
                             state_name=state_name,
                             cities=cities)
    except Exception as e:
        flash(str(e))
        return redirect(url_for('weather'))

@app.route('/weather/<continent>/<country_code>/<state_code>/<city_name>')
def show_city_weather(continent, country_code, state_code, city_name):
    """Show weather for a specific city"""
    try:
        # Get country and state names
        country = pycountry.countries.get(alpha_2=country_code)
        country_name = country.name if country else country_code
        
        # Get weather data
        weather_data = get_weather(continent, country_code, city_name)
        if isinstance(weather_data, tuple):  # Error response
            flash(weather_data[0].get('error', 'Failed to fetch weather data'))
            return redirect(url_for('show_cities', 
                                  continent=continent,
                                  country_code=country_code,
                                  state_code=state_code))
            
        return render_template('city_weather.html',
                             continent=continent,
                             country_code=country_code,
                             country_name=country_name,
                             state_code=state_code,
                             state_name=state_code,  # You might want to get the actual state name
                             city_name=city_name,
                             weather=weather_data)
    except Exception as e:
        flash(str(e))
        return redirect(url_for('show_cities',
                              continent=continent,
                              country_code=country_code,
                              state_code=state_code))

@app.route('/states/<continent>/<country_code>')
def show_states(continent, country_code):
    try:
        # Get country name
        country = pycountry.countries.get(alpha_2=country_code)
        if not country:
            return render_template('error.html', message='Country not found')
        
        # Get states for the country
        states = []
        subdivisions = pycountry.subdivisions.get(country_code=country_code)
        if subdivisions:
            states = [{'name': sub.name, 'code': sub.code.split('-')[1]} for sub in subdivisions]
        else:
            # Fallback to states.json if no subdivisions found
            with open('data/states.json', 'r') as f:
                states_data = json.load(f)
                country_states = states_data.get(country_code, [])
                states = [{'name': state['name'], 'code': state['code']} for state in country_states]
        
        # Sort states by name
        states.sort(key=lambda x: x['name'])
        
        return render_template('states.html', 
                             continent=continent,
                             country_code=country_code,
                             country_name=country.name,
                             states=states)
    except Exception as e:
        return render_template('error.html', message=str(e))

@app.route('/api/search-cities')
def search_cities():
    """API endpoint to search for cities"""
    try:
        query = request.args.get('q', '').strip().lower()
        if not query:
            return jsonify({'cities': []})

        # First try to get cities from the JSON file
        cities = []
        try:
            with open('data/cities.json', 'r') as f:
                cities_data = json.load(f)
                
            # Search through all countries and states
            for country_code, country_cities in cities_data.items():
                country = pycountry.countries.get(alpha_2=country_code)
                if not country:
                    continue

                for state_code, state_cities in country_cities.items():
                    for city in state_cities:
                        if query in city['name'].lower():
                            cities.append({
                                'name': city['name'],
                                'country_code': country_code,
                                'country_name': country.name,
                                'state_code': state_code
                            })
        except Exception as e:
            print(f"Error reading cities.json: {str(e)}")

        # If no cities found in JSON, use the fallback list
        if not cities:
            # Use the major cities list from get_cities function
            major_cities = {
                'US': {
                    'AL': ['Birmingham', 'Montgomery', 'Mobile', 'Huntsville', 'Tuscaloosa', 'Auburn'],
                    'AK': ['Anchorage', 'Fairbanks', 'Juneau', 'Wasilla', 'Sitka', 'Kodiak'],
                    'AZ': ['Phoenix', 'Tucson', 'Mesa', 'Scottsdale', 'Glendale', 'Tempe', 'Chandler'],
                    'CA': ['Los Angeles', 'San Francisco', 'San Diego', 'Sacramento', 'San Jose', 'Fresno', 'Long Beach', 'Oakland'],
                    'CO': ['Denver', 'Colorado Springs', 'Aurora', 'Fort Collins', 'Lakewood', 'Thornton'],
                    'CT': ['Bridgeport', 'New Haven', 'Hartford', 'Stamford', 'Waterbury', 'Norwalk'],
                    'FL': ['Miami', 'Orlando', 'Tampa', 'Jacksonville', 'St. Petersburg', 'Hialeah', 'Fort Lauderdale', 'Tallahassee'],
                    'GA': ['Atlanta', 'Augusta', 'Columbus', 'Macon', 'Savannah', 'Athens'],
                    'IL': ['Chicago', 'Aurora', 'Rockford', 'Joliet', 'Naperville', 'Springfield'],
                    'IN': ['Indianapolis', 'Fort Wayne', 'Evansville', 'South Bend', 'Carmel', 'Bloomington'],
                    'MA': ['Boston', 'Worcester', 'Springfield', 'Cambridge', 'Lowell', 'Brockton'],
                    'MI': ['Detroit', 'Grand Rapids', 'Warren', 'Sterling Heights', 'Lansing', 'Ann Arbor'],
                    'MN': ['Minneapolis', 'St. Paul', 'Rochester', 'Duluth', 'Bloomington', 'Brooklyn Park'],
                    'NY': ['New York City', 'Buffalo', 'Rochester', 'Syracuse', 'Yonkers', 'Albany'],
                    'OH': ['Columbus', 'Cleveland', 'Cincinnati', 'Toledo', 'Akron', 'Dayton'],
                    'PA': ['Philadelphia', 'Pittsburgh', 'Allentown', 'Erie', 'Reading', 'Scranton'],
                    'TX': ['Houston', 'Dallas', 'Austin', 'San Antonio', 'Fort Worth', 'El Paso', 'Arlington', 'Corpus Christi'],
                    'WA': ['Seattle', 'Spokane', 'Tacoma', 'Vancouver', 'Bellevue', 'Kent']
                },
                'CA': {
                    'ON': ['Toronto', 'Ottawa', 'Hamilton', 'London', 'Windsor', 'Kitchener', 'Mississauga', 'Brampton'],
                    'BC': ['Vancouver', 'Victoria', 'Surrey', 'Burnaby', 'Richmond', 'Abbotsford', 'Coquitlam'],
                    'AB': ['Calgary', 'Edmonton', 'Red Deer', 'Lethbridge', 'St. Albert', 'Medicine Hat'],
                    'QC': ['Montreal', 'Quebec City', 'Laval', 'Gatineau', 'Longueuil', 'Sherbrooke'],
                    'NS': ['Halifax', 'Sydney', 'Truro', 'New Glasgow', 'Glace Bay', 'Kentville']
                },
                'GB': {
                    'ENG': ['London', 'Manchester', 'Birmingham', 'Liverpool', 'Leeds', 'Sheffield', 'Bristol', 'Newcastle'],
                    'SCT': ['Edinburgh', 'Glasgow', 'Aberdeen', 'Dundee', 'Inverness', 'Perth'],
                    'WLS': ['Cardiff', 'Swansea', 'Newport', 'Bangor', 'St. Davids', 'St. Asaph'],
                    'NIR': ['Belfast', 'Derry', 'Lisburn', 'Newry', 'Bangor', 'Craigavon']
                },
                'AU': {
                    'NSW': ['Sydney', 'Newcastle', 'Wollongong', 'Maitland', 'Coffs Harbour', 'Wagga Wagga'],
                    'VIC': ['Melbourne', 'Geelong', 'Ballarat', 'Bendigo', 'Shepparton', 'Melton'],
                    'QLD': ['Brisbane', 'Gold Coast', 'Sunshine Coast', 'Townsville', 'Cairns', 'Toowoomba'],
                    'WA': ['Perth', 'Bunbury', 'Geraldton', 'Albany', 'Kalgoorlie', 'Broome'],
                    'SA': ['Adelaide', 'Mount Gambier', 'Whyalla', 'Murray Bridge', 'Port Augusta', 'Port Pirie']
                },
                'IN': {
                    'MH': ['Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik', 'Aurangabad'],
                    'KA': ['Bangalore', 'Mysore', 'Hubli', 'Mangalore', 'Belgaum', 'Gulbarga'],
                    'TN': ['Chennai', 'Coimbatore', 'Madurai', 'Salem', 'Tiruchirappalli', 'Tirunelveli'],
                    'GJ': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar', 'Jamnagar'],
                    'DL': ['New Delhi', 'Delhi Cantonment', 'New Delhi Cantonment']
                },
                'CN': {
                    'BJ': ['Beijing', 'Tongzhou', 'Changping', 'Daxing', 'Fangshan', 'Mentougou'],
                    'SH': ['Shanghai', 'Pudong', 'Huangpu', 'Xuhui', 'Changning', 'Jing\'an'],
                    'GD': ['Guangzhou', 'Shenzhen', 'Dongguan', 'Foshan', 'Zhuhai', 'Shantou'],
                    'JS': ['Nanjing', 'Suzhou', 'Wuxi', 'Changzhou', 'Nantong', 'Yangzhou'],
                    'ZJ': ['Hangzhou', 'Ningbo', 'Wenzhou', 'Shaoxing', 'Jinhua', 'Huzhou']
                },
                'BR': {
                    'SP': ['São Paulo', 'Campinas', 'Santos', 'São José dos Campos', 'Ribeirão Preto', 'Sorocaba'],
                    'RJ': ['Rio de Janeiro', 'Niterói', 'São Gonçalo', 'Duque de Caxias', 'Nova Iguaçu', 'São João de Meriti'],
                    'MG': ['Belo Horizonte', 'Uberlândia', 'Contagem', 'Juiz de Fora', 'Betim', 'Montes Claros'],
                    'RS': ['Porto Alegre', 'Caxias do Sul', 'Pelotas', 'Canoas', 'Santa Maria', 'Novo Hamburgo'],
                    'PR': ['Curitiba', 'Londrina', 'Maringá', 'Ponta Grossa', 'Cascavel', 'São José dos Pinhais']
                }
            }

            # Search through major cities
            for country_code, states in major_cities.items():
                country = pycountry.countries.get(alpha_2=country_code)
                if not country:
                    continue

                for state_code, cities_list in states.items():
                    for city_name in cities_list:
                        if query in city_name.lower():
                            cities.append({
                                'name': city_name,
                                'country_code': country_code,
                                'country_name': country.name,
                                'state_code': state_code
                            })

        # Sort results by city name
        cities.sort(key=lambda x: x['name'])

        # Limit results to prevent overwhelming response
        return jsonify({'cities': cities[:10]})

    except Exception as e:
        print(f"Error searching cities: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/weather/custom/<city_name>')
def show_custom_city_weather(city_name):
    """Show weather for a custom city search"""
    try:
        country_code = request.args.get('country')
        
        # Get weather data
        if country_code:
            weather_data = get_weather('custom', country_code, city_name)
        else:
            weather_data = get_custom_city_weather(city_name)
            
        if isinstance(weather_data, tuple):  # Error response
            flash(weather_data[0].get('error', 'Failed to fetch weather data'))
            return redirect(url_for('weather'))
            
        return render_template('city_weather.html',
                             city_name=city_name,
                             weather=weather_data,
                             is_custom=True)
    except Exception as e:
        flash(str(e))
        return redirect(url_for('weather'))

# Initialize data when starting the application
load_data()

if __name__ == '__main__':
    app.run(debug=True) 