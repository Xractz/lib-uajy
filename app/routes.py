from app import app
from flask import request
import json
from app.tasks import Room

room = Room()

def fetch_data(room):
  room.fetch_data(room.url)
  for i in range(1, int(room.pageNumber) + 1):
    room.fetch_page_data(i)
  room.group_data()

fetch_data(room)

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
    fetch_data(room)
    available_by_date = room.get_available_rooms_by_date(date)
    if available_by_date:
      return json.dumps({"roomAvailable": available_by_date, "status": 200, "message": "Successfully retrieved the available room by date."})
    else:
      return json.dumps({"roomAvailable": {"status": 404, "message": "Available room not found"}})
    
@app.route('/booking', methods=['POST'])
def booking_room():
  data = request.json
  
  npm = data['npm']
  selected_room = data.get('room', None)
  date = data.get('date', None)
  time = data.get('time', None)

  if 'npm' not in data or not data['npm'] and 'room' not in data and 'date' not in data and 'time' not in data:
    return json.dumps({"status": 400, "message": "Missing required fields (npm, room, date, time)"}), 400
  elif not npm:
    return json.dumps({"status": 400, "message": "Required fields cannot be empty"}), 400
  

  if selected_room is None or date is None or time is None:
    message = room.booking_room(npm, "", "", "")
  else:
    message = room.booking_room(npm, selected_room, date, time)

  if message:
    return json.dumps({"status": 200, "data": message})
  else:
    return json.dumps({"status": 400, "message": "Booking room failed. Please try again."})
  
@app.errorhandler(400)
def bad_request(e):
  return json.dumps({ "status" : 400, "message": "Bad Request"}), 400

@app.errorhandler(404)
def page_not_found(e):
  return json.dumps({ "status" : 404, "message": "Not Found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
  return json.dumps({ "status" : 405, "message": "Method Not Allowed"}), 405

@app.errorhandler(500)
def internal_server_error(e):
  return json.dumps({ "status" : 500, "message": "Internal Server Error"}), 500