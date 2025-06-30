from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.crypto import get_random_string
from .models import User, Adherent, Organization, Category, Interaction, Badge, UserObjective

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone', 'profession', 'fonction']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

# Formulaires pour Adhérent
class AdherentForm(forms.ModelForm):
    """Formulaire pour créer/modifier un adhérent"""
    class Meta:
        model = Adherent
        fields = [
            'first_name', 'last_name', 'birth_date', 'type_adherent',
            'commune', 'quartier', 'secteur', 'phone1', 'phone2', 
            'num_urgence1', 'num_urgence2', 'email', 'medical_info',
            'formation_pro', 'distinction', 'langues', 'join_date', 
            'organisation', 'profile_picture', 'activity_name', 'badge_validity'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'type_adherent': forms.Select(attrs={'class': 'form-select'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control'}),
            'secteur': forms.TextInput(attrs={'class': 'form-control'}),
            'phone1': forms.TextInput(attrs={'class': 'form-control'}),
            'phone2': forms.TextInput(attrs={'class': 'form-control'}),
            'num_urgence1': forms.TextInput(attrs={'class': 'form-control'}),
            'num_urgence2': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'medical_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'formation_pro': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'distinction': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'langues': forms.TextInput(attrs={'class': 'form-control'}),
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'organisation': forms.Select(attrs={'class': 'form-select'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'activity_name': forms.TextInput(attrs={'class': 'form-control'}),
            'badge_validity': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Rendre les champs de badge obligatoires
        self.fields['activity_name'].required = True
        self.fields['badge_validity'].required = True
        
        # Ajouter des labels et help_text personnalisés
        self.fields['activity_name'].label = "Nom de l'activité"
        self.fields['activity_name'].help_text = "Ex: Macanier, Commerçant, Artisan, etc."
        
        self.fields['badge_validity'].label = "Validité du badge"
        self.fields['badge_validity'].help_text = "Date jusqu'à laquelle le badge sera valide (généralement 1 an)"
        
        # Filtrer les organisations selon le rôle de l'utilisateur
        # if user and user.role == 'agent':
        #     self.fields['organisation'].queryset = Organization.objects.filter(created_by=user)

    def clean(self):
        cleaned_data = super().clean()
        activity_name = cleaned_data.get('activity_name')
        badge_validity = cleaned_data.get('badge_validity')
        
        # Validation personnalisée pour les champs de badge
        if not activity_name:
            self.add_error('activity_name', 'Le nom de l\'activité est obligatoire pour générer un badge.')
        
        if not badge_validity:
            self.add_error('badge_validity', 'La validité du badge est obligatoire.')
        elif badge_validity and badge_validity < timezone.now().date():
            self.add_error('badge_validity', 'La validité du badge ne peut pas être dans le passé.')
        
        return cleaned_data

# Formulaires pour Organisation
class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'identifiant', 'name', 'monthly_revenue', 'address',
            'creation_date', 'phone', 'whatsapp', 'category',
            'number_personnel', 'infos_annexes', 'hobies'
        ]
        widgets = {
            'identifiant': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_revenue': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'creation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'number_personnel': forms.NumberInput(attrs={'class': 'form-control'}),
            'infos_annexes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hobies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les adhérents selon le rôle de l'utilisateur
        # if user and user.role == 'agent':
        #     self.fields['adherent'].queryset = Adherent.objects.filter(
        #         organisation__in=Organization.objects.filter(created_by=user)
        #     )

class UserForm(forms.ModelForm):
    """Formulaire pour créer/modifier un utilisateur"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Laissez vide pour conserver le mot de passe actuel"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Confirmez le mot de passe"
    )
    
    class Meta:
        model = User
        fields = ['matricule', 'first_name', 'last_name', 'email', 'telephone', 'profession', 'fonction', 'role', 'is_active']
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
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

class UserRegistrationForm(UserCreationForm):
    """Formulaire de création d'utilisateur par l'administrateur"""
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Laissez vide pour générer un mot de passe automatique'
    )
    password2 = forms.CharField(
        label='Confirmation du mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'matricule', 'email', 'telephone', 
                 'profession', 'fonction', 'role', 'created_by', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # Supprimer le paramètre user s'il est passé
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limiter les choix de rôle selon l'utilisateur connecté
        # Cette logique sera gérée dans la vue

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Si aucun mot de passe n'est fourni, en générer un automatiquement
        if not self.cleaned_data.get('password1'):
            password = get_random_string(12)
            user.set_password(password)
            user._password_generated = password  # Pour l'affichage
        else:
            user.set_password(self.cleaned_data['password1'])
        
        if commit:
            user.save()
        return user

class UserEditForm(forms.ModelForm):
    """Formulaire de modification d'utilisateur"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone', 
                 'profession', 'fonction', 'role', 'created_by', 'is_active', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BadgeForm(forms.ModelForm):
    """Formulaire pour les badges"""
    class Meta:
        model = Badge
        fields = ['adherent', 'activity_name', 'badge_validity', 'activity_image', 'notes']
        widgets = {
            'adherent': forms.Select(attrs={'class': 'form-select'}),
            'activity_name': forms.TextInput(attrs={'class': 'form-control'}),
            'badge_validity': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activity_image': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les adhérents selon le rôle de l'utilisateur
        if user and user.role == 'agent':
            self.fields['adherent'].queryset = Adherent.objects.filter(
                organisation__in=Organization.objects.filter(created_by=user)
            )

class ProfileEditForm(forms.ModelForm):
    """Formulaire de modification du profil utilisateur"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone', 'profession', 'fonction']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AdherentSearchForm(forms.Form):
    """Formulaire de recherche d'adhérents"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom, prénom, identifiant...'
        })
    )
    type_adherent = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(Adherent.TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    organisation = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        empty_label="Toutes les organisations",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    join_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    join_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class OrganizationSearchForm(forms.Form):
    """Formulaire de recherche d'organisations"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom, identifiant...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    created_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    created_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class UserObjectiveForm(forms.ModelForm):
    """Formulaire pour assigner des objectifs aux utilisateurs"""
    class Meta:
        model = UserObjective
        fields = ['user',  'objective_type', 'target_value', 
                 'deadline', 'description'
                ]  

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role='agent'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Agent"
    )
    objective_type = forms.ChoiceField(
        choices=[
            ('organizations', 'Nombre d\'organisations'),
            ('adherents', 'Nombre d\'adhérents'),
            ('interactions', 'Nombre d\'interactions'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Type d'objectif"
    )
    target_value = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Valeur cible"
    )
    deadline = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Date limite"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label="Description"
    )

