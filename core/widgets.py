from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt

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
