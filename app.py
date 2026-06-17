# app.py
from flask import Flask, render_template, request, jsonify, session
import json
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'restaurant_booking_secret_key_2024'

# File to store bookings
BOOKINGS_FILE = 'bookings.json'

# Restaurant configuration
RESTAURANT_NAME = "The Gourmet Table"
RESTAURANT_ADDRESS = "123 Culinary Street, Foodville, FC 12345"
RESTAURANT_PHONE = "+1 (555) 123-4567"

# Table configurations
TABLE_CONFIG = {
    'small': {'capacity': 2, 'count': 4, 'label': 'Small (2 seats)'},
    'medium': {'capacity': 4, 'count': 3, 'label': 'Medium (4 seats)'},
    'large': {'capacity': 6, 'count': 2, 'label': 'Large (6 seats)'},
    'family': {'capacity': 8, 'count': 1, 'label': 'Family (8 seats)'}
}

# Operating hours
OPERATING_HOURS = {
    'start': 11,  # 11 AM
    'end': 22,    # 10 PM
    'slots_per_hour': 4  # 15-minute intervals
}

# Sample menu items
MENU_ITEMS = [
    {'id': 1, 'name': 'Grilled Salmon', 'category': 'Main Course', 'price': 28.99, 'description': 'Fresh Atlantic salmon with lemon herb sauce'},
    {'id': 2, 'name': 'Ribeye Steak', 'category': 'Main Course', 'price': 34.99, 'description': '12oz prime ribeye with garlic butter'},
    {'id': 3, 'name': 'Truffle Pasta', 'category': 'Pasta', 'price': 22.99, 'description': 'Homemade fettuccine with black truffle'},
    {'id': 4, 'name': 'Caesar Salad', 'category': 'Appetizer', 'price': 12.99, 'description': 'Classic Caesar with homemade dressing'},
    {'id': 5, 'name': 'Tiramisu', 'category': 'Dessert', 'price': 9.99, 'description': 'Traditional Italian tiramisu with espresso'},
    {'id': 6, 'name': 'Red Wine', 'category': 'Beverage', 'price': 12.99, 'description': 'House Cabernet Sauvignon'},
    {'id': 7, 'name': 'Sparkling Water', 'category': 'Beverage', 'price': 4.99, 'description': 'Premium sparkling mineral water'}
]

# Helper functions for booking management
def load_bookings():
    """Load bookings from JSON file"""
    if os.path.exists(BOOKINGS_FILE):
        try:
            with open(BOOKINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_bookings(bookings):
    """Save bookings to JSON file"""
    with open(BOOKINGS_FILE, 'w') as f:
        json.dump(bookings, f, indent=2)

def generate_booking_id():
    """Generate a unique booking ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))
    return f"BK-{timestamp}-{random_suffix}"

def get_available_tables(date_str, time_str, party_size):
    """Get available tables for a given date, time, and party size"""
    bookings = load_bookings()
    
    # Calculate required table size based on party
    if party_size <= 2:
        required_size = 'small'
    elif party_size <= 4:
        required_size = 'medium'
    elif party_size <= 6:
        required_size = 'large'
    else:
        required_size = 'family'
    
    # Get all tables of required size and larger
    available_tables = []
    for table_type, config in TABLE_CONFIG.items():
        if config['capacity'] >= party_size:
            # Check how many of this table type are booked
            booked_count = 0
            for booking in bookings:
                if (booking['date'] == date_str and 
                    booking['time'] == time_str and 
                    booking['table_type'] == table_type):
                    booked_count += 1
            
            available_count = config['count'] - booked_count
            if available_count > 0:
                available_tables.append({
                    'type': table_type,
                    'capacity': config['capacity'],
                    'label': config['label'],
                    'available': available_count
                })
    
    return available_tables

def is_time_slot_available(date_str, time_str, table_type):
    """Check if a specific table type is available at a given time"""
    bookings = load_bookings()
    booked_count = 0
    
    for booking in bookings:
        if (booking['date'] == date_str and 
            booking['time'] == time_str and 
            booking['table_type'] == table_type):
            booked_count += 1
    
    return booked_count < TABLE_CONFIG[table_type]['count']

def create_booking(booking_data):
    """Create a new booking"""
    bookings = load_bookings()
    booking_id = generate_booking_id()
    
    # Add booking
    new_booking = {
        'id': booking_id,
        'name': booking_data['name'],
        'email': booking_data['email'],
        'phone': booking_data['phone'],
        'date': booking_data['date'],
        'time': booking_data['time'],
        'party_size': booking_data['party_size'],
        'table_type': booking_data['table_type'],
        'special_requests': booking_data.get('special_requests', ''),
        'booking_time': datetime.now().isoformat(),
        'status': 'confirmed'
    }
    
    bookings.append(new_booking)
    save_bookings(bookings)
    return booking_id

def cancel_booking(booking_id):
    """Cancel a booking"""
    bookings = load_bookings()
    for booking in bookings:
        if booking['id'] == booking_id:
            booking['status'] = 'cancelled'
            save_bookings(bookings)
            return True
    return False

def get_booking_by_id(booking_id):
    """Get a booking by ID"""
    bookings = load_bookings()
    for booking in bookings:
        if booking['id'] == booking_id:
            return booking
    return None

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', 
                         restaurant_name=RESTAURANT_NAME,
                         address=RESTAURANT_ADDRESS,
                         phone=RESTAURANT_PHONE)

@app.route('/menu')
def menu():
    """Menu page"""
    return render_template('menu.html', 
                         restaurant_name=RESTAURANT_NAME,
                         menu_items=MENU_ITEMS)

@app.route('/book')
def book():
    """Booking page"""
    return render_template('book.html',
                         restaurant_name=RESTAURANT_NAME,
                         table_config=TABLE_CONFIG,
                         operating_hours=OPERATING_HOURS)

@app.route('/api/check-availability', methods=['POST'])
def check_availability():
    """API endpoint to check table availability"""
    data = request.json
    date = data.get('date')
    time = data.get('time')
    party_size = int(data.get('party_size', 1))
    
    if not date or not time:
        return jsonify({'success': False, 'message': 'Missing date or time'})
    
    available_tables = get_available_tables(date, time, party_size)
    
    return jsonify({
        'success': True,
        'available_tables': available_tables,
        'party_size': party_size
    })

@app.route('/api/book', methods=['POST'])
def api_book():
    """API endpoint to create a booking"""
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'email', 'phone', 'date', 'time', 'party_size', 'table_type']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'})
    
    # Validate party size
    try:
        party_size = int(data['party_size'])
        if party_size < 1 or party_size > 20:
            return jsonify({'success': False, 'message': 'Party size must be between 1 and 20'})
    except:
        return jsonify({'success': False, 'message': 'Invalid party size'})
    
    # Check availability again
    available_tables = get_available_tables(data['date'], data['time'], party_size)
    table_type = data['table_type']
    
    if not any(table['type'] == table_type for table in available_tables):
        return jsonify({'success': False, 'message': 'Selected table type is not available'})
    
    # Create booking
    booking_id = create_booking(data)
    
    return jsonify({
        'success': True,
        'booking_id': booking_id,
        'message': 'Booking confirmed!'
    })

@app.route('/api/cancel/<booking_id>', methods=['POST'])
def api_cancel(booking_id):
    """API endpoint to cancel a booking"""
    if cancel_booking(booking_id):
        return jsonify({'success': True, 'message': 'Booking cancelled successfully'})
    return jsonify({'success': False, 'message': 'Booking not found'})

@app.route('/api/booking/<booking_id>', methods=['GET'])
def api_get_booking(booking_id):
    """API endpoint to get booking details"""
    booking = get_booking_by_id(booking_id)
    if booking:
        return jsonify({'success': True, 'booking': booking})
    return jsonify({'success': False, 'message': 'Booking not found'})

@app.route('/api/dates-with-bookings', methods=['GET'])
def api_dates_with_bookings():
    """API endpoint to get dates with existing bookings"""
    bookings = load_bookings()
    dates = list(set([booking['date'] for booking in bookings if booking['status'] == 'confirmed']))
    dates.sort()
    return jsonify({'success': True, 'dates': dates})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(debug=True, host='0.0.0.0', port=5000)
