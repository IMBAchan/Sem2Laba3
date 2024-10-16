"""
URL configuration for dbproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from laba2.views import all_records_view, upload_sql_file_view, home_view, all_products_view, place_order, order_confirmation, confirm_order, list_and_delete_suppliers  # Імпортуємо нове представлення
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('all-records/', all_records_view, name='all_records'),
    path('upload-sql/', upload_sql_file_view, name='upload_sql'),  # Додаємо новий маршрут
    path('', home_view, name='home'),
    path('all-products/', all_products_view, name='all_products'),
    path('place-order/', place_order, name='place_order'),
    path('confirm-order/<int:article>/', confirm_order, name='confirm_order'),
    path('order-confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),
    path('suppliers/', list_and_delete_suppliers, name='list_and_delete_suppliers'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)