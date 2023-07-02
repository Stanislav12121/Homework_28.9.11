import requests
from pydantic import BaseModel, constr, Field

class AuthRequestModel(BaseModel):
    username: constr(strict=True)   # Username for authentication, valid: admin
    password: constr(strict=True)   # Password for authentication, valid: password123
class AuthResponse(BaseModel):
    token: str
class BookingDates(BaseModel):
    checkin: str
    checkout: str

class BookingResponseModel(BaseModel):
    firstname: str = Field(..., description="Firstname for the guest who made the booking")
    lastname: str = Field(..., description="Lastname for the guest who made the booking")
    totalprice: int = Field(..., description="The total price for the booking")
    depositpaid: bool = Field(..., description="Whether the deposit has been paid or not")
    bookingdates: dict = Field(..., description="Sub-object that contains the checkin and checkout dates")
    additionalneeds: str = Field(None, description="Any other needs the guest has")

    class Config:
        allow_population_by_field_name = True

class CreateBookingRequest(BaseModel):
    firstname: str = Field(..., description="Firstname for the guest who made the booking")
    lastname: str = Field(..., description="Lastname for the guest who made the booking")
    totalprice: int = Field(..., description="The total price for the booking")
    depositpaid: bool = Field(..., description="Whether the deposit has been paid or not")
    bookingdates: BookingDates = Field(..., description="Dates for check-in and check-out")
    additionalneeds: str = Field(..., description="Any other needs the guest has")

class BookingResponse(BaseModel):
    bookingid: int
    booking: CreateBookingRequest

class Booking(BaseModel):
    firstname: str
    lastname: str
    totalprice: int
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str

class CreateBookingResponse(BaseModel):
    bookingid: int

def auth_token():
    url = 'https://restful-booker.herokuapp.com/auth'
    headers = {'Content-Type': 'application/json'}
    data = {
        'username': 'admin',
        'password': 'password123'
    }
    response = requests.post(url, headers=headers, json=data)
    response_model = AuthResponse(**response.json())
    return response_model

def create_booking(auth_token):
    url = 'https://restful-booker.herokuapp.com/booking'
    headers = {'Content-Type': 'application/json'}
    data = {
        'firstname': 'Jim',
        'lastname': 'Brown',
        'totalprice': 111,
        'depositpaid': True,
        'bookingdates': {
            'checkin': '2018-01-01',
            'checkout': '2019-01-01'
        },
        'additionalneeds': 'Breakfast'
    }
    response = requests.post(url, headers=headers, json=data)
    response_model = BookingResponse(**response.json())
    return response_model.bookingid