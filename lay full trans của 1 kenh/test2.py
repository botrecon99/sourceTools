import requests

# Địa chỉ API của bên thứ ba
TRANSCRIPT_API_URL = "https://www.youtube-transcript.io/api/transcripts"

# Video ID để test
video_id = "-bWvhNGL6sY"

# Payload: mảng chứa video ID
payload = {"ids": [video_id]}  

# Headers: Authorization Bearer Token
headers = {
    'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjcxMTE1MjM1YTZjNjE0NTRlZmRlZGM0NWE3N2U0MzUxMzY3ZWViZTAiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoibmd1eeG7hW4gdsSDbiBjw7RuZyIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NMbm80OTBTZzZYOXRyVnotMllMYkQ1NVVWUkRIS1pkdTIwUG1ld1FvdENZX0gwaHdiLVZnPXM5Ni1jIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL3RyYW5zY3JpcHQtZmM1ODEiLCJhdWQiOiJ0cmFuc2NyaXB0LWZjNTgxIiwiYXV0aF90aW1lIjoxNzQ0MjA3MjM3LCJ1c2VyX2lkIjoiTG9CUFN3c3VwWmZVQVhPT1lUVk4zb0o2czlQMiIsInN1YiI6IkxvQlBTd3N1cFpmVUFYT09ZVFZOM29KNnM5UDIiLCJpYXQiOjE3NDQyMTA5ODEsImV4cCI6MTc0NDIxNDU4MSwiZW1haWwiOiJjb25nYW5oaWlrazlAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMTY5NTg2Nzc1NDUzNzg1NjM1MzkiXSwiZW1haWwiOlsiY29uZ2FuaGlpa2s5QGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6Imdvb2dsZS5jb20ifX0.S4b0-r6AGQWRHhcKrYFran38WiMieQqAXvpu5goIcbzAa_Fx9Ma8j3oNJYFLJ_hpo4RR_Z9d6HEMvE6Ow-5m_Iho-sjD2cuHEbUlB7-2v_nQJGvPkFgDpGxpQad-U_yfBGv0Ky_nxP9v4s1XYh3xAVsgZ_UOgVMaqlx_GruWetIi70tXCEaO1AigijvaHmuL_UaX5GCa0TfDbsEwnyY6SknGgcaA3toJeK7S8gqwFV0L-YxP17Cu5tLJlnBRssISF6eAbob6b_VWP7QP0LCE-2IdyVBBpI26GiyfTuUpZOnXFEqKrX7ETbVOGFZ-ZxVVQmjrAlcj5f6NPGVEo5ko2g',  # Thêm token hợp lệ của bạn vào đây
    'Content-Type': 'application/json'
}

# Gửi yêu cầu POST tới API
response = requests.post(TRANSCRIPT_API_URL, json=payload, headers=headers)

# Kiểm tra nếu trả về mã 200 (OK)
if response.status_code == 200:
    data = response.json()
    print("Phụ đề cho video", video_id, "đã được lấy thành công!")
    print("Transcript:", data)  # In ra toàn bộ transcript
else:
    print(f"❌ Lỗi khi gọi API: {response.status_code}")
