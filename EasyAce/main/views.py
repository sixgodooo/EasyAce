from django.shortcuts import render
from myAuth.models import Tutor,MyUser,Student,PreferSubject,ReferSubject,StudentPreferSub
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from itertools import chain
from django.http import JsonResponse
import json
# Create your views here.

def index(request):
    return render(request, 'index.html')
def information_tutor(request,id):
    tutors = Tutor.objects.filter(id=id)
    print(tutors)
    return render(request, 'information_tutor.html', {'tutors':tutors})
def information(request,id):
    try:
        user = MyUser.objects.get(pk=id)
    except ObjectDoesNotExist:
        messages.error(request,'User does not exist!')
        return HttpResponseRedirect('/index')
    if user.role=='tutor':
        tutor = user.get_user()
        if not tutor:
            if user==request.user:
                messages.warning(request,'Please complete your information first!')
                return HttpResponseRedirect(reverse('myAuth:signup_tutor'))
            messages.warning(request,'User didn\'t finish his/her information yet!')
            return HttpResponseRedirect('/index')
        if request.user.role=='student':
            student = request.user.get_user()
            return render(request, 'information_tutor.html', {'tutor':tutor,'student':student})
        return render(request, 'information_tutor.html', {'tutor':tutor})
    elif user.role=='student':
        student = user.get_user()
        if not student:
            if user==request.user:
                messages.warning(request,'Please complete your information first!')
                return HttpResponseRedirect(reverse('myAuth:signup_student'))
            messages.warning(request,'User didn\'t finish his/her information yet!')
            return HttpResponseRedirect('/index')
        return render(request, 'information_student.html', {'student':student})
    else:
        messages.error(request,'User didn\'t finish his/her information yet!')
        return HttpResponseRedirect('/index')

def view_tutor(request):
  region = request.GET.get('region')
  level = request.GET.get('level')
  subject = request.GET.get('subject')
  subject_other = request.GET.get('subject_other')
  gender = request.GET.get('gender')
  tutors = Tutor.objects.filter(check=True)
  if region:
    region1 = tutors.filter(region1__contains=region)
    region2 = tutors.filter(region2__contains=region)
    region3 = tutors.filter(region3__contains=region)
    tutors = region1 | region2 | region3
  if level:
    if subject and not subject=='Other':
      tutors = tutors.filter(prefer_teach__contains=subject)
    if subject and subject=='Other':
      tutors = tutors.filter(teaching_sub_other__contains=subject_other)
    else:
      tutors = tutors.filter(prefer_teach__contains=level)
  if gender:
    tutors = tutors.filter(gender=gender)
  return render(request, 'view_tutor.html', {'tutors':tutors})

def choose_tutor(request):
    if request.method == 'POST' and 'tutor_id' in request.POST:
        tutor_id = request.POST['tutor_id']
        user = request.user
        student = user.get_user()
        tutor = MyUser.objects.get(pk=tutor_id).get_user()
        if not student:
            messages.warning(request,'Please complete your info first.')
            return HttpResponseRedirect(reverse('myAuth:signup_student'))
        print('here')
        student.tutors_chosen.add(tutor)
        student.save()
        data = {'added':True}
        return JsonResponse(data)
    else:
        return HttpResponseRedirect(reverse('main:index'))
def edit(request):
    user = request.user
    # if the user is a tutor.
    if user.role=='tutor':
        # if post the form, update the information
        if request.method == 'POST':
            tutor = user.get_user()
            #### Base info start
            tutor.name = request.POST['name']
            tutor.gender = request.POST['gender']
            tutor.birth = request.POST['birthday']
            tutor.email = request.POST['email']
            tutor.phone = request.POST['phone']
            tutor.school = request.POST['school']
            tutor.wechat = request.POST['wechat']
            tutor.whatsapp = request.POST['whatsapp']
            #### Base info end

            #### Profile start
            tutor.teach_duration = request.POST['teach_duration']
            tutor.num_taught = request.POST['num_taught']
            tutor.achievement = request.POST['achievement']
            #### Profile end

            #### Option fields start
            user.email = request.POST['email']
            user.save()
            if 'photo' in request.FILES:
                tutor.photo = request.FILES['photo']
            if 'tutor_location_1' in request.POST:
                tutor.tutor_location1 = request.POST['tutor_location_1']
            if 'tutor_location_2' in request.POST:
                tutor.tutor_location2 = request.POST['tutor_location_2']
            if 'tutor_location_3' in request.POST:
                tutor.tutor_location3 = request.POST['tutor_location_3']
            tutor.save()
            #### Option fields end

            #### Start create prefer teach and refer teach 
            for sub in tutor.prefer_subs.all():
                sub.delete()
            for sub in tutor.refer_subs.all():
                sub.delete()
            for i in range(1,10):
                if 'teach_level'+str(i) in request.POST:
                    level = request.POST['teach_level'+str(i)]
                    name = request.POST['teach_sub'+str(i)]
                    other = False
                    if name == "Other":
                        name = request.POST['teach_sub_other'+str(i)]
                        other = True
                    prefer_teach = PreferSubject(level=level,name=name,rank=i,other=other,\
                        tutor=tutor)
                    prefer_teach.save()
                if 'ref_level'+str(i) in request.POST:
                    level = request.POST['ref_level'+str(i)]
                    name = request.POST['ref_sub'+str(i)]
                    other = False
                    if name == "Other":
                        name = request.POST['ref_sub_other'+str(i)]
                        other = True
                    score = request.POST['ref_score'+str(i)]
                    refer_teach = ReferSubject(level=level,name=name,score=score,rank=i,\
                        other=other,tutor=tutor)
                    refer_teach.save()
            #### END
            tutor.cal_isr()
            print(tutor.isr)
            tutor.save()
            messages.success(request,'Update information successfully!')
            return HttpResponseRedirect(reverse('main:information',kwargs={'id':user.id}))
            # End update information
        # if the method is GET, offer old information
        else:
            tutor = user.get_user()
            if tutor:
                return render(request,'signup_tutor.html',{'tutor':tutor,'edit':True})
            return HttpResponseRedirect(reverse('myAuth:signup_tutor'))
    # the user is a student
    else:
        # If post the form, update student info.
        if request.method == 'POST':
            student = user.get_user()
            #### Base info start
            student.name = request.POST['name']
            student.gender = request.POST['gender']
            student.email = request.POST['email']
            student.phone = request.POST['phone']
            student.school = request.POST['school']
            student.grade = request.POST['grade']
            student.wechat = request.POST['wechat']
            student.whatsapp = request.POST['whatsapp']
            #### Base info end

            #### Preference start
            student.location = request.POST['student_location']
            student.loc_nego = request.POST['student_location_negotiable']
            student.time_per_lesson = request.POST['student_duration_per_lesson']
            student.lesson_per_week = request.POST['student_lesson_per_week']
            student.start_time = request.POST['student_start_time']
            student.prefer_tutor_gender = request.POST['student_tutor_preference']
            #### Preference end

            #### Option fields start
            user.email = request.POST['email']
            user.save()
            if request.POST['student_start_time']=='Other':
                student.start_time_other = request.POST['student_start_time_other']
            remarks=''
            prefix = 'student_remark'
            for i in range(1,7):
                if prefix+str(i) in request.POST:
                    remarks+=request.POST[prefix+str(i)]
                    remarks+=';'
            student.remarks=remarks
            if 'student_weakness' in request.POST:
                student.weakness = request.POST['student_weakness']
            student.save()
            #### Option fields end

            #### Start create prefer teach and refer teach
            student_subject = request.POST['student_subject']
            for sub in student.prefer_subs.all():
                sub.delete() 
            for i in range(1,10):
                if 'student_subject'+str(i) in request.POST:
                    name = request.POST['student_subject'+str(i)]
                    other = False
                    if name == "Other":
                        name = request.POST['student_subject'+str(i)+'_other']
                        other = True
                    prefer_sub = StudentPreferSub(level=student_subject,name=name,rank=i,other=other,\
                        student=student)
                    prefer_sub.save()
            #### END
            messages.success(request,'Update information successfully!')
            return HttpResponseRedirect(reverse('main:information',kwargs={'id':user.id}))
        # if method is GET
        else:
            student = user.get_user()
            if student:
                return render(request,'signup_student.html',{'student':student,'edit':True})
            return HttpResponseRedirect(reverse('myAuth:signup_student'))

def edit_student(request):
    user = request.user
    if request.method == 'POST':
        student = user.get_user()
        subjects = student.get_single('subjects')
        subjects_other = student.get_single('subjects_other')
        exam_type = student.exam_type
        data = {}
        data["exam_type"] = exam_type
        data['subjects'] = subjects
        data['subjects_other'] = subjects_other
        data_json = json.dumps(data)
        print(data_json)
        return JsonResponse(data_json, safe=False)

def edit_tutor(request):
    user = request.user
    if request.method == 'POST':
        tutor = user.get_user()
        middle_test = tutor.middle_test
        high_test = tutor.high_test
        middle_test_score = tutor.get_pairs('middle_test_score')
        high_test_score = tutor.get_pairs('high_test_score')
        prefer_teach = tutor.get_prefer_teach()
        middle_sub_other = tutor.get_triple('middle_sub_other')
        high_sub_other = tutor.get_triple('high_sub_other')
        teaching_sub_other = tutor.get_triple('teaching_sub_other')

        data = {}
        data["middle_test"] = middle_test
        data["high_test"] = high_test
        data["middle_test_score"] = middle_test_score
        data["high_test_score"] = high_test_score
        data["prefer_teach"] = prefer_teach
        data["middle_sub_other"] = middle_sub_other
        data["high_sub_other"] = high_sub_other
        data["teaching_sub_other"] = teaching_sub_other
        data_json = json.dumps(data)
        print(data_json)
        return JsonResponse(data_json, safe=False)





