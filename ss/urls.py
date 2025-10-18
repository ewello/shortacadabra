from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('shorten', views.shorten, name="shorten"),
    path('urls/', views.viewUrls, name="urls"),
    path('url/<int:id>', views.viewUrl, name="url"),
    path('analytics/<int:id>', views.analytics, name="analytics"),
    path('domains/', views.domains, name="domains"),
    path('domains/<int:domain_id>/toggle/', views.toggle_domain, name="toggle_domain"),
    path('domains/<int:domain_id>/delete/', views.delete_domain, name="delete_domain"),
    path('url/<int:url_id>/delete/', views.deleteUrl, name="delete_url"),
    path('accounts/register', views.register, name="register"),
    path('<str:short>', views.redirectUrl, name="redirect")
]
