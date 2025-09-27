from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
from django.urls import reverse

class CustomCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Widget personnalisé pour les checkboxes multiples avec un meilleur rendu
    """
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)
        self.attrs = attrs or {}
        self.attrs.update({'class': 'form-check-input'})

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        if not isinstance(value, (list, tuple)):
            value = [value]
        
        final_attrs = self.build_attrs(self.attrs, attrs)
        output = []
        
        for i, (option_value, option_label) in enumerate(self.choices):
            if option_value == '':
                continue
                
            checkbox_id = f"{name}_{i}"
            checkbox_attrs = final_attrs.copy()
            checkbox_attrs['id'] = checkbox_id
            checkbox_attrs['value'] = option_value
            checkbox_attrs['name'] = name
            
            if str(option_value) in [str(v) for v in value]:
                checkbox_attrs['checked'] = 'checked'
            
            checkbox_html = format_html(
                '<input type="checkbox" {} />',
                flatatt(checkbox_attrs)
            )
            
            label_html = format_html(
                '<label class="form-check-label" for="{}">{}</label>',
                checkbox_id,
                option_label
            )
            
            item_html = format_html(
                '<div class="form-check">{}{}</div>',
                checkbox_html,
                label_html
            )
            
            output.append(item_html)
        
        return mark_safe('\n'.join(output))


class SearchableSelectWidget(forms.Select):
    """
    Widget personnalisé pour les champs select avec fonctionnalité de recherche
    """
    def __init__(self, attrs=None, choices=(), search_url=None, search_fields=None, placeholder="Rechercher..."):
        super().__init__(attrs, choices)
        self.search_url = search_url
        self.search_fields = search_fields or []
        self.placeholder = placeholder
        
        # Ajouter les classes CSS nécessaires
        if attrs is None:
            attrs = {}
        attrs.update({
            'class': 'form-select searchable-select',
            'data-search-url': search_url or '',
            'data-search-fields': ','.join(self.search_fields),
            'data-placeholder': self.placeholder
        })
        self.attrs = attrs

    def render(self, name, value, attrs=None, renderer=None):
        # Récupérer les attributs finaux
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['name'] = name
        
        # Générer les options
        options = []
        for option_value, option_label in self.choices:
            if option_value == '':
                continue
            selected = 'selected' if str(option_value) == str(value) else ''
            options.append(f'<option value="{option_value}" {selected}>{option_label}</option>')
        
        # Créer le HTML du select avec fonctionnalité de recherche
        select_html = f'''
        <div class="searchable-select-container">
            <select {flatatt(final_attrs)}>
                <option value="">{self.placeholder}</option>
                {''.join(options)}
            </select>
            <div class="search-overlay" style="display: none;">
                <input type="text" class="form-control search-input" placeholder="{self.placeholder}" autocomplete="off">
                <div class="search-results"></div>
            </div>
        </div>
        '''
        
        return mark_safe(select_html)


class PersonnelSearchWidget(SearchableSelectWidget):
    """
    Widget spécialisé pour la recherche de personnel par matricule
    """
    def __init__(self, attrs=None, choices=()):
        super().__init__(
            attrs=attrs,
            choices=choices,
            search_url='/api/personnel/search/',
            search_fields=['matricule', 'first_name', 'last_name'],
            placeholder="Rechercher par matricule, prénom ou nom..."
        )


class AdherentSearchWidget(SearchableSelectWidget):
    """
    Widget spécialisé pour la recherche d'adhérents par ID, matricule et téléphone
    """
    def __init__(self, attrs=None, choices=()):
        super().__init__(
            attrs=attrs,
            choices=choices,
            search_url='/api/adherent/search/',
            search_fields=['id', 'identifiant', 'phone1', 'phone2', 'first_name', 'last_name'],
            placeholder="Rechercher par ID, matricule, téléphone, prénom ou nom..."
        )


class OrganizationSearchWidget(SearchableSelectWidget):
    """
    Widget spécialisé pour la recherche d'organisations par nom
    """
    def __init__(self, attrs=None, choices=()):
        super().__init__(
            attrs=attrs,
            choices=choices,
            search_url='/api/organization/search/',
            search_fields=['name', 'identifiant'],
            placeholder="Rechercher par nom d'organisation..."
        )


class CategorySearchWidget(SearchableSelectWidget):
    """
    Widget spécialisé pour la recherche de catégories par nom
    """
    def __init__(self, attrs=None, choices=()):
        super().__init__(
            attrs=attrs,
            choices=choices,
            search_url='/api/category/search/',
            search_fields=['name'],
            placeholder="Rechercher par nom de catégorie..."
        )
