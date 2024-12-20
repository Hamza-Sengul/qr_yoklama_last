from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Course
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
import qrcode
import io
from django.http import HttpResponse
from .models import QRCode, Attendance, AttendanceStatus
from django.utils.timezone import now
from django.http import JsonResponse
import json
from django.utils.timezone import now, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import os
from io import BytesIO
from django.db import models


def handle_attendance_after_login(request, qr_code):
    try:
        # Ders ve öğrenci bilgilerini al
        course = Course.objects.get(name=qr_code.course_name, code=qr_code.course_code)
        profile = Profile.objects.get(user=request.user)

        # Yoklama kaydını oluştur
        Attendance.objects.create(
            student=request.user,
            course=course,
            week=qr_code.week,
            scanned_at=now()
        )

        # AttendanceStatus güncelle veya oluştur
        attendance_status, created = AttendanceStatus.objects.get_or_create(
            course=course,
            week=qr_code.week,
            student=profile
        )
        attendance_status.is_present = True
        attendance_status.save()

    except Exception as e:
        print(f"Hata: {e}")



def home(request):
    return render(request, 'home.html')

from django.contrib import messages

def student_login(request):
    """
    Öğrenci giriş işlemleri.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)

            # QR kod doğrulama ile gelen giriş işlemini kontrol et
            qr_code_id = request.session.pop('qr_code_id', None)
            if qr_code_id:
                try:
                    qr_code = QRCode.objects.get(id=qr_code_id)
                    handle_attendance_after_login(request, qr_code)
                    messages.success(request, 'Yoklama başarıyla alındı!')
                    return redirect('attendance_logs')  # Yoklama geçmişine yönlendir
                except QRCode.DoesNotExist:
                    messages.error(request, 'Geçersiz QR kod.')
                    return redirect('student_dashboard')

            return redirect('student_dashboard')
        else:
            messages.error(request, 'E-posta veya şifre hatalı!')
    return render(request, 'student_login.html')


def student_register(request):
    """
    Öğrenci kayıt işlemleri, şifre doğrulama dahil.
    """
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        student_no = request.POST.get('student_no')
        department = request.POST.get('department')
        student_class = request.POST.get('class')

        # Eksik bilgi kontrolü
        if not all([first_name, last_name, email, password, password_confirm, student_no, department, student_class]):
            messages.error(request, 'Lütfen tüm alanları doldurun!')
        elif password != password_confirm:
            messages.error(request, 'Şifreler eşleşmiyor!')
        else:
            # Kullanıcı oluşturma
            user = User.objects.create_user(
                username=email, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            # Profil oluşturma
            Profile.objects.create(
                user=user,
                student_no=student_no,
                department=department,
                student_class=int(student_class)
            )
            messages.success(request, 'Kayıt başarılı! Giriş yapabilirsiniz.')
            return redirect('student_login')

    return render(request, 'student_register.html')

def user_logout(request):
    """
    Kullanıcı çıkış işlemleri.
    """
    logout(request)
    return redirect('home')


@login_required
def student_dashboard(request):
    user_profile = request.user.profile
    courses = Course.objects.filter(students=user_profile)
    attendance_data = []

    for course in courses:
        total_weeks = course.weeks
        attendance_limit = course.attendance_limit
        absences = AttendanceStatus.objects.filter(
            course=course,
            student=user_profile,
            is_present=False
        ).count()
        remaining_attendance = max(attendance_limit - absences, 0)

        # course_id'yi ekliyoruz
        attendance_data.append({
            'course_name': course.name,
            'course_code': course.code,
            'course_id': course.id,  # Bu satır önemli
            'total_weeks': total_weeks,
            'attendance_limit': attendance_limit,
            'absence_count': absences,
            'remaining_attendance': remaining_attendance
        })

    return render(request, 'student_dashboard.html', {
        'user': request.user,
        'attendance_data': attendance_data
    })

@login_required
def student_course_details(request, course_id):
    user_profile = request.user.profile
    try:
        course = Course.objects.get(id=course_id, students=user_profile)
    except Course.DoesNotExist:
        return render(request, '404.html', status=404)  # Hatalı erişim için

    absences = AttendanceStatus.objects.filter(
        course=course,
        student=user_profile,
        is_present=False
    ).count()

    return render(request, 'student_course_details.html', {
        'user': request.user,
        'course': course,
        'total_weeks': course.weeks,
        'attendance_limit': course.attendance_limit,
        'absence_count': absences,
        'remaining_attendance': max(course.attendance_limit - absences, 0),
    })

@login_required
def attendance_logs(request):
    logs = Attendance.objects.filter(student=request.user).order_by('-scanned_at')

    return render(request, 'attendance_logs.html', {
        'user': request.user,
        'logs': logs,
    })

def academician_login(request):
    """
    Akademisyen giriş işlemleri.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Kullanıcı doğrulama
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('academician_dashboard')  # Akademisyen paneline yönlendirme
        else:
            messages.error(request, 'E-posta veya şifre hatalı!')

    return render(request, 'academician_login.html')

def academician_register(request):
    """
    Akademisyen kayıt işlemleri.
    """
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Eksik bilgi kontrolü
        if not all([first_name, last_name, email, password, password_confirm]):
            messages.error(request, 'Lütfen tüm alanları doldurun!')
        elif password != password_confirm:
            messages.error(request, 'Şifreler eşleşmiyor!')
        elif User.objects.filter(username=email).exists():
            messages.error(request, 'Bu e-posta adresi zaten kayıtlı!')
        else:
            # Kullanıcı oluşturma
            user = User.objects.create_user(
                username=email, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            messages.success(request, 'Kayıt başarılı! Giriş yapabilirsiniz.')
            return redirect('academician_login')

    return render(request, 'academician_register.html')

def academician_dashboard(request):
    """
    Akademisyen paneli.
    """
    return render(request, 'academician_dashboard.html')

def student_list(request):
    """
    Bölümlerine ve sınıflarına göre öğrencileri listeleyen görünüm.
    """
    # Öğrencileri bölüm ve sınıflarına göre grupla
    departments = {}
    for profile in Profile.objects.all():
        department = profile.department
        student_class = profile.student_class

        # Departman ve sınıfları organize et
        if department not in departments:
            departments[department] = {}

        if student_class not in departments[department]:
            departments[department][student_class] = []

        departments[department][student_class].append(profile)

    return render(request, 'student_list.html', {'departments': departments})


@login_required
def create_course(request):
    """
    Ders oluşturma işlemi.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        weeks = request.POST.get('weeks')
        attendance_limit = request.POST.get('attendance_limit')
        department = request.POST.get('department')
        day_of_week = request.POST.get('day_of_week')

        # Eksik bilgi kontrolü
        if not all([name, code, weeks, attendance_limit, department, day_of_week]):
            messages.error(request, 'Lütfen tüm alanları doldurun!')
        else:
            # Ders oluşturma
            Course.objects.create(
                name=name,
                code=code,
                weeks=weeks,
                attendance_limit=attendance_limit,
                department=department,
                day_of_week=day_of_week,
                created_by=request.user,
            )
            messages.success(request, 'Ders başarıyla oluşturuldu!')
            return redirect('course_list')

    return render(request, 'create_course.html')

@login_required
def course_list(request):
    """
    Akademisyenin oluşturduğu derslerin listesi.
    """
    courses = Course.objects.filter(created_by=request.user)
    return render(request, 'course_list.html', {'courses': courses})

@login_required
def add_students_to_course(request, course_id):
    """
    Ders için öğrenci ekleme işlemi.
    """
    course = get_object_or_404(Course, id=course_id, created_by=request.user)

    # Öğrencileri bölümler ve sınıflara göre grupla
    grouped_students = {}
    for profile in Profile.objects.all():
        department = profile.department
        student_class = profile.student_class

        # Eğer bölüm yoksa yeni bir anahtar oluştur
        if department not in grouped_students:
            grouped_students[department] = {}

        # Eğer sınıf yoksa yeni bir liste oluştur
        if student_class not in grouped_students[department]:
            grouped_students[department][student_class] = []

        # Öğrenciyi ilgili sınıf listesine ekle
        grouped_students[department][student_class].append(profile)

    if request.method == 'POST':
        selected_students = request.POST.getlist('students')
        for student_id in selected_students:
            student = Profile.objects.get(id=student_id)
            course.students.add(student)

        messages.success(request, 'Öğrenciler başarıyla eklendi!')
        return redirect('course_list')

    return render(request, 'add_students_to_course.html', {
        'course': course,
        'grouped_students': grouped_students
    })



@login_required
def profile_settings(request):
    """
    Akademisyen profil ayarları.
    """
    if request.method == 'POST':
        # Profil bilgilerini güncelleme işlemleri
        pass
    return render(request, 'profile_settings.html')

@login_required
def course_students(request, course_id):
    """
    Akademisyenin oluşturduğu dersin kayıtlı öğrencilerini görüntüleme.
    """
    course = get_object_or_404(Course, id=course_id, created_by=request.user)
    students = course.students.all()  # Derse kayıtlı öğrenciler

    return render(request, 'course_students.html', {'course': course, 'students': students})


@login_required
def create_qr_code(request):
    """
    QR kod oluşturma işlemi.
    """
    if request.method == 'POST':
        # Formdan gelen verileri alın
        course_name = request.POST.get('course_name')
        course_code = request.POST.get('course_code')
        week = request.POST.get('week')
        valid_minutes = request.POST.get('valid_minutes', 3)  # Varsayılan süre: 3 dakika

        # Eksik bilgi kontrolü
        if not all([course_name, course_code, week]):
            messages.error(request, 'Lütfen tüm alanları doldurun!')
            return redirect('create_qr_code')

        try:
            # QR kodun geçerlilik süresini hesapla
            valid_until = now() + timedelta(minutes=int(valid_minutes))

            # QR kod modelini oluştur
            qr_code = QRCode.objects.create(
                course_name=course_name,
                course_code=course_code,
                week=week,
                valid_until=valid_until,
                generated_by=request.user
            )

            # Kullanıcıyı QR kod detay sayfasına yönlendir
            return redirect('qr_code_detail', qr_code_id=qr_code.id)

        except Exception as e:
            # Hata mesajını kullanıcıya göster
            messages.error(request, f'QR kod oluşturulurken bir hata oluştu: {e}')
            return redirect('create_qr_code')

    # Eğer GET isteği yapılmışsa, QR kod oluşturma formunu render et
    return render(request, 'create_qr_code.html')





# def validate_qr_code(request, qr_code_id):
#     """
#     Bu fonksiyon kaldırılabilir.
#     """
#     qr_code = QRCode.objects.get(id=qr_code_id)
#     if now() > qr_code.valid_until:
#         qr_code.is_expired = True
#         qr_code.save()
#         return HttpResponse("Bu QR kodun süresi dolmuştur.", status=400)
#     return HttpResponse("QR kod geçerli.", status=200)


import json

@login_required
def scan_qr_code(request):
    """
    QR kod okutma işlemi ve tabloya kaydetme.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_content = data.get('qr_content')

            if not qr_content:
                return JsonResponse({'status': 'error', 'message': 'QR kod verisi eksik.'})

            # QR kod içeriği bir URL mi kontrol et
            if qr_content.startswith("http"):
                # QR kod linkinden id'yi çıkar
                qr_code_id = qr_content.split('/validate-qr/')[-1].strip('/')
                qr_code = QRCode.objects.filter(id=qr_code_id).first()

                if not qr_code:
                    return JsonResponse({'status': 'error', 'message': 'Geçersiz QR kod. Kod sistemde bulunamadı.'})

                # Ders bilgilerini QR kod modelinden al
                course_name = qr_code.course_name
                course_code = qr_code.course_code
                week = qr_code.week
            else:
                # Eski düz metin formatını çözümle
                try:
                    course_name, course_code, week = qr_content.split(',')
                    week = int(week)
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'QR kod formatı geçersiz.'})

            # Ders kontrolü
            course = Course.objects.filter(name=course_name, code=course_code).first()
            if not course:
                return JsonResponse({'status': 'error', 'message': 'Geçersiz QR kod. Ders bulunamadı.'})

            # Yoklama kaydını oluştur
            profile = Profile.objects.get(user=request.user)
            Attendance.objects.create(
                student=request.user,
                course=course,
                week=week
            )
            attendance_status, created = AttendanceStatus.objects.get_or_create(
                course=course,
                week=week,
                student=profile
            )
            attendance_status.is_present = True
            attendance_status.save()

            return JsonResponse({'status': 'success', 'message': f"Yoklama başarıyla alındı ({course.name}, Hafta {week})."})

        except Exception as e:
            print(f"Hata: {e}")
            return JsonResponse({'status': 'error', 'message': 'Sunucu tarafında bir hata oluştu.'})

    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek.'})





@login_required
def attendance_overview(request):
    """
    Tüm yoklama kayıtlarını ders adı ve hafta bazında listele.
    """
    courses = Course.objects.filter(created_by=request.user)
    attendance_data = Attendance.objects.filter(course__in=courses).values(
        'course__name', 'week'
    ).annotate(total_students=models.Count('id'))

    return render(request, 'attendance_overview.html', {'attendance_data': attendance_data})




@login_required
def attendance_details(request, course_name, week):
    """
    Belirli bir ders ve hafta için tüm öğrencilerin yoklama durumunu listele.
    """
    course = get_object_or_404(Course, name=course_name, created_by=request.user)
    registered_students = course.students.all()

    # Tüm öğrencilerin yoklama durumlarını al
    attendance_statuses = AttendanceStatus.objects.filter(course=course, week=week)

    student_attendance = []
    for student in registered_students:
        status = attendance_statuses.filter(student=student).first()
        student_attendance.append({
            'first_name': student.user.first_name,
            'last_name': student.user.last_name,
            'student_no': student.student_no,
            'is_present': status.is_present if status else False,  # Varsayılan False
        })

    return render(request, 'attendance_details.html', {
        'course': course,
        'week': week,
        'student_attendance': student_attendance
    })



from django.conf import settings

pdfmetrics.registerFont(TTFont('FreeSans', 'static/fonts/FreeSans.ttf'))

@login_required
def download_attendance_pdf(request, course_name, week):
    """
    PDF olarak yoklama listesini indir.
    """
    course = get_object_or_404(Course, name=course_name, created_by=request.user)
    registered_students = course.students.all()

    # Tüm öğrencilerin mevcut durumunu alın
    attendance_statuses = AttendanceStatus.objects.filter(course=course, week=week)

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)

    # PDF başlığı ve tablosu için veriler
    title = f"{course.name} - Hafta {week} Yoklama Listesi"
    data = [["Ad", "Soyad", "Okul No", "Durum"]]

    for student in registered_students:
        status = attendance_statuses.filter(student=student).first()
        is_present = "Mevcut" if status and status.is_present else "Mevcut Değil"
        data.append([
            student.user.first_name,
            student.user.last_name,
            student.student_no,
            is_present
        ])

    # Tablo stili ve düzeni
    table = Table(data, colWidths=[100, 100, 100, 100])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'FreeSans'),  # Türkçe karakter desteği için
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
    ]))

    elements = []
    elements.append(Table([[title]], style=[
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'FreeSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20)
    ]))
    elements.append(table)

    pdf.build(elements)
    buffer.seek(0)

    # PDF adını dinamik olarak oluşturun
    filename = f"{course.name.replace(' ', '_')}_Hafta_{week}_Yoklama_Listesi.pdf"

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response



@login_required
def finalize_attendance(request, qr_code_id):
    """
    Yoklamayı sonlandır ve tüm öğrenciler için mevcut/mevcut değil durumunu güncelle.
    """
    qr_code = get_object_or_404(QRCode, id=qr_code_id, generated_by=request.user)

    # QR kodu süresi dolmuş olarak işaretle
    qr_code.is_expired = True
    qr_code.save()

    # QR kod bilgilerine göre ders ve öğrencileri al
    course = get_object_or_404(Course, name=qr_code.course_name, code=qr_code.course_code)
    registered_students = course.students.all()

    # QR kodu okutan öğrencileri al
    attended_students = Attendance.objects.filter(course=course, week=qr_code.week).values_list('student', flat=True)

    # Tüm öğrenciler için mevcut/mevcut değil durumunu belirle ve kaydet
    for student in registered_students:
        attendance_status, created = AttendanceStatus.objects.get_or_create(
            course=course,
            week=qr_code.week,
            student=student
        )
        # QR kodu okutanlar mevcut, diğerleri mevcut değil
        attendance_status.is_present = student.user.id in attended_students
        attendance_status.save()

    messages.success(request, "Yoklama başarıyla sonlandırıldı ve tüm durumlar güncellendi!")
    return redirect('academician_dashboard')


@login_required
def qr_code_detail(request, qr_code_id):
    """
    QR Kod detay sayfası.
    """
    qr_code = get_object_or_404(QRCode, id=qr_code_id, generated_by=request.user)
    return render(request, 'qr_code_detail.html', {'qr_code': qr_code})

def qr_code_image(request, qr_code_id):
    qr_code = get_object_or_404(QRCode, id=qr_code_id)
    qr_content = qr_code.get_qr_content()  # Dinamik URL içeriği alınıyor

    qr_image = qrcode.make(qr_content)
    buffer = io.BytesIO()
    qr_image.save(buffer)
    buffer.seek(0)

    return HttpResponse(buffer, content_type='image/png')


import logging
from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib import messages

# Logger oluştur
logger = logging.getLogger(__name__)

def custom_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            # Kullanıcıyı e-posta adresine göre al
            user = User.objects.get(email=email)

            # Token ve UID oluştur
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # E-posta bağlantısı için ayarlar
            domain = 'tarsusuniversitesiqryoklama.online'
            protocol = 'https'

            # E-posta içeriğini oluştur
            subject = 'Şifre Sıfırlama Talebi'
            try:
                html_content = render_to_string('password_reset_email.html', {
                    'protocol': protocol,
                    'domain': domain,
                    'uid': uid,
                    'token': token,
                })
            except Exception as e:
                logger.error("Şablon oluşturma hatası: %s", e)
                raise

            # E-posta gönderimi
            try:
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body='',  # Düz metin içeriği (HTML kullanıldığı için boş bırakılabilir)
                    from_email='no-reply@tarsusuniversitesiqryoklama.online',
                    to=[email]
                )
                email_message.attach_alternative(html_content, "text/html")
                email_message.send()
            except Exception as e:
                logger.error("E-posta gönderim hatası: %s", e)
                raise

            # Başarılı mesaj ve yönlendirme
            messages.success(request, 'Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.')
            return redirect('password_reset_done')

        except User.DoesNotExist:
            # Kullanıcı bulunamazsa hata mesajı
            messages.error(request, 'Bu e-posta adresiyle eşleşen bir kullanıcı bulunamadı.')

    # Şifre sıfırlama formunu göster
    return render(request, 'password_reset.html')


    # Şifre sıfırlama formunu göster
    return render(request, 'password_reset.html')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages

def validate_qr_and_redirect(request, qr_code_id):
    """
    QR kodu doğrulayıp kullanıcıyı yönlendirir.
    """
    try:
        qr_code = QRCode.objects.get(id=qr_code_id)

        # Kullanıcı giriş yapmamışsa giriş sayfasına yönlendir
        if not request.user.is_authenticated:
            request.session['qr_code_id'] = qr_code_id  # QR kod bilgisini sakla
            return redirect('student_login')  # Giriş sayfasına yönlendir

        # Kullanıcı giriş yapmışsa yoklamayı kaydet
        handle_attendance_after_login(request, qr_code)
        messages.success(request, 'Yoklama başarıyla alındı!')
        return redirect('attendance_logs')  # Yoklama geçmişine yönlendir

    except QRCode.DoesNotExist:
        return render(request, 'invalid_qr.html', status=400)



