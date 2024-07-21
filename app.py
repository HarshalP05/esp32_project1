from flask import Flask, request, send_file, render_template
import firebase_admin
from firebase_admin import credentials, db
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import io
import os
import json

app = Flask(__name__, template_folder='public')

# Initialize Firebase Admin SDK using environment variables
cred = credentials.Certificate({
    "type": os.getenv('FIREBASE_TYPE'),
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
    "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN')
})
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
})

# Reference to your database
data_ref = db.reference('sensor_data')

# Set your data size limit (in bytes) - adjust as needed
SIZE_LIMIT_BYTES = 250 * 1024 * 1024  # 250 MB

def get_database_size():
    all_data = data_ref.get()
    if not all_data:
        return 0
    data_json = json.dumps(all_data)
    return len(data_json.encode('utf-8'))

def manage_data():
    if get_database_size() > SIZE_LIMIT_BYTES:
        all_data = data_ref.get()
        if all_data:
            sorted_data = sorted(all_data.items(), key=lambda x: x[1]['timestamp'])
            excess_entries = sorted_data[:-10000]
            
            for entry_id, _ in excess_entries:
                data_ref.child(entry_id).delete()

temperature_data = []
humidity_data = []
mq6_data = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/temperature_humidity_data', methods=['POST'])
def receive_temp_humidity_data():
    try:
        data = request.json
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_data = {'timestamp': timestamp, 'temperature': data['temperature'], 'humidity': data['humidity']}
        
        # Add new data to the database
        data_ref.push(new_data)
        
        # Manage data size
        manage_data()
        
        return "Temperature and humidity data received successfully"
    except Exception as e:
        return str(e), 500

@app.route('/mq6_data', methods=['POST'])
def receive_mq6_data():
    try:
        data = request.json
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_data = {'timestamp': timestamp, 'mq6_reading': data['mq6_reading']}
        
        # Add new data to the database
        data_ref.push(new_data)
        
        # Manage data size
        manage_data()
        
        return "MQ6 data received successfully"
    except Exception as e:
        return str(e), 500

@app.route('/plot_mq6')
def plot_mq6():
    try:
        sns.set(style="whitegrid")
        plt.figure(figsize=(10, 6))

        timestamps_mq6 = [entry['timestamp'] for entry in mq6_data]
        mq6_readings = [entry['mq6_reading'] for entry in mq6_data]

        sns.lineplot(x=timestamps_mq6, y=mq6_readings, marker='o', color='red')
        plt.title('MQ6 Sensor Data')
        plt.xlabel('Timestamp')
        plt.ylabel('MQ6 Reading')
        plt.xticks(rotation=45)
        plt.tight_layout()

        img_bytesio = io.BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()

        return send_file(img_bytesio, mimetype='image/png')
    except Exception as e:
        return str(e), 500

@app.route('/plot_aht21')
def plot_aht21():
    try:
        sns.set(style="whitegrid")
        plt.figure(figsize=(10, 12))

        timestamps_temperature = [entry['timestamp'] for entry in temperature_data]
        temperatures = [entry['temperature'] for entry in temperature_data]

        timestamps_humidity = [entry['timestamp'] for entry in humidity_data]
        humidities = [entry['humidity'] for entry in humidity_data]

        plt.subplot(2, 1, 1)
        sns.lineplot(x=timestamps_temperature, y=temperatures, marker='o', color='blue')
        plt.title('Temperature Data')
        plt.xlabel('Timestamp')
        plt.ylabel('Temperature (°C)')
        plt.xticks(rotation=45)

        plt.subplot(2, 1, 2)
        sns.lineplot(x=timestamps_humidity, y=humidities, marker='o', color='green')
        plt.title('Humidity Data')
        plt.xlabel('Timestamp')
        plt.ylabel('Humidity (%)')
        plt.xticks(rotation=45)

        plt.tight_layout()

        img_bytesio = io.BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()

        return send_file(img_bytesio, mimetype='image/png')
    except Exception as e:
        return str(e), 500

@app.route('/overall')
def overall():
    try:
        sns.set(style="whitegrid")
        plt.figure(figsize=(18, 18))

        # MQ6 Data
        timestamps_mq6 = [entry['timestamp'] for entry in mq6_data]
        mq6_readings = [entry['mq6_reading'] for entry in mq6_data]

        plt.subplot(3, 1, 1)
        sns.lineplot(x=timestamps_mq6, y=mq6_readings, marker='o', color='red')
        plt.title('MQ6 Sensor Data')
        plt.xlabel('Timestamp')
        plt.ylabel('MQ6 Reading')
        plt.xticks(rotation=45)

        # Temperature Data
        timestamps_temperature = [entry['timestamp'] for entry in temperature_data]
        temperatures = [entry['temperature'] for entry in temperature_data]

        plt.subplot(3, 1, 2)
        sns.lineplot(x=timestamps_temperature, y=temperatures, marker='o', color='blue')
        plt.title('Temperature Data')
        plt.xlabel('Timestamp')
        plt.ylabel('Temperature (°C)')
        plt.xticks(rotation=45)

        # Humidity Data
        timestamps_humidity = [entry['timestamp'] for entry in humidity_data]
        humidities = [entry['humidity'] for entry in humidity_data]

        plt.subplot(3, 1, 3)
        sns.lineplot(x=timestamps_humidity, y=humidities, marker='o', color='green')
        plt.title('Humidity Data')
        plt.xlabel('Timestamp')
        plt.ylabel('Humidity (%)')
        plt.xticks(rotation=45)

        plt.tight_layout()

        img_bytesio = io.BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()

        return send_file(img_bytesio, mimetype='image/png')
    except Exception as e:
        return str(e), 500

@app.route('/mq6')
def mq6():
    try:
        return render_template('mq6.html', mq6_data=mq6_data)
    except Exception as e:
        return str(e), 500

@app.route('/aht21')
def aht21():
    try:
        return render_template('aht21.html', temperature_data=temperature_data, humidity_data=humidity_data)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
