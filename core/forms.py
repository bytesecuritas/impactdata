from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.crypto import get_random_string
from .models import User, Adherent, Organization, Category, Interaction, Badge, UserObjective, RolePermission, ReferenceValue, GeneralParameter, SystemLog

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone', 'profession', 'fonction', 
                 'adresse', 'nom_urg1', 'prenom_urg1', 'telephone_urg1', 
                 'nom_urg2', 'prenom_urg2', 'telephone_urg2']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nom_urg1': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom_urg1': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_urg1': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_urg2': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom_urg2': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_urg2': forms.TextInput(attrs={'class': 'form-control'}),
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
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'max': timezone.now().date()}),
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
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'max': timezone.now().date()}),
            'organisation': forms.Select(attrs={'class': 'form-select'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'activity_name': forms.TextInput(attrs={'class': 'form-control'}),
            'badge_validity': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min':timezone.now().date()}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Utiliser les valeurs de référence pour les types d'adhérent
        try:
            from core.models import ReferenceValue
            type_choices = ReferenceValue.get_choices_for_category('adherent_types')
            self.fields['type_adherent'].choices = [('', '---------')] + list(type_choices)
        except Exception:
            # Fallback vers les choix statiques si les valeurs de référence ne sont pas disponibles
            self.fields['type_adherent'].choices = [('', '---------')] + list(Adherent.TYPE_CHOICES)
        
        # Filtrer les organisations selon le rôle de l'utilisateur
        if user and user.role == 'agent':
            self.fields['organisation'].queryset = Organization.objects.filter(created_by=user)
        elif user and user.role == 'superviseur':
            # Les superviseurs peuvent voir les organisations de leurs agents
            agent_ids = User.objects.filter(role='agent').values_list('id', flat=True)
            self.fields['organisation'].queryset = Organization.objects.filter(created_by__id__in=agent_ids)

    def clean(self):
        cleaned_data = super().clean()
        phone1 = cleaned_data.get('phone1')
        
        # Vérifier que le numéro de téléphone est unique dans la base de données
        # Exclure l'instance actuelle lors de la mise à jour
        if phone1:
            queryset = Adherent.objects.filter(phone1=phone1)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError("Le numéro de téléphone principal existe déjà pour un autre adhérent.")
        
        phone2 = cleaned_data.get('phone2')
        
        # Validation des numéros de téléphone
        if phone1 and phone2 and phone1 == phone2:
            raise forms.ValidationError("Les deux numéros de téléphone ne peuvent pas être identiques.")
        
        return cleaned_data

# Formulaires pour Organisation
class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'name', 'monthly_revenue', 'address',
            'creation_date', 'phone', 'whatsapp', 'category',
            'number_personnel', 'infos_annexes'
        ]
        widgets = {
            'identifiant': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_revenue': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'creation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'max':timezone.now().date()}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'number_personnel': forms.NumberInput(attrs={'class': 'form-control'}),
            'infos_annexes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        
        # Vérifier l'unicité du nom de la catégorie
        # Exclure l'instance actuelle lors de la mise à jour
        if name:
            queryset = Category.objects.filter(name__iexact=name)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError("Une catégorie avec ce nom existe déjà.")
        
        return cleaned_data        

# Formulaires pour Interaction
class InteractionForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = [
            'personnel', 'adherent', 'report',
            'due_date', 'status'
        ]
        widgets = {
            'identifiant': forms.TextInput(attrs={'class': 'form-control'}),
            'personnel': forms.Select(attrs={'class': 'form-control'}),
            'adherent': forms.Select(attrs={'class': 'form-control'}),
            'report': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local', 'min': timezone.now().strftime('%Y-%m-%dT%H:%M')  }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Utiliser les valeurs de référence pour le statut
        try:
            from core.models import ReferenceValue
            status_choices = ReferenceValue.get_choices_for_category('interaction_status')
            self.fields['status'].choices = [('', '---------')] + list(status_choices)
        except Exception:
            # Fallback vers les choix statiques si les valeurs de référence ne sont pas disponibles
            self.fields['status'].choices = [('', '---------')] + list(Interaction.STATUS_CHOICES)
        
        # Filtrer les adhérents selon le rôle de l'utilisateur
        # if user and user.role == 'agent':
        #     self.fields['adherent'].queryset = Adherent.objects.filter(
        #         organisation__in=Organization.objects.filter(created_by=user)
        #     )

    def clean_due_date(self):
        due_date = self.cleaned_data['due_date']
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("La date d'échéance ne peut pas être dans le passé.")
        return due_date

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
        fields = ['matricule', 'first_name', 'last_name', 'email', 'telephone', 'profession', 'fonction', 
                 'adresse', 'nom_urg1', 'prenom_urg1', 'telephone_urg1', 
                 'nom_urg2', 'prenom_urg2', 'telephone_urg2', 'role', 'is_active']
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Matricule du personnel ex:AG1245'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Fodé'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Camara'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder':'king@gmail.com'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'625325458'}),
            'profession': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Electricien, Maçon, ...'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Rôle dans l\'entreprise ex: DRH'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder':'Adresse complète'}),
            'nom_urg1': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Nom du contact d\'urgence 1'}),
            'prenom_urg1': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Prénom du contact d\'urgence 1'}),
            'telephone_urg1': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'625325458'}),
            'nom_urg2': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Nom du contact d\'urgence 2'}),
            'prenom_urg2': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Prénom du contact d\'urgence 2'}),
            'telephone_urg2': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'625325458'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Utiliser les valeurs de référence pour les rôles
        try:
            from core.models import ReferenceValue
            role_choices = ReferenceValue.get_choices_for_category('user_roles')
            self.fields['role'].choices = [('', '---------')] + list(role_choices)
        except Exception:
            # Fallback vers les choix statiques si les valeurs de référence ne sont pas disponibles
            self.fields['role'].choices = [('', '---------')] + list(User.ROLE_CHOICES)
    
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
                 'profession', 'fonction', 'adresse', 'nom_urg1', 'prenom_urg1', 'telephone_urg1', 
                 'nom_urg2', 'prenom_urg2', 'telephone_urg2', 'role', 'created_by', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Le prénom ex: Fodé'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Le nom ex: Camara'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Matricule du personnel ex:AG1245'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder':'king@gmail.com'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Numéro de téléphone ex: 625325458'}),
            'profession': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Electricien, Maçon, ...'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Rôle dans l\'entreprise ex: DGH'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder':'Adresse complète'}),
            'nom_urg1': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Nom du contact d\'urgence 1'}),
            'prenom_urg1': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Prénom du contact d\'urgence 1'}),
            'telephone_urg1': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'625325458'}),
            'nom_urg2': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Nom du contact d\'urgence 2'}),
            'prenom_urg2': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Prénom du contact d\'urgence 2'}),
            'telephone_urg2': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'625325458'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # Supprimer le paramètre user s'il est passé
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Utiliser les valeurs de référence pour les rôles
        try:
            from core.models import ReferenceValue
            role_choices = ReferenceValue.get_choices_for_category('user_roles')
            self.fields['role'].choices = [('', '---------')] + list(role_choices)
        except Exception:
            # Fallback vers les choix statiques si les valeurs de référence ne sont pas disponibles
            self.fields['role'].choices = [('', '---------')] + list(User.ROLE_CHOICES)
        
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
                 'profession', 'fonction', 'adresse', 'nom_urg1', 'prenom_urg1', 'telephone_urg1', 
                 'nom_urg2', 'prenom_urg2', 'telephone_urg2', 'role', 'created_by', 'is_active', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nom_urg1': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom_urg1': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_urg1': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_urg2': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom_urg2': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_urg2': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Utiliser les valeurs de référence pour les rôles
        try:
            from core.models import ReferenceValue
            role_choices = ReferenceValue.get_choices_for_category('user_roles')
            self.fields['role'].choices = [('', '---------')] + list(role_choices)
        except Exception:
            # Fallback vers les choix statiques si les valeurs de référence ne sont pas disponibles
            self.fields['role'].choices = [('', '---------')] + list(User.ROLE_CHOICES)

class BadgeForm(forms.ModelForm):
    """Formulaire pour les badges"""
    class Meta:
        model = Badge
        fields = ['adherent', 'activity_name', 'badge_validity', 'activity_image', 'notes']
        widgets = {
            'adherent': forms.Select(attrs={'class': 'form-select'}),
            'activity_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Sont travail ex: Ménusier'}),
            'badge_validity': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min':timezone.now().date()}),
            'activity_image': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder':'Une petite escription'}),
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
        fields = ['first_name', 'last_name', 'email', 'telephone', 'profession', 'fonction', 
                 'adresse', 'nom_urg1', 'prenom_urg1', 'telephone_urg1', 
                 'nom_urg2', 'prenom_urg2', 'telephone_urg2']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nom_urg1': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom_urg1': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_urg1': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_urg2': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom_urg2': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_urg2': forms.TextInput(attrs={'class': 'form-control'}),
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
        choices=[('', 'Tous les types')],
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
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min':join_date_from})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Utiliser les valeurs de référence pour les types d'adhérent
        try:
            from core.models import ReferenceValue
            type_choices = ReferenceValue.get_choices_for_category('adherent_types')
            self.fields['type_adherent'].choices = [('', 'Tous les types')] + list(type_choices)
        except Exception:
            # Fallback vers les choix statiques si les valeurs de référence ne sont pas disponibles
            self.fields['type_adherent'].choices = [('', 'Tous les types')] + list(Adherent.TYPE_CHOICES)

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
        label="Nombre à ajouter",
        help_text="Nombre d'éléments à créer en plus de ce qui existe déjà"
    )
    deadline = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min':timezone.now().date()}),
        label="Date limite"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder':'Un petit détail '}),
        required=False,
        label="Description"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Utiliser les valeurs de référence pour les types d'objectif
        try:
            from core.models import ReferenceValue
            objective_choices = ReferenceValue.get_choices_for_category('objective_status')
            # Note: Pour les types d'objectif, on utilise des choix personnalisés car ce ne sont pas des statuts
            # mais des types d'objectif. Les statuts d'objectif sont gérés automatiquement par le modèle.
        except Exception:
            pass  # On garde les choix par défaut pour les types d'objectif

class InteractionSearchForm(forms.Form):
    """Formulaire de recherche avancée pour les interactions"""
    personnel = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=['agent', 'superviseur']).order_by('first_name', 'last_name'),
        required=False,
        label="Personnel",
        empty_label="Tous les personnels"
    )
    adherent = forms.ModelChoiceField(
        queryset=Adherent.objects.all().order_by('last_name', 'first_name'),
        required=False,
        label="Adhérent",
        empty_label="Tous les adhérents"
    )
    status = forms.ChoiceField(
        choices=[('', 'Tous les statuts')],
        required=False,
        label="Statut"
    )
    due_date_from = forms.DateField(
        required=False,
        label="Date d'échéance (début)",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    due_date_to = forms.DateField(
        required=False,
        label="Date d'échéance (fin)",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    keywords = forms.CharField(
        max_length=100,
        required=False,
        label="Mots-clés",
        widget=forms.TextInput(attrs={'placeholder': 'Rechercher dans les rapports...'})
    )
    overdue_only = forms.BooleanField(
        required=False,
        label="En retard uniquement",
        initial=False
    )
    due_soon = forms.BooleanField(
        required=False,
        label="Échéance proche (7 jours)",
        initial=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Utiliser les valeurs de référence pour le statut
        try:
            from core.models import ReferenceValue
            status_choices = ReferenceValue.get_choices_for_category('interaction_status')
            self.fields['status'].choices = [('', 'Tous les statuts')] + list(status_choices)
        except Exception:
            # Fallback vers les choix statiques si les valeurs de référence ne sont pas disponibles
            self.fields['status'].choices = [('', 'Tous les statuts')] + list(Interaction.STATUS_CHOICES)

# ==================== FORMULAIRES POUR LES PARAMÈTRES DE L'APPLICATION ====================

class RolePermissionForm(forms.ModelForm):
    """Formulaire pour la gestion des permissions de rôles"""
    class Meta:
        model = RolePermission
        fields = ['role', 'permission', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'permission': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Grouper les permissions par catégorie
        permission_choices = []
        current_category = None
        
        for code, label in self.fields['permission'].choices:
            if code == '':  # Skip empty choice
                continue
                
            # Déterminer la catégorie basée sur le code
            if code.startswith('user_'):
                category = 'Gestion des utilisateurs'
            elif code.startswith('adherent_'):
                category = 'Gestion des adhérents'
            elif code.startswith('organization_'):
                category = 'Gestion des organisations'
            elif code.startswith('interaction_'):
                category = 'Gestion des interactions'
            elif code.startswith('badge_'):
                category = 'Gestion des badges'
            elif code.startswith('objective_'):
                category = 'Gestion des objectifs'
            elif code.startswith('settings_'):
                category = 'Gestion des paramètres'
            elif code.startswith('reports_') or code.startswith('stats_'):
                category = 'Rapports et statistiques'
            elif code.startswith('system_') or code.startswith('data_'):
                category = 'Administration système'
            else:
                category = 'Autres'
            
            if category != current_category:
                permission_choices.append((category, [(code, label)]))
                current_category = category
            else:
                permission_choices[-1][1].append((code, label))
        
        self.fields['permission'].choices = permission_choices


class ReferenceValueForm(forms.ModelForm):
    """Formulaire pour la gestion des valeurs de référence"""
    class Meta:
        model = ReferenceValue
        fields = ['category', 'code', 'label', 'description', 'sort_order', 'is_active', 'is_default', 'is_system']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code unique ex: create_user'}),
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Libellé affiché ex: Créer un agent'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description optionnelle'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_code(self):
        code = self.cleaned_data['code']
        category = self.cleaned_data.get('category')
        
        # Vérifier l'unicité du code dans la catégorie
        if category:
            existing = ReferenceValue.objects.filter(
                category=category,
                code=code
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    f"Un code '{code}' existe déjà dans la catégorie '{self.fields['category'].choices_dict[category]}'"
                )
        
        return code.upper()  # Convertir en majuscules
    
    def clean(self):
        cleaned_data = super().clean()
        is_default = cleaned_data.get('is_default')
        is_active = cleaned_data.get('is_active')
        
        # Une valeur par défaut doit être active
        if is_default and not is_active:
            raise forms.ValidationError(
                "Une valeur par défaut doit être active."
            )
        
        return cleaned_data


class GeneralParameterForm(forms.ModelForm):
    """Formulaire pour la gestion des paramètres généraux"""
    class Meta:
        model = GeneralParameter
        fields = ['parameter_key', 'parameter_type', 'value', 'default_value', 'description', 'is_required', 'is_system']
        widgets = {
            'parameter_key': forms.Select(attrs={'class': 'form-select'}),
            'parameter_type': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'default_value': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnaliser le widget de valeur selon le type
        if self.instance and self.instance.parameter_type:
            self.update_value_widget(self.instance.parameter_type)
    
    def update_value_widget(self, parameter_type):
        """Met à jour le widget de valeur selon le type de paramètre"""
        if parameter_type == 'boolean':
            self.fields['value'] = forms.BooleanField(
                required=False,
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
            )
        elif parameter_type == 'number':
            self.fields['value'] = forms.DecimalField(
                widget=forms.NumberInput(attrs={'class': 'form-control'})
            )
        elif parameter_type == 'email':
            self.fields['value'] = forms.EmailField(
                widget=forms.EmailInput(attrs={'class': 'form-control'})
            )
        elif parameter_type == 'url':
            self.fields['value'] = forms.URLField(
                widget=forms.URLInput(attrs={'class': 'form-control'})
            )
        elif parameter_type == 'date':
            self.fields['value'] = forms.DateField(
                widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
            )
        elif parameter_type == 'time':
            self.fields['value'] = forms.TimeField(
                widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
            )
        elif parameter_type == 'datetime':
            self.fields['value'] = forms.DateTimeField(
                widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
            )
        elif parameter_type == 'textarea':
            self.fields['value'] = forms.CharField(
                widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
            )
        else:  # text, select, file
            self.fields['value'] = forms.CharField(
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
    
    def clean_value(self):
        value = self.cleaned_data['value']
        parameter_type = self.cleaned_data.get('parameter_type')
        
        if parameter_type == 'number':
            try:
                float(value)
            except ValueError:
                raise forms.ValidationError("La valeur doit être un nombre valide.")
        elif parameter_type == 'email':
            from django.core.validators import validate_email
            try:
                validate_email(value)
            except forms.ValidationError:
                raise forms.ValidationError("L'adresse email n'est pas valide.")
        elif parameter_type == 'url':
            from django.core.validators import URLValidator
            validator = URLValidator()
            try:
                validator(value)
            except forms.ValidationError:
                raise forms.ValidationError("L'URL n'est pas valide.")
        
        return value


class SystemLogFilterForm(forms.Form):
    """Formulaire de filtrage pour les journaux système"""
    level = forms.ChoiceField(
        choices=[('', 'Tous les niveaux')] + SystemLog.LOG_LEVELS,
        required=False,
        label="Niveau",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ChoiceField(
        choices=[('', 'Toutes les catégories')] + SystemLog.LOG_CATEGORIES,
        required=False,
        label="Catégorie",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by('first_name', 'last_name'),
        required=False,
        label="Utilisateur",
        empty_label="Tous les utilisateurs",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        label="Date de début",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        label="Date de fin",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    message = forms.CharField(
        max_length=100,
        required=False,
        label="Message",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rechercher dans les messages...'})
    )


class BulkRolePermissionForm(forms.Form):
    """Formulaire pour l'assignation en masse de permissions"""
    role = forms.ChoiceField(
        choices=[],
        label="Rôle",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    permissions = forms.MultipleChoiceField(
        choices=RolePermission.PERMISSION_CHOICES,
        label="Permissions",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    action = forms.ChoiceField(
        choices=[
            ('add', 'Ajouter les permissions'),
            ('remove', 'Retirer les permissions'),
            ('replace', 'Remplacer toutes les permissions'),
        ],
        label="Action",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Utiliser les valeurs de référence pour les rôles
        try:
            from core.models import ReferenceValue
            role_choices = ReferenceValue.get_choices_for_category('user_roles')
            self.fields['role'].choices = [('', '---------')] + list(role_choices)
        except Exception:
            # Fallback vers les choix statiques si les valeurs de référence ne sont pas disponibles
            self.fields['role'].choices = [('', '---------')] + list(User.ROLE_CHOICES)


class ReferenceValueImportForm(forms.Form):
    """Formulaire pour l'import de valeurs de référence"""
    category = forms.ChoiceField(
        choices=ReferenceValue.CATEGORY_CHOICES,
        label="Catégorie",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    csv_file = forms.FileField(
        label="Fichier CSV",
        help_text="Format: code,label,description,sort_order,is_active,is_default,is_system",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    replace_existing = forms.BooleanField(
        required=False,
        label="Remplacer les valeurs existantes",
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ParameterBackupForm(forms.Form):
    """Formulaire pour la sauvegarde des paramètres"""
    include_system_params = forms.BooleanField(
        initial=True,
        required=False,
        label="Inclure les paramètres système"
    )
    include_reference_values = forms.BooleanField(
        initial=True,
        required=False,
        label="Inclure les valeurs de référence"
    )
    include_role_permissions = forms.BooleanField(
        initial=True,
        required=False,
        label="Inclure les permissions de rôles"
    )
    format = forms.ChoiceField(
        choices=[
            ('json', 'JSON'),
            ('csv', 'CSV'),
        ],
        initial='json',
        label="Format d'export"
    )

