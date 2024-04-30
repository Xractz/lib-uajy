import re, pytz, requests
from datetime import datetime, date

class Token:
  def __init__(self):
    self.url = "http://form.lib.uajy.ac.id/booking/default.aspx"
    self.session = requests.Session()
    self.viewState = None
    self.viewStateGenerator = None
    self.eventValidation = None
    
  def fetch_token(self, type=None):
    url = self.url if type is None else type
    response = self.session.get(url, verify=False)
    text = response.text

    self.viewState = re.search(r'id="__VIEWSTATE" value="(.*?)"', text).group(1)
    self.viewStateGenerator = re.search(r'id="__VIEWSTATEGENERATOR" value="(.*?)"', text).group(1)
    self.eventValidation = re.search(r'id="__EVENTVALIDATION" value="(.*?)"', text).group(1)
    
  def get_token(self):
    if not self.viewState:
      raise ValueError("Token has not been fetched yet. Call fetch_token() first.")
    return {
      '__VIEWSTATE': self.viewState,
      '__VIEWSTATEGENERATOR': self.viewStateGenerator,
      '__EVENTVALIDATION': self.eventValidation
    }

class FetchData(Token):
  def __init__(self): 
    super().__init__()
    self.urlJadwal = "http://form.lib.uajy.ac.id/booking/CekJadwal.aspx"
    self.pageNumber = None
    self.name = None
    self.email = None
    self.bookedData = []
    self.groupedData = {}
    self.groupedDataOutput = {}
    self.tz = pytz.timezone('Asia/Jakarta')
    self.current_time = datetime.now(self.tz).strftime("%H.%M")
    self.current_date = datetime.now(self.tz).strftime("%d/%m/%Y")

  def fetch_max_page(self):
    response = self.session.get(self.urlJadwal, verify=False)
    response = response.text

    pageNumber = re.findall(r'<td colspan="5"><table>(.*?)</table>', response, re.DOTALL)
    pageNumber = pageNumber[0].replace('\n', '').replace('\t', '').replace('\r', '')
    pageNumber = re.findall(r'>(\d+)</a>', pageNumber)
    self.pageNumber = max(pageNumber)
    
  def get_max_page(self):
    if not self.pageNumber:
      raise ValueError("Page number has not been fetched yet. Call fetch_max_page() first.")
    return self.pageNumber

  def fetch_page_data(self, page):
    self.fetch_token(self.urlJadwal)
    token = self.get_token()
    
    data = {
      '__EVENTTARGET': 'ctl00$MainContent$gvTransaksi',
      '__EVENTARGUMENT': '',
      '__VIEWSTATEENCRYPTED': '',
    }
    data.update(token)
    
    if page != 1:
      data['__EVENTARGUMENT'] = f"Page${page}"
      response = self.session.post(self.urlJadwal, verify=False, data=data)
    else:
      response = self.session.post(self.urlJadwal, verify=False)
    
    pageData = re.findall(r'</tr><tr class="RowStyle">(.*?)<tr class="PagerStyle">', response.text, re.DOTALL)
    pageData = pageData[0].replace('\n', '').replace('\t', '').replace('\r', '').replace('  ', '')
    pageData = re.findall(r'<td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td>', pageData)

    for entry in pageData:
      self.bookedData.append({
        "room": entry[0],
        "date": entry[1],
        "time": entry[2],
        "name": entry[3]
      })

  def group_data(self):
    for item in self.bookedData:
      data = {'name': item['name'], 'time': item['time']}
      date = item['date']
      room = item['room']

      if date not in self.groupedData:
        self.groupedData[date] = []
          
      self.groupedData[date].append(item)

      if date not in self.groupedDataOutput:
        self.groupedDataOutput[date] = {}
      
      if room not in self.groupedDataOutput[date]:
        self.groupedDataOutput[date][room] = []
      
      self.groupedDataOutput[date][room].append(data)
      self.groupedDataOutput = {date: room for date, room in self.groupedDataOutput.items() if datetime.now(self.tz).strptime(date, '%d/%m/%Y') >= datetime.now(self.tz).strptime(self.current_date, '%d/%m/%Y')}

  def fetch_all_data(self):
    self.fetch_max_page()
    for i in range(1, int(self.get_max_page()) + 1):
      self.fetch_page_data(i)
    self.group_data()

class Room(FetchData):
  def __init__(self):
    super().__init__()
    self.fetch_all_data()
    self.list_time = ["08.00 - 09.30 WIB", "09.30 - 11.00 WIB", "11.00 - 12.30 WIB", "12.30 - 14.00 WIB", "14.00 - 15.30 WIB", "15.30 - 17.00 WIB", "17.00 - 18.30 WIB"]
    self.list_room = ["Discussion Room 1", "Discussion Room 2", "Discussion Room 3", "Leisure Room 1"]

  def get_booked_data(self):
    if self.groupedDataOutput:
      return {"bookedRoom": self.groupedDataOutput, "message": "Successfully retrieved the booked room."}, 200
    else:
      return {"bookedRoom": {}, "message": "Booked room not found"}, 404
  
  def get_booked_data_by_date(self, date):
    formatted_date = f"{date[:2]}/{date[2:4]}/{date[4:]}"
    if formatted_date in self.groupedData:
      output = {room: [] for room in self.list_room}

      for booked in self.groupedData[formatted_date]:
        room = booked['room']
        time = booked['time']
        name = booked['name']
        
        output[room].append({'time': time, 'name': name})

      return {"bookedRoom": output, "message": "Successfully retrieved the booked room by date."}, 200
    else:
      return {"bookedRoom": {}, "message": "Successfully retrieved the booked room by date."}, 404

  def get_available_rooms(self, date=None):
    listTime = self.list_time
    listRoom = self.list_room

    room_availability = {}
    output = {}

    for room in listRoom:
      room_availability[room] = set(listTime)

    for date, bookeds in self.groupedData.items():
      output[date] = {}
      
      for room in listRoom:
        output[date][room] = list(room_availability[room])
      
      for booked in bookeds:
        room = booked['room']
        time = booked['time']
        
        if time in output[date][room]:
          output[date][room].remove(time)
          
        if date == self.current_date:
          updated_times = []
          for times in output[self.current_date][room]:
            time_one = times.split(" ")[0]
            if time_one > self.current_time:
                updated_times.append(times)
          output[self.current_date][room] = updated_times

          for room, times in output[self.current_date].items():
            updated_times = []
            for time in times:
                time_one = time.split(" ")[0]
                if time_one > self.current_time:
                    updated_times.append(time)
            output[self.current_date][room] = updated_times
      output[date][room] = sorted((output[date][room]))

    output = {date: room for date, room in output.items() if datetime.now(self.tz).strptime(date, '%d/%m/%Y') >= datetime.now(self.tz).strptime(self.current_date, '%d/%m/%Y')}
    output = {date: {room: sorted(times) for room, times in rooms.items()} for date, rooms in output.items()}
    
    if date:
      return output

    if output:
      return {"roomAvailable": output, "message": "Successfully retrieved the available room."}, 200
    else:
      return {"roomAvailable": {}, "message": "There's no available room right now"}, 404

  def get_available_rooms_by_date(self, date_str):
    formatted_date = f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}"
    if formatted_date in self.groupedDataOutput:
      output = self.get_available_rooms()[formatted_date]
      return {"roomAvailable": output, "message": "Successfully retrieved the available room by date."}, 200
    else:
      formatted_date = date(int(date_str[4:]), int(date_str[2:4].lstrip('0')), int(date_str[:2].lstrip('0')))
      date_today = date.today()
      if formatted_date >= date_today:
        output = {}
        listTime = self.list_time
        listRoom = self.list_room

        for room in listRoom:
          output[room] = listTime

        if output:
          return {"roomAvailable": output, "message": "Successfully retrieved the available room by date."}, 200 
        else:
          return {"roomAvailable": {}, "message": "There's no available room right now"}, 404

  def get_information(self, npm):
    self.fetch_token()
    token = self.get_token()
    data = {
      '__EVENTTARGET': '',
      '__EVENTARGUMENT': '',
      '__LASTFOCUS': '',
      'ctl00$MainContent$txtNPM': npm,
      'ctl00$MainContent$txtNama': '',
      'ctl00$MainContent$txtEmail': '',
      'ctl00$MainContent$DdlRuang': 'Discussion Room 1',
      'ctl00$MainContent$txtTanggal': '',
      'ctl00$MainContent$DdlJam': '08.00 - 09.30 WIB'
    }
    data.update(token)

    response = self.session.post(self.url, verify=False, data=data)
    text = response.text
    
    if "Oooops..  NPM/NPP anda tidak terdaftar." in text:
      self.name = None
      self.email = None
    else:
      self.name = re.findall(r'name="ctl00\$MainContent\$txtNama" type="text" value="(.*?)"', text, re.DOTALL)[0]
      email_matches = re.findall(r'name="ctl00\$MainContent\$txtEmail" type="text" value="(.*?)"', text, re.DOTALL)
      if email_matches:
          email = email_matches[0]
          self.email = email if email else ""
      else:
          self.email = "" 
      return True

  def is_valid_date(self, date):
    try:
      datetime_object = datetime.strptime(date, '%d/%m/%Y')
      return datetime_object.strftime('%d/%m/%Y') >= self.current_date
    except ValueError:
      return False
  
  def is_valid_time(self, date, time):
    if date != self.current_date:
      return True
    time_two = time.split(" ")[2]
    return time_two >= self.current_time

  def booking_room(self, npm, room, date, time):
    check_data = self.get_information(npm)
    if not check_data:
      return {"message": "Oooops...  Your NPM/NPP is not registered."}, 404
    elif (room is None and date is None and time is None):
      if self.name == None:
        return {"message": "Oooops...  Your NPM/NPP is not registered."}, 404
      return {'npm' : npm, 'name' : self.name}, 200
    elif room not in self.list_room:
      return {"message": "Valid rooms field are Discussion Room 1, Discussion Room 2, Discussion Room 3, or Leisure Room 1"}, 400
    elif not self.is_valid_date(date):
      return {"message": "Please use DD/MM/YYYY format for 'date' field"}, 400
    elif time not in self.list_time:
      return {"message": "Valid time slots are 08.00 - 09.30 WIB, 09.30 - 11.00 WIB, 11.00 - 12.30 WIB, 12.30 - 14.00 WIB, 14.00 - 15.30 WIB, 15.30 - 17.00 WIB, or 17.00 - 18.30 WIB"}, 400
    elif not self.is_valid_time(date, time):
      return {"message": "Cannot book room at this time"}, 400

    date = f"{date[3:5]}/{date[:2]}/{date[6:]}"

    data = {
      '__EVENTTARGET': 'ctl00$MainContent$btnDaftar',
      '__EVENTARGUMENT': '',
      '__LASTFOCUS': '',
      '__VIEWSTATE': self.viewState,
      '__VIEWSTATEGENERATOR': self.viewStateGenerator,
      '__EVENTVALIDATION': self.eventValidation,
      'ctl00$MainContent$txtNPM': npm,
      'ctl00$MainContent$txtNama': self.name,
      'ctl00$MainContent$txtEmail': self.email,
      'ctl00$MainContent$DdlRuang': room,
      'ctl00$MainContent$txtTanggal': date,
      'ctl00$MainContent$DdlJam': time
    }

    response = self.session.post(self.url, verify=False, data=data)
    text = response.text
    message = re.search(r"alert\('(.+?)'\)", text)
    message = message.group(1) if message else "Booking room failed."

    status_code = 400 if message == "Booking room failed." else 200

    return {"npm": npm, "name": self.name, "message": message}, status_code

class Plagiarism(FetchData):
  def __init__(self, npm, title=None, file=None):
    super().__init__()
    self.urlPlagiarism = "http://form.lib.uajy.ac.id/plagiarisme/"
    self.urlPlagiarismStatus = "http://form.lib.uajy.ac.id/plagiarisme/status.aspx"
    self.npm = npm
    self.name = None
    self.email = None
    self.noPhone = None

    if file:
      self.file = file
      self.title = title
      self.file_contents = file.file.read()
      self.filename = file.filename
      self.mimetype = file.content_type
  
  def check_file(self):
    try:
      contents = self.file_contents
      mimetype = self.mimetype
      file_name = self.filename
      file_size = len(contents)
    except Exception:
      return "There was an error uploading the file", 400
    
    allowed_extensions = ['pdf', 'docx', 'doc']
    allowed_mimetypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']
    maximum_file_size = 33 * 1024 * 1024
    
    if mimetype not in allowed_mimetypes or file_name.split('.')[-1].lower() not in allowed_extensions:
      return {"message":"Please upload a valid PDF or Word file"}, 415
    elif file_size >= maximum_file_size:
      return {"message":"File size exceeds maximum allowed size (33 MB)"}, 413
    return True

  def get_information(self):
    self.fetch_token(self.urlPlagiarism)
    token = self.get_token()

    data = {
    '__EVENTTARGET': 'ctl00$MainContent$TextBox1',
    '__EVENTARGUMENT': '',
    '__LASTFOCUS': '',
    'ctl00$MainContent$TextBox1': self.npm,
    'ctl00$MainContent$TxtEmail': '',
    'ctl00$MainContent$TxtTlp': '',
    'ctl00$MainContent$txtTitle': '',
    'ctl00$MainContent$FileUpload1': '',
    }
    data.update(token)

    response = self.session.post(self.urlPlagiarism, verify=False, data=data).text
    try:
      self.name = re.search(r'name="ctl00\$MainContent\$txtNama" type="text" value="(.*?)"', response).group(1)
      self.email = re.search(r'name="ctl00\$MainContent\$TxtEmail" type="text" value="(.*?)"', response).group(1)
      self.noPhone = re.search(r'name="ctl00\$MainContent\$TxtTlp" type="text" value="(.*?)"', response).group(1)
    except:
      return False

    data = { 
      'name' : self.name,
      'email' : self.email,
      'phone' : self.noPhone
    }

    return data
  
  def upload(self):
    check_npm = self.get_information()
    if not check_npm:
      return {"message": "NPM Not Found"}, 404
    check_file = self.check_file()
    if check_file != True:
      return check_file
  
    data = {
    '__EVENTTARGET': '',
    '__EVENTARGUMENT': '',
    '__LASTFOCUS': '',
    '__VIEWSTATE': self.viewState,
    '__VIEWSTATEGENERATOR': self.viewStateGenerator,
    '__EVENTVALIDATION': self.eventValidation,
    'ctl00$MainContent$TextBox1': self.npm,
    'ctl00$MainContent$TxtEmail': self.email,
    'ctl00$MainContent$TxtTlp': self.noPhone,
    'ctl00$MainContent$txtTitle': self.title,
    'ctl00$MainContent$Button1': 'ADD'
    }
    
    files = {
    'ctl00$MainContent$FileUpload1': (self.filename, self.file_contents, self.mimetype)
    }

    response = self.session.post(self.urlPlagiarism, verify=False, data=data, files=files)
    text = response.text
    try:
      message = re.search(r"alert\('(.+?)'\)", text).group(1)
      data = {
        'npm' : self.npm,
        'name' : self.name,
        'email' : self.email,
        'phone' : self.noPhone,
        'document': {
          'title': self.title, 
          'filename':self.filename
        },
        'message' : message
      }
      return data, 200
    except:
      return {"message": "Error processing the file"}, 500

  def status(self):
    self.fetch_token(self.urlPlagiarismStatus)
    token = self.get_token()
    dataTurnitin = {}

    data = {
      '__VIEWSTATEENCRYPTED': '',
      'ctl00$MainContent$txtNPM': self.npm,
      'ctl00$MainContent$btnCek': 'CEK'
    }
    data.update(token)

    response = self.session.post(self.urlPlagiarismStatus, verify=False, data=data).text

    npmNotFound = re.search(r"alert\('(.+?)'\)", response)

    if npmNotFound:
      npmNotFound = npmNotFound.group(1)
      return {"message": npmNotFound}, 404

    table_pattern = r'<table[^>]*class="GridViewStyle"[^>]*>(.*?)</table>'
    table_match = re.search(table_pattern, response, re.DOTALL)

    if table_match:
      response = table_match.group(1)
      row_pattern = r'<tr[^>]*>\s*<td[^>]*>\s*(\d+)\s*</td><td[^>]*>(.*?)</td><td[^>]*>(.*?)</td><td[^>]*>(.*?)</td><td[^>]*>(.*?)</td>\s*</tr>'
      matches = re.findall(row_pattern, response, re.DOTALL)

      for match in matches:
        dataTurnitin[int(match[0])] = {
          'title': match[3].split('-')[2].strip().replace("\n", "").replace("\r", ""),
          'status': match[4]
        }
      return dataTurnitin, 200
    else:
      return {"message": "Error retrieving plagiarism status"}, 500