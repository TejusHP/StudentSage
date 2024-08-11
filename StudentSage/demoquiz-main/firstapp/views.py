from typing import Any
from django.forms import BaseModelForm
from django.shortcuts import render,redirect,HttpResponse
from .forms import *
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin,LoginRequiredMixin
from .models import *
from firstapp import rag
from django.db.models import Sum,Count,Max,Min,Avg
from django.http import FileResponse
from django.views.generic import CreateView,UpdateView,DeleteView,DetailView,ListView,TemplateView
import os
from django.utils.dateparse import parse_datetime
from django.conf import settings
from django.utils import timezone
from django.urls import reverse_lazy


# Create your views here.
def user_register(request):
    RegisterForm=RegisterUser()
    if request.method=='POST':
        RegisterForm=RegisterUser(request.POST)
        if RegisterForm.is_valid():
            RegisterForm.save()
            return redirect('firstapp:login')
        
    return render(request,'firstapp/register.html',{'RegisterForm':RegisterForm})

def user_login(request):
    if request.method=='POST':
        username=request.POST.get('username')
        password=request.POST.get('password1')
        user=authenticate(username=username,password=password)
        if user is not None:
            login(request,user)
            if user.groups.filter(name='Teacher').exists():
                    teacher = Teacher.objects.get(name=user)
                    return redirect('firstapp:teacher_detail', pk=teacher.pk)
            elif user.groups.filter(name='Students').exists():
                try:
                    student = Students.objects.get(name=user) 
                    return redirect('firstapp:detail-student', pk=student.pk)
                except Students.DoesNotExist:
                    return HttpResponse("Your account is successfully registered, but you are not yet added to the classroom.")
    return render(request,'firstapp/login.html')

@login_required
def home(request):
    user=request.user
    if user.groups.filter(name='Teacher').exists():
                teacher = Teacher.objects.get(name=user)
                return redirect('firstapp:teacher_detail', pk=teacher.pk)
    elif user.groups.filter(name='Students').exists():
        try:
            student = Students.objects.get(name=user)
            return redirect('firstapp:detail-student', pk=student.pk)
        except Students.DoesNotExist:
            return HttpResponse("Your account is successfully registered, but you are not yet added to the classroom.")

@login_required
def user_logout(request):
    logout(request)
    return redirect('firstapp:login')


class addStudent(LoginRequiredMixin,PermissionRequiredMixin,CreateView):
    permission_required='firstapp.add_students'
    model=Students
    fields={'name'}
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        teacher = Teacher.objects.get(name=self.request.user)
        form.instance.teacher=teacher
        return super().form_valid(form)

class deleteStudent(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    permission_required='firstapp.add_students'
    model=Students
    success_url=reverse_lazy('firstapp:home')
    

class teacherdata(LoginRequiredMixin,PermissionRequiredMixin,ListView):
    permission_required='firstapp.add_students'
    model=Teacher
    context_object_name='teachers'

class teacherdetail(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    permission_required='firstapp.add_students'
    model=Teacher
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context= super().get_context_data(**kwargs)
        context['now']=timezone.now().isoformat()
        print(type(timezone.now()))
        return context

class studentdetail(LoginRequiredMixin,DetailView):
    model=Students

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context=super().get_context_data(**kwargs)
        student=self.get_object()
        tests=TestAttempt.objects.filter(student=student)
        attempted_tests = [attempt.test.id for attempt in tests]
        context["attempted_tests"]=attempted_tests
        return context


class studentUpdate(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    permission_required='firstapp.change_students'
    model=Students
    fields={'description'}
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.name=self.request.user
        return super().form_valid(form)


def handle_uploaded_file(f):
    with open('modelrev2/media/documents/'+f.name, 'wb+') as destination:   
        for chunk in f.chunks(): 
            destination.write(chunk)  
    rag.start_embedding('modelrev2/media/documents/'+f.name)
    return f.name


def upload_file(request):
    if request.method=='POST':
        form=FileUpload(request.POST,request.FILES)
        if form.is_valid():
            file_path=handle_uploaded_file(request.FILES["file"])
            request.session['uploaded_file_path'] = file_path
            return redirect('firstapp:user-input')
    else:
        form=FileUpload()
    return render(request,'firstapp/upload_file.html',{'form':form})


def ask_question(request):
    if request.method=='POST':
        question=request.POST.get('question')
        request.session['title_quiz']=request.POST.get('title_quiz')
        request.session['datetime_start']=request.POST.get('datetime_start')
        request.session['datetime_end']=request.POST.get('datetime_end')
        return redirect('firstapp:quiz', question=question)
    return render(request,"firstapp/ask_question.html")


class deleteTest(LoginRequiredMixin,PermissionRequiredMixin,DeleteView):
    permission_required='firstapp.add_students'
    model=Test
    success_url=reverse_lazy('firstapp:home')


class updateTest(LoginRequiredMixin,PermissionRequiredMixin,UpdateView):
    permission_required='firstapp.add_students'
    model=Test
    form_class=UpdateTestForm
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form_data = form.save(commit=False)
        questions = form_data.test_data.get('questions')
        data=form_data.test_total_marks
        print(data)
        for i in range(len(questions)):
            questions[i][f'question'] = form.cleaned_data.get(f'question_{i}')
            questions[i]['correct_answer'] = form.cleaned_data.get(f'correct_answer_{i}')
            questions[i][f'marks'] = form.cleaned_data.get(f'marks_{i}')
            if questions[i][f'marks'] == 5:
                questions[i][f'difficulty']='Easy'
            elif questions[i][f'marks'] == 10:
                questions[i][f'difficulty']='Medium'
            elif questions[i][f'marks'] == 20:
                questions[i][f'difficulty']='Hard'
            for j in range(len(questions[i]['options'])):
                questions[i]['options'][j]=form.cleaned_data.get(f'option_{i}_{j}')
        form_data.test_total_marks=rag.calculate_total_marks({'questions':questions})
        print(form_data.test_total_marks)
        form.save()
            
        return super().form_valid(form)
    
@login_required
@permission_required('firstapp.add_students')
def original_test_view(request,test_id):
    test=Test.objects.get(id=test_id)

    return render(
        request,
        'firstapp/preview_teacher_test.html',
        context={'test':test}
    )


@login_required
def quiz(request,question):
    if request.method=='GET':
        request.session['test_name']=question
        question_list=rag.generate_quiz(question)
        request.session['gen_ques']=question_list

        teacher,_=Teacher.objects.get_or_create(name=request.user)
        test=Test.objects.create(
            teacher=teacher,
            test_name=request.session.get('test_name'),
            display_name=request.session.get('title_quiz'),
            start_time=request.session.get('datetime_start'),
            end_time=request.session.get('datetime_end'),
            test_total_marks=rag.calculate_total_marks(request.session.get('gen_ques')),
            test_data=request.session.get('gen_ques'),
            file_path=request.session.get('uploaded_file_path')
        )
        del request.session['uploaded_file_path']
        del request.session['test_name']
        del request.session['title_quiz']
        del request.session['datetime_start']
        del request.session['datetime_end']
        del request.session['gen_ques']
        return redirect('firstapp:test_formation',test_id=test.id)
    

def attend_quiz(request,test_id):
    student,_=Students.objects.get_or_create(name=request.user)
    if request.method=='GET':
        test=Test.objects.get(id=test_id)
        TestAttempt.objects.create(
            student=student,
            test=test,
            attempt_start=timezone.now()
        )
        
        return render(request,"firstapp/quiz.html",context={'test':test,'test_mode':'one'})
    elif request.method == 'POST':
        submitted_data=request.POST
        test=Test.objects.get(id=test_id)
        test_attempt=TestAttempt.objects.get(student_id=student.id,test_id=test.id)
        test_attempt.attempt_end=timezone.now()
        question_list=test.test_data
        obtained_marks=0
        topicstags=[]
        for i in range(1,len(question_list['questions'])+1):
            if 'question--'+str(i) in submitted_data:
                question_list['questions'][i-1].update({'answer_given_value':submitted_data['question--'+str(i)]})
                if submitted_data['question--'+str(i)] == question_list['questions'][i-1]['correct_answer']:
                    question_list['questions'][i-1].update({'answer_given':'correct'})
                    obtained_marks+=int(question_list['questions'][i-1]['marks'])
                else:
                    question_list['questions'][i-1].update({'answer_given':'incorrect'})
                    for i in question_list['questions'][i-1]['tags']:
                        if i not in topicstags:
                            topicstags.append(i)
                            Topics.objects.create(
                                student=student,
                                topic=i,
                                test=test
                            )
            else:
                question_list['questions'][i-1].update({'answer_given':'unattempted'})
                for i in question_list['questions'][i-1]['tags']:
                    if i not in topicstags:
                        topicstags.append(i)
                        Topics.objects.create(
                            student=student,
                            topic=i,
                            test=test
                        )
        test_marks=test.test_total_marks
        test_attempt.Submitted_data=question_list['questions']
        test_attempt.test_marks=obtained_marks
        test_attempt.save()

        result_status=rag.count_result_status(question_list)

        return render(
            request,'firstapp/result_page.html',
                    {
                        'marks_obtained':obtained_marks,
                        'total_marks': test_marks,
                        'questions':question_list['questions'],
                        'preview':None,
                        'student_pk':student.name.pk,
                        'correct_count':result_status[0],
                        'incorrect_count':result_status[1],
                        'unattempted_count':result_status[2]
                    }
            )
    

def preview_test(request,id,stud_id):
    student,_=Students.objects.get_or_create(id=stud_id)
    test_master=Test.objects.get(id=id)
    test=TestAttempt.objects.get(student_id=student.id,test_id=id)
    topic_tags=Topics.objects.filter(test=test_master,student=student)
    
    result_status=rag.count_result_status({'questions':test.Submitted_data})

    return render(
        request,
        'firstapp/result_page.html',
        {
            'marks_obtained':test.test_marks,
            'total_marks': test_master.test_total_marks,
            'questions':test.Submitted_data,
            'preview':None,
            'student':student,
            'start_time':test.attempt_start,
            'end_time':test.attempt_end,
            'test_mode':'one',
            'tags':topic_tags,
            'correct_count':result_status[0],
            'incorrect_count':result_status[1],
            'unattempted_count':result_status[2]
        }
    )


def download_file(request,file_path):
    file_abs_path = 'modelrev2/media/documents/'+file_path
    file= FileResponse(open(file_abs_path,'rb'))
    file['Content-Disposition'] = f'attachment; filename="{file_path}"'
    return file


def rectification_quiz(request,topic_id):
    student,_=Students.objects.get_or_create(name=request.user)
    if request.method=='GET':
        topic=Topics.objects.get(id=topic_id,student_id=student.id)
        test=Test.objects.get(id=topic.test_id)
        rag.start_embedding('modelrev2/media/documents/'+test.file_path)
        question_list=rag.generate_quiz("generate 15 questions with 7 questions easy, 5 questions medium and 3 questions hard level on "+topic.topic+" to master this topic")
        request.session['gen_ques']=question_list
        test={
            'test_data':question_list,
            'test_mode':'two'
        }
        return render(request,"firstapp/quiz.html",context={'test':test})
    elif request.method == 'POST':
        submitted_data=request.POST
        question_list=request.session.get('gen_ques')
        obtained_marks=0
        for i in range(1,len(question_list['questions'])+1):
            if 'question--'+str(i) in submitted_data:
                question_list['questions'][i-1].update({'answer_given_value':submitted_data['question--'+str(i)]})
                if submitted_data['question--'+str(i)] == question_list['questions'][i-1]['correct_answer']:
                    question_list['questions'][i-1].update({'answer_given':'correct'})
                    obtained_marks+=int(question_list['questions'][i-1]['marks'])
                else:
                    question_list['questions'][i-1].update({'answer_given':'incorrect'})
            else:
                question_list['questions'][i-1].update({'answer_given':'unattempted'})
        test_marks=rag.calculate_total_marks(question_list)
        result_status=rag.count_result_status(question_list)

        if obtained_marks/test_marks>0.8:
            Topics.objects.filter(id=topic_id).delete()
        return render(
            request,'firstapp/result_page.html',
                    {
                        'marks_obtained':obtained_marks,
                        'total_marks': test_marks,
                        'questions':question_list['questions'],
                        'preview':None,
                        'student_pk':student.name.pk,
                        'test_mode':'two',
                        'correct_count':result_status[0],
                        'incorrect_count':result_status[1],
                        'unattempted_count':result_status[2]
                    }
            )



class Test_View(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    permission_required='firstapp.add_students'
    template_name='firstapp/test_view.html'
    model=Test
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context= super().get_context_data(**kwargs)
        context["students"]=Students.objects.filter(
            test_history__test=self.object,
        )
        context["test"]=self.object
        context["average"]=TestAttempt.objects.filter(test=self.object).aggregate(Avg('test_marks'))['test_marks__avg']
        return context
    
def react_chatbot(request):
    student,_=Students.objects.get_or_create(name=request.user)
    context={
        'student_id':student.id,
        'student_name':student.name
    }
    return render(request,'firstapp/chatbot.html',context=context)

def base_url(request):
    return request.build_absolute_uri()