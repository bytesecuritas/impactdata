from django.shortcuts import render
from .models import User

# Create your views here.
def is_admin(user):
    return user.is_authenticated and user.can_manage_users()