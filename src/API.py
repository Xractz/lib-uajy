import re, pytz, requests
from datetime import datetime

class Room:
    def __init__(self):
        self.session = requests.Session()
        self.url = "http://form.lib.uajy.ac.id/booking/CekJadwal.aspx"
        self.urlPost = "http://form.lib.uajy.ac.id/booking/default.aspx"
        self.viewState = None
        self.viewStateGenerator = None
        self.eventValidation = None
        self.pageNumber = None
        self.name = None
        self.email = None
        self.bookedData = []
        self.groupedData = {}
        self.groupedDataOutput = {}
        self.tz = pytz.timezone('Asia/Jakarta')
        self.current_time = datetime.now(self.tz).strftime("%H.%M")
        self.current_date = datetime.now(self.tz).strftime("%d/%m/%Y")

    def fetch_data(self, url):
        response = self.session.get(url, verify=False)
        text = response.text

        self.viewState = re.search(r'id="__VIEWSTATE" value="(.*?)"', text).group(1)
        self.viewStateGenerator = re.search(r'id="__VIEWSTATEGENERATOR" value="(.*?)"', text).group(1)
        self.eventValidation = re.search(r'id="__EVENTVALIDATION" value="(.*?)"', text).group(1)

        if url == self.url:
            pageNumber = re.findall(r'<td colspan="5"><table>(.*?)</table>', text, re.DOTALL)
            pageNumber = pageNumber[0].replace('\n', '').replace('\t', '').replace('\r', '')
            pageNumber = re.findall(r'>(\d+)</a>', pageNumber)
            self.pageNumber = max(pageNumber)

    def fetch_page_data(self, page):
        data = {
            '__EVENTTARGET': 'ctl00$MainContent$gvTransaksi',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': self.viewState,
            '__VIEWSTATEGENERATOR': self.viewStateGenerator,
            '__VIEWSTATEENCRYPTED': '',
            '__EVENTVALIDATION': self.eventValidation,
        }

        if page == 1:
            response = self.session.post(self.url, verify=False)
        else:
            data['__EVENTARGUMENT'] = f"Page${page}"
            response = self.session.post(self.url, verify=False, data=data)

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

    def get_booked_data_by_date(self, date):
        formatted_date = f"{date[:2]}/{date[2:4]}/{date[4:]}"
        if formatted_date in self.groupedData:
            return self.groupedData[formatted_date]
        else:
            return []

    def get_available_rooms(self):
        listTime = ["08.00 - 09.30 WIB", "09.30 - 11.00 WIB", "11.00 - 12.30 WIB", "12.30 - 14.00 WIB", "14.00 - 15.30 WIB", "15.30 - 17.00 WIB", "17.00 - 18.30 WIB"]
        listRoom = ["Discussion Room 1", "Discussion Room 2", "Discussion Room 3", "Leisure Room 1"]

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

        return output

    def get_available_rooms_by_date(self, date):
        formatted_date = f"{date[:2]}/{date[2:4]}/{date[4:]}"
        if formatted_date in self.groupedData:
            return self.get_available_rooms()[formatted_date]
        else:
            return []

    def get_information(self, npm):
        self.fetch_data(self.urlPost)
        data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': self.viewState,
            '__VIEWSTATEGENERATOR': self.viewStateGenerator,
            '__EVENTVALIDATION': self.eventValidation,
            'ctl00$MainContent$txtNPM': npm,
            'ctl00$MainContent$txtNama': '',
            'ctl00$MainContent$txtEmail': '',
            'ctl00$MainContent$DdlRuang': 'Discussion Room 1',
            'ctl00$MainContent$txtTanggal': '',
            'ctl00$MainContent$DdlJam': '08.00 - 09.30 WIB'
        }

        response = self.session.post(self.urlPost, verify=False, data=data)
        text = response.text
        
        if "Oooops..  NPM/NPP anda tidak terdaftar." in text:
            self.name = None
            self.email = None
        else:
            self.name = re.findall(r'name="ctl00\$MainContent\$txtNama" type="text" value="(.*?)"', text, re.DOTALL)[0]
            self.email = re.findall(r'name="ctl00\$MainContent\$txtEmail" type="text" value="(.*?)"', text, re.DOTALL)[0]

    def booking_room(self, npm, room, date, time):
        self.get_information(npm)
        if (room == "" or date == "" or time == ""):
            data = {'name' : self.name, 'npm' : npm}
            return data
        
        date = f"{date[3:5]}/{date[:2]}/{date[6:]}"

        if self.name == None or self.email == None:
            return "Oooops..  NPM/NPP anda tidak terdaftar."
        
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

        response = self.session.post(self.urlPost, verify=False, data=data)
        text = response.text
        message = re.search(r"alert\('(.+?)'\)", text).group(1)
        data = {'message' : message, 'name' : self.name, 'npm' : npm}

        return data