import json
from src.API import Room
from flask_swagger_ui import get_swaggerui_blueprint
from flask import request

class SetUp:
  def __init__(self, app):
    self.app = app
    self.room = Room()
  
  def swagger(self):
    SWAGGER_URL="/docs"
    API_URL="/static/swagger.json"
    
    swagger_ui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': 'Access API'
        }
    )

    self.app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

  def fetch_data(self, room):
    room.fetch_data(room.url)
    for i in range(1, int(room.pageNumber) + 1):
        room.fetch_page_data(i)
    room.group_data()

  def routes(self):
    self.fetch_data(self.room)

    @self.app.route('/booked', methods=['GET'])
    def get_booked_data():
        booked = self.room.groupedDataOutput
        if booked:
            return json.dumps({"bookedRoom": booked, "status": 200, "message": "Successfully retrieved the booked room."})
        else:
            return json.dumps({"bookedRoom" : {"status": 404, "message": "Booked room not found"}})

    @self.app.route('/booked/<date>', methods=['GET'])
    def get_booked_data_by_date(date):
        data_by_date = self.room.get_booked_data_by_date(date)
        if data_by_date:
            return json.dumps({"bookedRoom": data_by_date, "status": 200, "message": "Successfully retrieved the booked room by date."})
        else:
            return json.dumps({"bookedRoom" : {"status": 404, "message": "Booked room not found"}})

    @self.app.route('/available', methods=['GET'])
    def get_available_rooms():
        available = self.room.get_available_rooms()
        if available:
            return json.dumps({"roomAvailable": available, "status": 200, "message": "Successfully retrieved the available room."})
        else:
            return json.dumps({"roomAvailable": {"status": 404, "message": "Available room not found"}})

    @self.app.route('/available/<date>', methods=['GET'])
    def get_available_rooms_by_date(date):
        available_by_date = self.room.get_available_rooms_by_date(date)
        if available_by_date:
            return json.dumps({"roomAvailable": available_by_date, "status": 200, "message": "Successfully retrieved the available room by date."})
        else:
            return json.dumps({"roomAvailable": {"status": 404, "message": "Available room not found"}})
        
    @self.app.route('/booking', methods=['POST'])
    def booking_room():
        npm = request.json['npm']
        selected_room = request.json['room']
        date = request.json['date']
        time = request.json['time']
        message = self.room.booking_room(npm, selected_room, date, time)
        if message:
            return json.dumps({"status": 200, "data": message})
        else:
            return json.dumps({"status": 400, "message": "Booking room failed. Please try again."})

  def error_handler(self):
    @self.app.errorhandler(400)
    def bad_request(e):
        return json.dumps({ "status" : 400, "message": "Bad Request"}), 400
    
    @self.app.errorhandler(404)
    def page_not_found(e):
        return json.dumps({ "status" : 404, "message": "Not Found"}), 404

    @self.app.errorhandler(405)
    def method_not_allowed(e):
        return json.dumps({ "status" : 405, "message": "Method Not Allowed"}), 405

    @self.app.errorhandler(500)
    def internal_server_error(e):
        return json.dumps({ "status" : 500, "message": "Internal Server Error"}), 500

  def run(self):
    self.swagger()
    self.routes()
    self.error_handler()