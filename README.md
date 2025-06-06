# Energy Management System

A comprehensive energy management system for monitoring and controlling power consumption across multiple locations and devices.

## Features

- Real-time energy monitoring with numerical values and visualizations
- Power control with time-based and wattage-based settings
- Location-based power tracking
- Consumption history and analytics
- User authentication with admin and staff roles
- Modern, responsive interface with dark/light theme support

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd energy-management-system
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Login Credentials

- Admin:

  - Username: admin
  - Password: admin123

- Staff:
  - Username: staff1
  - Password: staff123

### Features

1. **Real-time Monitoring**

   - View current power usage
   - Monitor total runtime
   - Track daily consumption
   - See active locations

2. **Power Control**

   - Set time-based controls (hours, minutes, seconds)
   - Configure wattage limits
   - Select locations for control

3. **Data Visualization**

   - Real-time consumption charts
   - Device distribution analysis
   - Location-based power usage
   - Historical data tracking

4. **User Roles**
   - Admin: Full access to all locations and devices
   - Staff: Access to personal power pack only

## Development

The application uses:

- Flask for the backend
- Bootstrap 5 for the frontend
- Plotly for data visualization
- JSON files for data storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
#   E n e r g y M a n a g e m e n t S y s t e m  
 