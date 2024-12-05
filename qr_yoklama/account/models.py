from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now, timedelta

class Profile(models.Model):
    """
    Kullanıcıya özel profil bilgileri.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_no = models.CharField(max_length=10)
    department = models.CharField(max_length=100)
    student_class = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')])

    def __str__(self):
        return self.user.username


class Course(models.Model):
    """
    Ders modeli.
    """
    DAYS_OF_WEEK = [
        ('Monday', 'Pazartesi'),
        ('Tuesday', 'Salı'),
        ('Wednesday', 'Çarşamba'),
        ('Thursday', 'Perşembe'),
        ('Friday', 'Cuma'),
        ('Saturday', 'Cumartesi'),
        ('Sunday', 'Pazar'),
    ]

    name = models.CharField(max_length=255)  # Ders adı
    code = models.CharField(max_length=50, unique=True)  # Ders kodu
    weeks = models.PositiveIntegerField()  # Dersin kaç hafta süreceği
    attendance_limit = models.PositiveIntegerField()  # Yoklama sınırı
    department = models.CharField(max_length=255)  # Bağlantılı olduğu bölüm
    day_of_week = models.CharField(max_length=15, choices=DAYS_OF_WEEK)  # Haftanın günü
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Dersi oluşturan akademisyen
    students = models.ManyToManyField('Profile', blank=True)  # Dersi alan öğrenciler

    def __str__(self):
        return f"{self.name} ({self.code})"


from django.utils.timezone import now, timedelta

class QRCode(models.Model):
    course_name = models.CharField(max_length=255)  # Ders adı
    course_code = models.CharField(max_length=50)  # Ders kodu
    week = models.PositiveIntegerField()  # Hafta bilgisi
    created_at = models.DateTimeField(auto_now_add=True)  # Oluşturulma zamanı
    valid_until = models.DateTimeField()  # Geçerlilik süresi
    is_expired = models.BooleanField(default=False)  # Süre doldu mu?
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)  # QR kodu oluşturan akademisyen

    def check_expiration(self):
        """Süresinin dolup dolmadığını kontrol et."""
        if not self.is_expired and now() > self.valid_until:
            self.is_expired = True
            self.save()

    def save(self, *args, **kwargs):
        """Save sırasında süresi dolduysa güncelle."""
        self.check_expiration()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course_name} - {self.course_code} (Hafta: {self.week})"





class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    week = models.PositiveIntegerField()
    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course', 'week'], name='unique_attendance'
            )
        ]

    def __str__(self):
        return f"{self.student.username} - {self.course.name} (Week {self.week})"


class AttendanceStatus(models.Model):
    """
    Öğrencilerin yoklama durumunu saklayan model.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE)  # Ders
    week = models.PositiveIntegerField()  # Hafta
    student = models.ForeignKey('Profile', on_delete=models.CASCADE)  # Öğrenci
    is_present = models.BooleanField(default=False)  # Katılım durumu

    class Meta:
        unique_together = ('course', 'week', 'student')  # Aynı ders, hafta ve öğrenci için tek kayıt

