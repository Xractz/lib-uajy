from app.main import Room, Plagiarism
from pydantic import BaseModel, Field
from typing import Union, Annotated
from fastapi.responses import JSONResponse
from fastapi import status, APIRouter, File, UploadFile, Form

router = APIRouter()
room = Room()

@router.get(
  "/booked",
  response_model=dict,
  tags=["BOOKED ROOM"],
  summary="Get booked room data",
  description="Get the booked room data",
  responses={
    200: {
      "description": "Successfully retrieved the booked room",
      "content": {
        "application/json": {
          "example": {
            "bookedRoom": {
              "29/04/2024": {
                "Discussion Room 1": [
                  {
                  "name": "name",
                  "time": "14.00 - 15.30 WIB"
                  },
                  {
                  "name": "name",
                  "time": "15.30 - 17.00 WIB"
                  },
                ],
                "Discussion Room 2" : [],
                "Discussion Room 3" : [],
                "Leisure Room 1":[]
              }
            },
            "message": "Successfully retrieved the booked room."
          }
        }
      }
    },
    404: {
      "description": "Booked room not found",
      "content": {
        "application/json": {
          "example": {
            "bookedRoom": {},
            "message": "Booked room not found"
          }
        }
      }
    }
  }
)
async def all_booked():
  message, status = room.get_booked_data()
  return JSONResponse(content=message, status_code=status)
  
@router.get(
  "/booked/{date}",
  response_model=dict,
  tags=["BOOKED ROOM"],
  summary="Get booked room data by date",
  description="Get the booked room data by date",
  responses={
    200: {
      "description": "Successfully retrieved the booked room by date",
      "content": {
        "application/json": {
          "example": {
            "bookedRoom": [
              {
                "room": "Discussion Room 1",
                "date": "29/04/2024",
                "time": "14.00 - 15.30 WIB",
                "name": "Jhon Abe"
              },
              {
                "room": "Discussion Room 2",
                "date": "29/04/2024",
                "time": "14.00 - 15.30 WIB",
                "name": "Jhon Abe"
              },
              {
                "room": "Discussion Room 3",
                "date": "29/04/2024",
                "time": "14.00 - 15.30 WIB",
                "name": "Jhon Abe"
              },
              {
                "room": "Leisure Room 1",
                "date": "29/04/2024",
                "time": "14.00 - 15.30 WIB",
                "name": "Jhon Abe"
              }
            ],
            "message": "Successfully retrieved the booked room by date."
          }
        }
      }
    },
    404: {
      "description": "Booked room not found",
      "content": {
        "application/json": {
          "example": {
            "bookedRoom": {},
            "message": "Booked room not found"
          }
        }
      }
    }
  }
)
async def booked_by_date(date: str):
  message, status = room.get_booked_data_by_date(date)
  return JSONResponse(content=message, status_code=status)
  
@router.get(
  "/available",
  response_model=dict,
  tags=["AVAILABLE ROOM"],
  summary="Get available room data",
  description="Get the available room data",
  responses={
    200: {
      "description": "Successfully retrieved the available room",
      "content": {
        "application/json": {
          "example": {
            "roomAvailable": {
              "29/04/2024": {
                "Discussion Room 1" : [],
                "Discussion Room 2" : [],
                "Discussion Room 3" : [],
                "Leisure Room 1" : []
              },
              "30/04/2024": {
                "Discussion Room 1" : [
                  "08.00 - 09.30 WIB",
                  "09.30 - 11.00 WIB",
                  "17.00 - 18.30 WIB"  
                ],
                "Discussion Room 2" : [
                  "08.00 - 09.30 WIB",
                  "17.00 - 18.30 WIB"
                ],
                "Discussion Room 3" : [
                  "17.00 - 18.30 WIB"
                ],
                "Leisure Room 1" : []
              }
            },
            "message": "Successfully retrieved the available room."
          }
        }
      }
    },
    404: {
      "description": "There's not available room right now",
      "content": {
        "application/json": {
          "example": {
            "roomAvailable": {},
            "message": "There's no available room right now"
          }
        }
      }
    }
  }
)
def available_rooms():
  message, status = room.get_available_rooms()
  return JSONResponse(content=message, status_code=status)

@router.get(
  "/available/{date}",
  response_model=dict,
  tags=["AVAILABLE ROOM"],
  summary="Get available room data by date",
  description="Get the available room data by date",
  responses={
    200: {
      "description": "Successfully retrieved the available room by date",
      "content": {
        "application/json": {
          "example": {
            "roomAvailable": {
              "Discussion Room 1" : [
                "08.00 - 09.30 WIB",
                "09.30 - 11.00 WIB",
                "17.00 - 18.30 WIB"  
              ],
              "Discussion Room 2" : [
                "08.00 - 09.30 WIB",
                "17.00 - 18.30 WIB"
              ],
              "Discussion Room 3" : [
                "17.00 - 18.30 WIB"
              ],
              "Leisure Room 1" : []
            },
            "message": "Successfully retrieved the available room by date."
          }
        }
      }
    },
    400: {
      "description": "Invalid date format",
      "content": {
        "application/json": {
          "example": {
            "message": "Invalid date format. Please use the format 'dd/mm/yyyy'"
          }
        }
      }
    },
    404: {
      "description": "There's not available room right now",
      "content": {
        "application/json": {
          "example": {
            "roomAvailable": {},
            "message": "There's no available room right now"
          }
        }
      }
    }
  }
)
def available_rooms_by_date(date: str):
  try:
    message, status = room.get_available_rooms_by_date(date)
  except ValueError as e:
    return JSONResponse(content={"message": str(e)}, status_code=400)
  
  return JSONResponse(content=message, status_code=status)

class BookingRoom(BaseModel):
  npm: int
  room: Union[str, None] = None
  date: Union[str, None] = None
  time: Union[str, None] = None

@router.post(
  "/booking",
  response_model=dict,
  tags=["BOOKING ROOM"],
  summary="Booking room",
  description="Booking a room",
  responses={
    200: {
      "description": "Successfully booked the room",
      "content": {
        "application/json": {
          "schema": {
            "required": ["npm", "room", "date", "time"],
            "type": "object",
            "properties": {
              "npm": {"type": "integer", "example": 1234567890},
              "room": {"type": "string", "example": ["Discussion Room 1", "Discussion Room 2", "Discussion Room 3", "Leisure Room 1"]},
              "date": {"type": "string", "example": "29/04/2024"},
              "time": {"type": "string", "example": ["08.00 - 09.30 WIB", "09.30 - 11.00 WIB", "11.00 - 12.30 WIB", "12.30 - 14.00 WIB", "14.00 - 15.30 WIB", "15.30 - 17.00 WIB", "17.00 - 18.30 WIB"]}
            },
          },
          "example": {
            "message": "Booking Success, please check your email",
            "npm": 1234567890,
            "name": "Jhon Doe"
          }
        }
      }
    },
    400: {
      "description": "Booking room failed",
      "content": {
        "application/json": {
          "schema": {
            "required": ["room", "date", "time"],
            "type": "object",
            "properties": {
              "room": {"type": "string", "example": ["Discussion Room 1", "Discussion Room 2", "Discussion Room 3", "Leisure Room 1"]},
              "date": {"type": "string", "example": "29/04/2024"},
              "time": {"type": "string", "example": ["08.00 - 09.30 WIB", "09.30 - 11.00 WIB", "11.00 - 12.30 WIB", "12.30 - 14.00 WIB", "14.00 - 15.30 WIB", "15.30 - 17.00 WIB", "17.00 - 18.30 WIB"]}
            },
          },
          "example": {
            "message": [
              "Booking room failed. Please try again.",
              "Valid rooms field are Discussion Room 1, Discussion Room 2, Discussion Room 3, or Leisure Room 1",
              "Please use DD/MM/YYYY format for 'date' field",
              "Valid time slots are 08.00 - 09.30 WIB, 09.30 - 11.00 WIB, 11.00 - 12.30 WIB, 12.30 - 14.00 WIB, 14.00 - 15.30 WIB, 15.30 - 17.00 WIB, or 17.00 - 18.30 WIB",
              "Cannot book room at this time"
            ],
          }
        }
      }
    },
  404: {
    "description": "NPM Not Found",
    "content": {
      "application/json": {
        "example": {
          "message": "Oooops...  Your NPM/NPP is not registered."
        }
      }
    }
  }
  }
)
def booking_room(data: BookingRoom):
  message, status = room.booking_room(data.npm, data.room, data.date, data.time)
  return JSONResponse(content=message, status_code=status)
  
@router.post(
  "/turnitin", 
  tags=["PLAGIARISM CHECKER"],
  summary="Upload file to check plagiarism",
  description="Upload file to check plagiarism",
  responses={
    200: {
      "description": "File uploaded successfully",
      "content": {
        "application/json": {
          "example": {
            'npm' : 1234567890,
            'name' : "Jhon Abe",
            'email' : "jhonabe@gmail.com",
            'phone' : "628773433xxxx",
            'document': {
              'title': "HUBUNGAN KARAKTERISTIK INDIVIDU DENGAN KINERJA KARYAWAN", 
              'filename':"skripsiku_final.pdf"
            },
            'message' : "Terimakasih sudah melakukan input cek plagiarisme, silahkan cek email Anda"
          }
        }
      }
    },
    400: {
      "description": "File upload failed",
      "content": {
        "application/json": {
          "example": {
            "message": "There was an error uploading the file"
          }
        }
      }
    },
    404: {
      "description": "NPM Not Found",
      "content": {
        "application/json": {
          "example": {
            "message": "NPM Not Found"
          }
        }
      }
    },
    413:{
      "description": "File size exceeds maximum allowed size (33 MB)",
      "content": {
        "application/json": {
          "example": {
            "message": "File size exceeds maximum allowed size (33 MB)"
          }
        }
      }
    },
    415:{
      "description": "Please upload a valid PDF or Word file",
      "content": {
        "application/json": {
          "example": {
            "message": "Please upload a valid PDF or Word file"
          }
        }
      }
    },
    500: {
      "description": "Error processing the file",
      "content": {
        "application/json": {
          "example": {
            "message": "Error processing the file"
          }
        }
      }
    }
  }
)
def upload(
  file: Annotated[UploadFile, File(...)],
  npm: Annotated[int, Form(...)],
  title: Annotated[str, Form(...)]
):
  plagiarism = Plagiarism(npm, title, file)
  message, status = plagiarism.upload()
  
  return JSONResponse(content=message, status_code=status)

class PlagiarismStatus(BaseModel):
  npm: int = Field(..., example=1234567890)

@router.post(
  "/turnitin/status", 
  tags=["PLAGIARISM CHECKER"], 
  summary="Check plagiarism status", 
  description="Check plagiarism status",
  responses={
    200: {
      "description": "Plagiarism status retrieved successfully",
      "content": {
        "application/json": {
          "example": {
            "1": {
              "title": "HUBUNGAN KARAKTERISTIK INDIVIDU DENGAN KINERJA KARYAWAN",
              "status": "Awaiting"
            }
          }
        }
      }
    },
    404: {
      "description": "NPM Not Found",
      "content": {
        "application/json": {
          "example": {
            "message": "NPM Not Found"
          }
        }
      }
    },
    500: {
      "description": "Error retrieving plagiarism status",
      "content": {
        "application/json": {
          "example": {
            "message": "Error retrieving plagiarism status"
          }
        }
      }
    }
  }
)
def check_status(data: PlagiarismStatus):
  plagiarism = Plagiarism(data.npm)
  message, status = plagiarism.status()
  
  return JSONResponse(content=message, status_code=status)