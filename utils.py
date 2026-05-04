# import json
#
# categories = [
#     {
#         "id": 1,
#         "name": "Go'sh maxsulotlari",
#         "photo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTu2OscgxRYn3SoqLTJqmDaZywRT7sPOU58gw&s"
#     },
#     {
#         "id": 2,
#         "name": "Ichimliklar",
#         "photo": "https://t4.ftcdn.net/jpg/02/79/69/21/360_F_279692163_4O1mMxIe4KdK3GZYl8gDY02zBFn65Gj0.jpg"
#     }
# ]
#
# products = [
#     {
#         "id": 1,
#         "name": "Pepsi",
#         "photo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQhEEDDi983uTfDNTuaUPVC9ah3IBIycUz-Bg&s",
#         "category_id": 2,
#         "price": 12_000,
#         "amount": 500,
#         "is_discount": False
#     },
# ]
#
# with open("db/categories.json", "w") as f:
#     json.dump(categories, f, indent=3)
#
# with open("db/products.json", "w") as f:
#     json.dump(products, f, indent=3)
from pathlib import Path

