from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Category, Organization, Adherent, Interaction

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'matricule', 'name', 'profession', 'telephone', 'role', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded'}),
            'matricule': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'profession': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'telephone': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'role': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4}),
        }

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'monthly_revenue', 'address', 'creation_date', 'phone', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'monthly_revenue': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'}),
            'address': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4}),
            'creation_date': forms.DateInput(attrs={'class': 'w-full p-2 border rounded', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'category': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
        }

class AdherentForm(forms.ModelForm):
    class Meta:
        model = Adherent
        fields = [
            'identifiant', 'first_name', 'last_name', 'type_adherent', 'address',
            'phone1', 'phone2', 'join_date', 'organisation', 'activity_name',
            'badge_validity', 'profile_picture', 'activity_image'
        ]
        widgets = {
            'identifiant': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'type_adherent': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'address': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4}),
            'phone1': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'phone2': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'join_date': forms.DateInput(attrs={'class': 'w-full p-2 border rounded', 'type': 'date'}),
            'organisation': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'activity_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'badge_validity': forms.DateInput(attrs={'class': 'w-full p-2 border rounded', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'w-full p-2 border rounded'}),
            'activity_image': forms.FileInput(attrs={'class': 'w-full p-2 border rounded'}),
        }

class InteractionForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = ['identifiant', 'personnel', 'adherent', 'report', 'due_date', 'status']
        widgets = {
            'identifiant': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'personnel': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'adherent': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'report': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 6}),
            'due_date': forms.DateTimeInput(attrs={'class': 'w-full p-2 border rounded', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
        }