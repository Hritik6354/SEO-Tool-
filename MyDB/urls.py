from django.urls import path
from . import views 
from MyDB.views import *
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static

urlpatterns = [
    #path('', views.navbar, name='navbar'),
    path('', views.seohome, name='seohome'),
    #path('', views.sign, name='register'),
    path('register/', views.sign, name='register'),
    path('login/', views.logn, name='login'),
    path('register/login/',views.logn,name='login'),
    path('index/', views.index, name='index'),
    
    #
    
    path('add/', views.addproject, name='addproject'),
    path('edit_project/<int:project_id>/', views.edit_project, name='edit_project'),
    path('delete_project/<int:project_id>/', views.delete_project, name='delete_project'),
    path('projdetail/<int:project_id>/', views.projdetail, name='projdetail'),
    #path('project/<int:pk>/', views.projdetail, name='view_project'),
    path('project/<int:project_id>/crawl/', views.start_crawl, name='start_crawl'),
    
    path('analysis_results/', views.analysis_results, name='analysis_results'),

    path('crawl/', views.handlecrawling, name='crawl'),
    path('analytics/', views.analytics, name='analytics'),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('index/dashboard/', views.dashboard, name="dashboard"),
    path('index/analytics/', views.analytics, name='analytics'),
    path('index/addproject/addrecord/', views.addrecord, name='addrecord'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login'), name='logout'),
    path('logout/', views.logout, name='logout'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('index/aboutus/', views.aboutus, name='aboutus'),
    path('contect_us/', views.contect_us, name='contect_us'),
    path('services/', views.services, name="services"),
    path('index/services', views.services, name="services"),
    path('index/contect_us/', views.contect_us, name='contect_us'),
    path('my-account/', views.my_account, name='my_account'),
    path('planpricing/', views.planpricing, name='planpricing'),
    
    #path('project/<int:project_id>/report/pdf/', views.generate_project_pdf, name='project_pdf'),
    path('generate-report/', views.generate_project_report, name='generate_project_report'),
    
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    
    path('change-password/', views.change_password, name='change_password'),
    #path('password_reset/', auth_views.PasswordResetView.as_view(template_name='forgotpassword.html'), name='password_reset'),
    #path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    #path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    #path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    #path('forgetpassword/', views.forgetpassword, name='forgetpassword'),
    #path('cpassword/<token>/', views.cpassword, name='cpassword'),
    #path('changepassword/', views.changepassword, name='changepassword'),
    
    # New URLs for forgot password
    
] #+ static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    
