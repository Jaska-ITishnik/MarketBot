import os

import uvicorn
from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy_file.storage import StorageManager
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin import I18nConfig
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla import ModelView

from config import settings
from db import User, Category, Product, Order, Payment
from db.base import db
from web.provider import UsernameAndPasswordProvider

middleware = [
    Middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
]

app = Starlette(middleware=middleware)

i18n_config = I18nConfig(
    default_locale="uz"
)
logo_url = 'https://i.ibb.co/NgjxKy0c/china-uzbek.jpg'
admin = Admin(
    engine=db._engine,
    title="Online Shop",
    templates_dir='templates/admin/index.html',
    base_url='/',
    logo_url=logo_url,
    login_logo_url='https://i.ibb.co/RkbDfwS7/login-logo-2.jpg',
    auth_provider=UsernameAndPasswordProvider(),
    i18n_config=i18n_config
)


class UserModelView(ModelView):
    label = "🤵 Klientlar"
    # list_template = ''

    fields_default_sort = 'last_name', 'first_name', 'phone'
    searchable_fields = 'last_name', 'first_name', 'phone'
    exclude_fields_from_edit = 'created_at', 'updated_at'


class CategoryModelView(ModelView):
    label = "🍡Kategoriyalar"
    exclude_fields_from_create = 'created_at', 'updated_at'
    exclude_fields_from_edit = 'created_at', 'updated_at'


class ProductModelView(ModelView):
    label = "🧈Maxsulotlar"
    exclude_fields_from_create = 'created_at', 'updated_at'
    exclude_fields_from_edit = 'created_at', 'updated_at'


class OrderModelView(ModelView):
    label = "Buyurtmalar"
    exclude_fields_from_create = 'created_at', 'updated_at'
    exclude_fields_from_edit = 'created_at', 'updated_at'


class PaymentModelView(ModelView):
    label = "💲To'lovlar"
    exclude_fields_from_create = 'created_at', 'updated_at'
    exclude_fields_from_edit = 'created_at', 'updated_at'


admin.add_view(UserModelView(User))
admin.add_view(CategoryModelView(Category))
admin.add_view(ProductModelView(Product))
admin.add_view(OrderModelView(Order))
admin.add_view(PaymentModelView(Payment))

# Mount admin to your app
admin.mount_to(app)

# Configure Storage
os.makedirs("./media/attachment", 0o777, exist_ok=True)
container = LocalStorageDriver("./media").get_container("attachment")
StorageManager.add_storage("default", container)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)
