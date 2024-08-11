from typing import Any, Mapping
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User,Group
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import *
from django import forms


class RegisterUser(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','username','email','password1','password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            students_group = Group.objects.get(name='Students')
            user.groups.add(students_group)
        return user
    

class FileUpload(forms.Form):
    file=forms.FileField()


class UpdateTestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields=['display_name','start_time','end_time','test_total_marks']
    
    def __init__(self,*args,**kwargs):
        super(UpdateTestForm,self).__init__(*args,**kwargs)

        MARKS_CHOICE=(
            (5,5),
            (10,10),
            (20,20)
        )
        
        if 'instance' in kwargs:
            instance= kwargs['instance']
            questions=instance.test_data.get('questions',[])
            for i,question in enumerate(questions):
                self.fields[f'question_{i}']=forms.CharField(
                    initial=question.get('question'),
                    label=f'question {i+1}'
                )
                for j,option in enumerate(question.get('options')):
                    self.fields[f'option_{i}_{j}']=forms.CharField(
                        initial=option,
                        label=f'option {j+1}'
                    )
                self.fields[f'correct_answer_{i}']=forms.CharField(
                    initial=question.get('correct_answer'),
                    label='correct answer'
                )
                self.fields[f'marks_{i}']=forms.ChoiceField(
                    choices=MARKS_CHOICE,
                    initial=question.get('marks'),
                    label=f'marks'
                )