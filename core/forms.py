from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from .models import User, Adherent, Organization, Category, Interaction

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'telephone', 'profession']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

# Formulaires pour Adhérent
class AdherentForm(forms.ModelForm):
    class Meta:
        model = Adherent
        fields = [
            'identifiant', 'first_name', 'last_name', 'type_adherent',
            'address', 'phone1', 'phone2', 'join_date', 'organisation',
            'activity_name', 'badge_validity', 'profile_picture', 'activity_image'
        ]
        widgets = {
            'identifiant': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'type_adherent': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone1': forms.TextInput(attrs={'class': 'form-control'}),
            'phone2': forms.TextInput(attrs={'class': 'form-control'}),
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'organisation': forms.Select(attrs={'class': 'form-control'}),
            'activity_name': forms.TextInput(attrs={'class': 'form-control'}),
            'badge_validity': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'activity_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

# Formulaires pour Organisation
class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'identifiant', 'name', 'monthly_revenue', 'address',
            'creation_date', 'phone', 'category'
        ]
        widgets = {
            'identifiant': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_revenue': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'creation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

# Formulaires pour Catégorie
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# Formulaires pour Interaction
class InteractionForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = [
            'identifiant', 'personnel', 'adherent', 'report',
            'due_date', 'status'
        ]
        widgets = {
            'identifiant': forms.TextInput(attrs={'class': 'form-control'}),
            'personnel': forms.Select(attrs={'class': 'form-control'}),
            'adherent': forms.Select(attrs={'class': 'form-control'}),
            'report': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class UserForm(forms.ModelForm):
    """Formulaire pour créer/modifier un utilisateur"""
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text="Laissez vide pour conserver le mot de passe actuel"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text="Confirmez le mot de passe"
    )
    
    class Meta:
        model = User
        fields = ['matricule', 'name', 'email', 'telephone', 'profession', 'role', 'is_active']
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user