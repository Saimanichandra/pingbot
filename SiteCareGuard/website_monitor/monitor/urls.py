from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('website/<int:website_id>/', views.website_detail, name='website_detail'),
    path('website/<int:website_id>/data/', views.get_website_health_data, name='website_data'),  # ✅ Added for accurate Chart.js graph
    path('website/add/', views.add_website, name='add_website'),
    path('website/<int:website_id>/edit/', views.edit_website, name='edit_website'),
    path('website/<int:website_id>/delete/', views.delete_website, name='delete_website'),
    path('api/check/<int:website_id>/', views.check_website_ajax, name='check_website_ajax'),
    path('api/check-all/', views.check_all_websites_ajax, name='check_all_websites_ajax'),
    path('api/alerts/', views.get_alerts, name='get_alerts'),
    path('api/alerts/mark-read/', views.mark_alerts_read, name='mark_alerts_read'),
    path('website/<int:website_id>/data/', views.website_data, name='website_data'),

]
