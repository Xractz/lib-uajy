from app import app
from flask import request, jsonify
from app.tasks import Plagiarism, Room

room = Room()
plagiarism = Plagiarism()

@app.route('/booked', methods=['GET'])
def get_booked_data():
  booked = room.get_booked_data()
  if booked:
    return jsonify({"bookedRoom": booked, "status": 200, "message": "Successfully retrieved the booked room."}), 200
  else:
    return jsonify({"bookedRoom" : {"status": 404, "message": "Booked room not found"}})

@app.route('/booked/<date>', methods=['GET'])
def get_booked_data_by_date(date):
  data_by_date = room.get_booked_data_by_date(date)
  if data_by_date:
    return jsonify({"bookedRoom": data_by_date, "status": 200, "message": "Successfully retrieved the booked room by date."}), 200
  else:
    return jsonify({"bookedRoom" : {"status": 404, "message": "Booked room not found"}})

@app.route('/available', methods=['GET'])
def get_available_rooms():
  available = room.get_available_rooms()
  if available:
    return jsonify({"roomAvailable": available, "status": 200, "message": "Successfully retrieved the available room."}), 200
  else:
    return jsonify({"roomAvailable": {"status": 404, "message": "Available room not found"}})

@app.route('/available/<date>', methods=['GET'])
def get_available_rooms_by_date(date):
    available_by_date = room.get_available_rooms_by_date(date)
    if available_by_date:
      return jsonify({"roomAvailable": available_by_date, "status": 200, "message": "Successfully retrieved the available room by date."}), 200
    else:
      return jsonify({"roomAvailable": {"status": 404, "message": "Available room not found"}})
    
@app.route('/booking', methods=['POST'])
def booking_room():
  data = request.json
  
  npm = data['npm']
  selected_room = data.get('room', None)
  date = data.get('date', None)
  time = data.get('time', None)

  if 'npm' not in data or not data['npm'] and 'room' not in data and 'date' not in data and 'time' not in data:
    return jsonify({"status": 400, "message": "Missing required fields (npm, room, date, time)"}), 400
  elif not npm:
    return jsonify({"status": 400, "message": "Required fields cannot be empty"}), 400
  

  if selected_room is None or date is None or time is None:
    message = room.booking_room(npm, "", "", "")
  else:
    message = room.booking_room(npm, selected_room, date, time)

  if message:
    return jsonify({"status": 200, "data": message}), 200
  else:
    return jsonify({"status": 400, "message": "Booking room failed. Please try again."}), 400

@app.route('/student', methods=['POST'])
def student():
  data = request.json
  npm = data.get('npm', None)
  
  if len(data) > 1 or not npm:
    return jsonify({"status": 400, "message": "Key must be 'npm'"}), 400
  elif len(npm) == 0:
    return jsonify({"status": 400, "message": "Error no npm found"}), 400
  
  message = plagiarism.get_information(npm)
  if message:
    return jsonify({"status": 200, "dataStudent": message}), 200
  else:
    return jsonify({"status": 400, "dataStudent": "Not Found"}), 400

@app.route('/turnitin', methods=['POST'])
def turnitin():
  if 'file' not in request.files:
    return jsonify({'error': 'No file part in request', 'status': 400}), 400

  file = request.files['file']
  mimetype = file.mimetype
  allowed_extensions = ['pdf', 'docx', 'doc']

  form = request.form
  npm = form.get('npm', None)
  title = form.get('title', None)
  content_file = file.read()

  if not npm or not title:
    return jsonify({'error': 'NPM or title field is missing or None', 'status': 400}), 400
  elif not file.filename:
    return jsonify({'error': 'No selected file', 'status': 400}), 400
  elif file.filename.split('.')[-1].lower() not in allowed_extensions or mimetype != 'application/pdf' and mimetype != 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' and mimetype != 'application/msword':
    return jsonify({'error': 'Please upload a valid PDF or Word file', 'status': 400}), 400
  elif len(content_file) >= 33 * 1024 * 1024:
    return jsonify({'error': 'File size exceeds maximum allowed size (33 MB)', 'status': 413}), 413
  
  status = plagiarism.get_information(npm)
  if not status:
    return jsonify({"status": 400, "message": "NPM Not Found"}), 400

  files = {
    'ctl00$MainContent$FileUpload1': (file.filename, content_file, mimetype)
  }

  message = plagiarism.turnitin(npm, title, files)
  if message:
    return jsonify({"status": 200, "data": message}), 200
  else:
    return jsonify({"status": 400, "message": "Error processing the file"}), 400

@app.route('/turnitin/status', methods=['POST'])
def turnitin_status():
  data = request.json
  npm = data.get('npm', None)

  if not npm:
    return jsonify({'error': 'No NPM field in request', 'status': 400}), 400
  elif npm and len(data) > 1:
    return jsonify({'error': 'Key must be npm', 'status': 400}), 400

  message = plagiarism.get_turnitin_status(npm)
  if "Oooops..  NPM tidak terdaftar" in message:
    return jsonify({"status": 400, "data": {"message": message}}), 400
  elif message:
    return jsonify({"status": 200, "data": message}), 200
  else:
    return jsonify({"status": 400, "message": "Error processing the data"}), 400

@app.errorhandler(400)
def bad_request(e):
  return jsonify({ "status" : 400, "message": "Bad Request"}), 400

@app.errorhandler(404)
def page_not_found(e):
  return jsonify({ "status" : 404, "message": "Not Found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
  return jsonify({ "status" : 405, "message": "Method Not Allowed"}), 405

@app.errorhandler(500)
def internal_server_error(e):
  return jsonify({ "status" : 500, "message": "Internal Server Error"}), 500