# Đọc file input_links.txt để lấy danh sách các liên kết
with open('input_links.txt', 'r') as file:
    input_links = file.readlines()

# Xử lý các liên kết trong file, loại bỏ ký tự \n ở cuối mỗi dòng
input_links = [link.strip() for link in input_links]

# Chuyển các liên kết thành mảng JavaScript
output_js_array = "const videoLinks = [\n"
for link in input_links:
    output_js_array += f'  "{link}",\n'

# Cắt bỏ dấu phẩy cuối cùng và thêm dấu đóng mảng
output_js_array = output_js_array.rstrip(",\n") + "\n];"

# Lưu mảng JavaScript vào file output.js
with open('output.js', 'w') as js_file:
    js_file.write(output_js_array)

# Xuất ra console để kiểm tra
print(output_js_array)
