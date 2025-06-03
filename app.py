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

# Add your OpenWeatherMap API key here
OPENWEATHER_API_KEY = "YOUR_API_KEY_HERE"

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
    return render_template('weather.html')

@app.route('/api/weather')
def get_weather():
    location = request.args.get('location', '')
    
    if not location:
        return jsonify({'error': 'Location parameter is required'}), 400

    try:
        # First, get coordinates from location name
        geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={OPENWEATHER_API_KEY}"
        geocode_response = requests.get(geocode_url)
        geocode_data = geocode_response.json()

        if not geocode_data:
            return jsonify({'error': 'Location not found'}), 404

        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']
        location_name = f"{geocode_data[0]['name']}, {geocode_data[0]['country']}"

        # Then, get weather data using coordinates
        weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        # Add location name to the response
        weather_data['location'] = location_name

        return jsonify(weather_data)

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to fetch weather data'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize data when starting the application
load_data()

if __name__ == '__main__':
    app.run(debug=True) 