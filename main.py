from src.API import Room
import json
from flask_cors import CORS
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
CORS(app)
room = Room()

SWAGGER_URL="/docs"
API_URL="/static/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Access API'
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

room.fetch_data(room.url)
for i in range(1, int(room.pageNumber) + 1):
    room.fetch_page_data(i)
room.group_data()

@app.route('/booked', methods=['GET'])
def get_booked_data():
    booked = room.groupedDataOutput
    if booked:
        return json.dumps({"bookedRoom": booked, "status": 200, "message": "Successfully retrieved the booked room."})
    else:
        return json.dumps({"bookedRoom" : {"status": 404, "message": "Booked room not found"}})

@app.route('/booked/<date>', methods=['GET'])
def get_booked_data_by_date(date):
    data_by_date = room.get_booked_data_by_date(date)
    if data_by_date:
        return json.dumps({"bookedRoom": data_by_date, "status": 200, "message": "Successfully retrieved the booked room by date."})
    else:
        return json.dumps({"bookedRoom" : {"status": 404, "message": "Booked room not found"}})

@app.route('/available', methods=['GET'])
def get_available_rooms():
    available = room.get_available_rooms()
    if available:
        return json.dumps({"roomAvailable": available, "status": 200, "message": "Successfully retrieved the available room."})
    else:
        return json.dumps({"roomAvailable": {"status": 404, "message": "Available room not found"}})

@app.route('/available/<date>', methods=['GET'])
def get_available_rooms_by_date(date):
    available_by_date = room.get_available_rooms_by_date(date)
    if available_by_date:
        return json.dumps({"roomAvailable": available_by_date, "status": 200, "message": "Successfully retrieved the available room by date."})
    else:
        return json.dumps({"roomAvailable": {"status": 404, "message": "Available room not found"}})
    
@app.route('/booking', methods=['POST'])
def booking_room():
    npm = request.json['npm']
    selected_room = request.json['room']
    date = request.json['date']
    time = request.json['time']
    message = room.booking_room(npm, selected_room, date, time)
    if message:
        return json.dumps({"status": 200, "data": message})
    else:
        return json.dumps({"status": 400, "message": "Booking room failed. Please try again."})

@app.errorhandler(404)
def page_not_found(e):
    return json.dumps({ "status" : 404, "message": "not found"}), 404

@app.errorhandler(400)
def bad_request(e):
    return json.dumps({ "status" : 400, "message": "bad request"}), 400

@app.errorhandler(500)
def internal_server_error(e):
    return json.dumps({ "status" : 500, "message": "internal server error"}), 500

if __name__ == '__main__':
    app.run()
