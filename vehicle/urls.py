from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('',view=views.home,name="home"),
    path('login/',view=views.login,name="login"),
    path('signup/',views.signup,name="signup"),
    path('admin_login/',views.admin_login),
    path('admin_dashboard/',views.admin_dashboard,name="admin_dashboard"),
    path("add_driver/",views.add_driver),
    path("manage_drivers/",views.manage_drivers),
    path("edit_driver/",views.edit_driver),
    path("add_vehicle/",views.add_vehicle),
    path("manage_vehicle/",views.manage_vehicle),
    path("edit_vehicle/",views.edit_vehicle),
    path("manage_rental_status/",views.manage_rental_status,name="manage_rental_status"),
    path("edit_rental_status/",views.edit_rental_status),
    path('logout/', views.logout_view, name='logout'),
    path("delete_driver/", views.delete_driver),
    path("manage_drivers_edit/<int:id>/", views.manage_drivers_edit),
    path('update_vehicle/', views.update_vehicle),
    path('edit_vehicle/<int:id>/', views.edit_vehicle),
    path('delete_vehicle/<int:id>/', views.delete_vehicle, name='delete_vehicle'),
    path('update_driver/', views.update_driver, name='update_driver'),
    path('queue_booking/<int:vehicle_id>/', views.queue_booking, name='queue_booking'),
    path('my_bookings/',views.my_bookings,name='my_bookings'),
    path('driver_requests/', views.driver_requests, name='driver_requests'),
    path('accept_booking/<int:booking_id>/', views.accept_booking, name='accept_booking'),
    path('reject_booking/<int:booking_id>/', views.reject_booking, name='reject_booking'),
    path('notifications/', views.user_notifications, name='notifications'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)