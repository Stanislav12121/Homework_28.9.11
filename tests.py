import pytest
import requests
from pydantic import ValidationError
from api import AuthRequestModel, auth_token, create_booking, BookingResponseModel, CreateBookingRequest, BookingResponse

@pytest.mark.auth
@pytest.mark.parametrize('username, password, headers', [
    ('admin', 'password123', {"Content-Type": "application/json"}),  # Тест с корректными данными
    ('admin', 'password123', {"Content-Type": ""}),                  # Пустое поле заголовка Content-Type
    ('admin', 'password123', {}),                                    # Отсутствие заголовка
    ('admin1', 'password123', {"Content-Type": "application/json"}), # Некорректный логин
    ('', '', {"Content-Type": "application/json"}),                  # Отсутствие логина и пароля
    ('dsaqwe', 'asd123', {"Content-Type": "application/json"}),      # Некорректные логин и пароль

])
def test_auth_request(username, password, headers):
    url = "https://restful-booker.herokuapp.com/auth"

    try:
        data = AuthRequestModel(username=username, password=password)
    except ValidationError as e:
        if username == '' and password == '':
            assert str(e) == "1 validation error for AuthRequestModel\nusername\n  " \
                             "field required (type=value_error.missing)\npassword\n  " \
                             "field required (type=value_error.missing)"
        else:
            pytest.fail(f"Failed to validate request data: {e}")

    response = requests.post(url, headers=headers, json=data.dict())

    assert response.status_code == 200, f"Request failed with status code {response.status_code}"
    if "reason" in response.json() and response.json()["reason"] == "Bad credentials":
        assert "token" not in response.json(), "Response contains a token for invalid credentials"
    else:
        assert "token" in response.json(), "Response does not contain a token"

@pytest.mark.xfail
@pytest.mark.required_token
@pytest.mark.parametrize(
    'auth_token, create_booking, content_type, expected_status',
    [(auth_token(), create_booking(auth_token), 'application/json', 201),      #Корректные токен и данные
     ('asd324sda', create_booking(auth_token), 'application/json', 403),       #Некорректный токен и корректные данные
     (auth_token(), '-1', 'application/json', 405),                            #Некорректный bookingid и корректные данные
     (auth_token(), create_booking(auth_token), 'text/plain', 415)])           #Некорректный Content-Type и корректные данные
def test_delete_booking(auth_token, create_booking, content_type, expected_status):

    url = f'https://restful-booker.herokuapp.com/booking/{create_booking}'
    headers = {
        'Content-Type': f'{content_type}',
        'Cookie': f'token={auth_token}'
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 201:
        assert response.status_code == expected_status, f'Delete booking request failed with status code {response.status_code}'
        assert response.text == 'Created', 'Delete booking response should contain "Created"'
    elif response.status_code == 403:
        assert response.status_code == expected_status, f'Delete booking request failed with status code {response.status_code}'
        assert response.text == 'Forbidden', 'Delete booking response should contain "Created"'
    elif response.status_code == 405:
        assert response.status_code == expected_status, f'Delete booking request failed with status code {response.status_code}'
        assert response.text == 'Method Not Allowed', 'Delete booking response should contain "Created"'
    elif response.status_code == 415:
        assert response.status_code == expected_status, f'Delete booking request failed with status code {response.status_code}'
        assert response.text == 'Unsupported Media Type', 'Delete booking response should contain "Created"'

@pytest.mark.without_token
@pytest.mark.parametrize('booking_id, expected_status, headers', [
    (1, 200, {"Accept": "application/json"}),       # Корректные данные
    (0, 404, {"Accept": "application/json"}),       # Некорректный booking_id
    (-1, 404, {"Accept": "application/json"}),      # Некорректный booking_id
    ('a', 404, {"Accept": "application/json"}),     # Некорректный booking_id
    (1, 418, {"Accept": ""}),                       # Пустое значение возвращаемого формата ответа
    (1, 200, None)])                                # Не указан формат возвращаемого ответа
def test_get_booking(booking_id, expected_status, headers):
    url = f"https://restful-booker.herokuapp.com/booking/{booking_id}"

    response = requests.get(url, headers=headers)

    assert response.status_code == expected_status, f"Request failed with status code {response.status_code}"

    if expected_status == 200:
        try:
            data = response.json()
            booking = BookingResponseModel(**data)
        except (ValidationError, TypeError) as e:
            pytest.fail(f"Failed to validate booking response data: {e}")

        assert booking.firstname != '', "Firstname is missing"
        assert booking.lastname != '', "Lastname is missing"
        assert booking.totalprice >= 0, "Total price must be non-negative"
        assert isinstance(booking.depositpaid, bool), "Depositpaid must be a boolean"
        assert isinstance(booking.bookingdates, dict), "Bookingdates must be a dictionary"
        assert "checkin" in booking.bookingdates and isinstance(booking.bookingdates["checkin"], str), \
            "Checkin date is missing or invalid"
        assert "checkout" in booking.bookingdates and isinstance(booking.bookingdates["checkout"], str), \
            "Checkout date is missing or invalid"

@pytest.mark.xfail
@pytest.mark.without_token
@pytest.mark.parametrize('headers, request_body, expected_status', [
    ({"Content-Type": "application/json", "Accept": "application/json"},
     {"firstname": "Jim", "lastname": "Brown", "totalprice": 111, "depositpaid": True,
        "bookingdates": {"checkin": "2018-01-01", "checkout": "2019-01-01"},
        "additionalneeds": "Breakfast"}, 200),          # Корректные данные
    ({"Content-Type": "text/plain", "Accept": "text/plain"},
     {"firstname": "Jim", "lastname": "Brown", "totalprice": 111, "depositpaid": True,
      "bookingdates": {"checkin": "2018-01-01", "checkout": "2019-01-01"},
        "additionalneeds": "Breakfast"}, 415),          # Некорректные значение Content-Type, Accept
    (None, {"firstname": "Jim", "lastname": "Brown", "totalprice": 111, "depositpaid": True,
        "bookingdates": {"checkin": "2018-01-01", "checkout": "2019-01-01"},
        "additionalneeds": "Breakfast"}, 200)])         # Отсутствуют заголовки
def test_create_booking(headers, request_body, expected_status):
    url = "https://restful-booker.herokuapp.com/booking"

    try:
        request_data = CreateBookingRequest(**request_body)
    except ValidationError as e:
        pytest.fail(f"Failed to validate request data: {e}")

    response = requests.post(url, headers=headers, json=request_data.dict())

    assert response.status_code == expected_status, f"Request failed with status code {response.status_code}"

    if expected_status == 200:
        try:
            response_data = response.json()
            booking_response = BookingResponse(**response_data)
        except (ValidationError, TypeError) as e:
            pytest.fail(f"Failed to validate booking response data: {e}")

        assert booking_response.bookingid is not None and isinstance(booking_response.bookingid, int), \
            "Booking ID is missing or invalid"
        assert isinstance(booking_response.booking, CreateBookingRequest), \
            "Booking data is missing or invalid"
        booking = booking_response.booking
        assert booking.firstname == request_data.firstname, "Invalid firstname in the response"
        assert booking.lastname == request_data.lastname, "Invalid lastname in the response"
        assert booking.totalprice == request_data.totalprice, "Invalid totalprice in the response"
        assert booking.depositpaid == request_data.depositpaid, "Invalid depositpaid in the response"
        assert booking.bookingdates.dict() == request_data.bookingdates.dict(), "Invalid bookingdates in the response"
        assert booking.additionalneeds == request_data.additionalneeds, "Invalid additionalneeds in the response"