from django.contrib import admin
from .models import Profile, Course, QRCode, Attendance

admin.site.register(Course)
admin.site.register(QRCode)
admin.site.register(Attendance)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_no', 'department', 'student_class')
