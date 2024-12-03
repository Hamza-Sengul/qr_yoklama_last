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
from .models import QRCode, Attendance
from django.utils.timezone import now
from django.http import JsonResponse
import json
from django.utils.timezone import now, timedelta

def home(request):
    return render(request, 'home.html')

def student_login(request):
    """
    Öğrenci giriş işlemleri.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Kullanıcı doğrulama
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('student_dashboard')  # Öğrenci paneline yönlendir
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
    """
    Giriş yapmış öğrencilere özel öğrenci paneli.
    """
    return render(request, 'student_dashboard.html', {'user': request.user})



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
    course = Course.objects.get(id=course_id, created_by=request.user)
    students = Profile.objects.all()

    if request.method == 'POST':
        selected_students = request.POST.getlist('students')
        for student_id in selected_students:
            student = Profile.objects.get(id=student_id)
            course.students.add(student)

        messages.success(request, 'Öğrenciler başarıyla eklendi!')
        return redirect('course_list')

    return render(request, 'add_students_to_course.html', {'course': course, 'students': students})

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
    QR Kod oluşturma işlemi.
    """
    if request.method == 'POST':
        course_name = request.POST.get('course_name')
        course_code = request.POST.get('course_code')
        week = request.POST.get('week')

        # Eksik bilgi kontrolü
        if not all([course_name, course_code, week]):
            messages.error(request, 'Lütfen tüm alanları doldurun!')
            return redirect('create_qr_code')

        # QR kod içeriğini birleştir
        qr_content = f"{course_name},{course_code},{week}"

        # QR kod oluştur
        qr_image = qrcode.make(qr_content)
        buffer = io.BytesIO()
        qr_image.save(buffer)
        buffer.seek(0)

        # QR kodu ekranda göster
        response = HttpResponse(buffer, content_type='image/png')
        response['Content-Disposition'] = 'inline; filename=qr_code.png'
        return response

    return render(request, 'create_qr_code.html')

@login_required
def validate_qr_code(request, qr_code_id):
    """
    QR Kod geçerlilik kontrolü.
    """
    qr_code = QRCode.objects.get(id=qr_code_id)
    if now() > qr_code.valid_until:
        qr_code.is_expired = True
        qr_code.save()
        return HttpResponse("Bu QR kodun süresi dolmuştur.", status=400)
    return HttpResponse("QR kod geçerli.", status=200)

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

            # QR kod içeriğini parçala
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
            try:
                Attendance.objects.create(
                    student=request.user,
                    course=course,
                    week=week
                )
                return JsonResponse({'status': 'success', 'message': f"Yoklama başarıyla alındı ({course.name}, Week {week})."})
            except Exception as e:
                print(f"Hata: {e}")
                return JsonResponse({'status': 'error', 'message': 'Yoklama kaydedilirken bir hata oluştu.'})

        except Exception as e:
            print(f"Hata: {e}")
            return JsonResponse({'status': 'error', 'message': 'Sunucu tarafında bir hata oluştu.'})

    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek.'})







