from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/register/', views.student_register, name='student_register'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.user_logout, name='logout'),
    path('academician/login/', views.academician_login, name='academician_login'),
    path('academician/register/', views.academician_register, name='academician_register'),
    path('academician/dashboard/', views.academician_dashboard, name='academician_dashboard'),
    path('academician/student-list/', views.student_list, name='student_list'),
    path('courses/create/', views.create_course, name='create_course'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/add-students/', views.add_students_to_course, name='add_students_to_course'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('courses/<int:course_id>/students/', views.course_students, name='course_students'),
    path('qr-code/create/', views.create_qr_code, name='create_qr_code'),
    path('qr-code/validate/<int:qr_code_id>/', views.validate_qr_code, name='validate_qr_code'),
    path('scan-qr-code/', views.scan_qr_code, name='scan_qr_code'),
]
