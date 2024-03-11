# REST API Documentation

## Overview

**Unofficial REST API Form Booking Digital Library Room Atma Jaya Yogyakarta University (UAJY).**

_This API is used to manage room bookings. Such as viewing all booked rooms or by date, viewing all unbooked rooms or by date, and being able to book rooms._

This REST API is created by scraping data on

- [FORM BOOKING DIGITAL LIBRARY ROOM](http://form.lib.uajy.ac.id/booking/default.aspx)
- [CEK PENGGUNAAN RUANG](http://form.lib.uajy.ac.id/booking/CekJadwal.aspx)

## Installation

```bash
$ git clone https://github.com/Xractz/lib-uajy.git
$ cd lib-uajy
$ pip install -r requirements.txt
$ python main.py
```

## Endpoints

### GET /booked

Fetches data about all booked rooms.

**Parameters:**
None

**Response:**

- 200 : An array of booked rooms
  ```json
  {
    "bookedRoom": {
      "09/03/2024": [
        {
          "date": "09/03/2024",
          "name": "Name",
          "room": "Discussion Room 1",
          "time": "09.30 - 11.00 WIB"
        },
        {
          "date": "09/03/2024",
          "name": "Name",
          "room": "Discussion Room 2",
          "time": "09.30 - 11.00 WIB"
        },
        {
          "date": "09/03/2024",
          "name": "Name",
          "room": "Leisure Room 1",
          "time": "09.30 - 11.00 WIB"
        }
      ],
      "10/03/2024": [
        {
          "date": "09/03/2024",
          "name": "Name",
          "room": "Discussion Room 1",
          "time": "09.30 - 11.00 WIB"
        }
      ]
    },
    "message": "Successfully retrieved the booked room.",
    "status": 200
  }
  ```
- 404 : If no bookings are found
  ```json
  { "bookedRoom": { "status": 404, "message": "Booked room not found" } }
  ```

### GET /booked/{date}

Fetches data about all rooms booked on a specific date.

**Parameters:**

- `date`: The date to fetch bookings for

  - Format date : `ddmmyyyy`

**Response:**

- 200: An array of booked rooms for the given date
- `GET /booked/09032024`
  ```json
  {
    "bookedRoom": [
      {
        "date": "09/03/2024",
        "name": "Name",
        "room": "Discussion Room 1",
        "time": "09.30 - 11.00 WIB"
      },
      {
        "date": "09/03/2024",
        "name": "Name",
        "room": "Discussion Room 2",
        "time": "09.30 - 11.00 WIB"
      },
      {
        "date": "09/03/2024",
        "name": "Name",
        "room": "Leisure Room 1",
        "time": "09.30 - 11.00 WIB"
      }
    ],
    "message": "Successfully retrieved the booked room by date.",
    "status": 200
  }
  ```
- 404: If no bookings are found for the given date
  ```json
  { "bookedRoom": { "status": 404, "message": "Booked room not found" } }
  ```

### GET /available

Fetches data about all available rooms.

**Parameters:**
None

**Response:**

- 200: An array of available rooms
  ```json
  {
    "message": "Successfully retrieved the available room.",
    "roomAvailable": {
        "03/11/2024": {
            "Discussion Room 1": [
              "08.00 - 09.30 WIB",
              "09.30 - 11.00 WIB",
              "11.00 - 12.30 WIB",
              "14.00 - 15.30 WIB",
              "15.30 - 17.00 WIB",
              "17.00 - 18.30 WIB"
            ],
            "Discussion Room 2": [
              "08.00 - 09.30 WIB",
              "09.30 - 11.00 WIB",
              "11.00 - 12.30 WIB",
              "12.30 - 14.00 WIB",
              "14.00 - 15.30 WIB",
              "15.30 - 17.00 WIB",
              "17.00 - 18.30 WIB"
            ],
            "Discussion Room 3": [
              "08.00 - 09.30 WIB",
              "09.30 - 11.00 WIB",
              "11.00 - 12.30 WIB",
              "12.30 - 14.00 WIB",
              "14.00 - 15.30 WIB",
              "15.30 - 17.00 WIB",
              "17.00 - 18.30 WIB"
            ],
            "Leisure Room 1": [
              "08.00 - 09.30 WIB",
              "09.30 - 11.00 WIB",
              "11.00 - 12.30 WIB",
              "12.30 - 14.00 WIB",
              "14.00 - 15.30 WIB",
              "15.30 - 17.00 WIB",
              "17.00 - 18.30 WIB"
            ]
        },
        "09/03/2024": {
            "Discussion Room 1": [
                ...
            ],
            "Discussion Room 2": [
                ...
            ],
            "Discussion Room 3": [
                ...
            ],
            "Leisure Room 1": [
                ...
            ]
        },
    },
    "status": 200
  }
  ```
- 404: If no available rooms are found

```json
{ "roomAvailable": { "status": 404, "message": "Available room not found" } }
```

### GET /available/{date}

Fetches data about all rooms available on a specific date.

**Parameters:**

- `date`: The date to fetch availability for

  - Format date : `ddmmyyyy`

**Response:**

- 200: An array of available rooms
- `GET /available/09032024`
  ```json
  {
    "message": "Successfully retrieved the available room by date.",
    "roomAvailable": {
      "Discussion Room 1": ["08.00 - 09.30 WIB", "11.00 - 12.30 WIB", "12.30 - 14.00 WIB", "14.00 - 15.30 WIB", "15.30 - 17.00 WIB", "17.00 - 18.30 WIB"],
      "Discussion Room 2": ["08.00 - 09.30 WIB", "11.00 - 12.30 WIB", "12.30 - 14.00 WIB", "14.00 - 15.30 WIB", "15.30 - 17.00 WIB", "17.00 - 18.30 WIB"],
      "Discussion Room 3": ["08.00 - 09.30 WIB", "09.30 - 11.00 WIB", "11.00 - 12.30 WIB", "12.30 - 14.00 WIB", "14.00 - 15.30 WIB", "15.30 - 17.00 WIB", "17.00 - 18.30 WIB"],
      "Leisure Room 1": ["08.00 - 09.30 WIB", "14.00 - 15.30 WIB", "15.30 - 17.00 WIB", "17.00 - 18.30 WIB"]
    },
    "status": 200
  }
  ```
- 404: If no available rooms are found for the given date

```json
{ "roomAvailable": { "status": 404, "message": "Available room not found" } }
```

### POST /booking

This endpoint is useful for booking rooms

**Parameters:**

- `npm`
- `date`
  - Format date `dd/mm/yyyy`
- `room`
  - Discussion Room 1
  - Discussion Room 2
  - Discussion Room 3
  - Leisure Room 1
- `time`
  - 08.00 - 09.30 WIB
  - 09.30 - 11.00 WIB
  - 11.00 - 12.30 WIB
  - 12.30 - 14.00 WIB
  - 14.00 - 15.30 WIB
  - 15.30 - 17.00 WIB
  - 17.00 - 18.30 WIB

**Example :**

```json
{
  "npm": "xxxxxxxxx", //9 digits student number
  "room": "Discussion Room 1",
  "date": "11/03/2024",
  "time": "08.00 - 09.30 WIB"
}
```

**Response:**

- Response code 200 message :

  - Waktu yang anda pilih sudah dibooking, silahkan memilih waktu
  - Anda sudah booking di tanggal yang sama, silahkan memilih tanggal yang berbeda
  - Booking Success, please check your email

  ```json
  {"status": 200, "message": message}
  ```

- 400 :
  ```json
  { "status": 400, "message": "Booking room failed. Please try again." }
  ```
