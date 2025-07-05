from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service pour gérer l'envoi d'emails"""
    
    @staticmethod
    def send_welcome_email(user, password, request=None):
        """
        Envoie un email de bienvenue avec les informations de connexion
        """
        try:
            # Construire l'URL de connexion
            if request:
                current_site = get_current_site(request)
                login_url = f"http://{current_site.domain}{reverse('core:login')}"
            else:
                login_url = "http://localhost:8000/login/"
            
            # Contexte pour le template
            context = {
                'user': user,
                'password': password,
                'login_url': login_url,
            }
            
            # Rendre le template HTML
            html_message = render_to_string('core/emails/new_user_welcome.html', context)
            plain_message = strip_tags(html_message)
            
            # Envoyer l'email
            send_mail(
                subject='🎉 Bienvenue sur Impact Data Platform - Vos informations de connexion',
                message='Bonjour',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Email de bienvenue envoyé avec succès à {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de bienvenue à {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(user, reset_url, request=None):
        """
        Envoie un email de réinitialisation de mot de passe
        """
        try:
            # Contexte pour le template
            context = {
                'user': user,
                'reset_url': reset_url,
            }
            
            # Rendre le template HTML
            html_message = render_to_string('core/emails/password_reset.html', context)
            plain_message = strip_tags(html_message)
            
            # Envoyer l'email
            send_mail(
                subject='🔐 Réinitialisation de mot de passe - Impact Data Platform',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Email de réinitialisation envoyé avec succès à {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation à {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_test_email(email_address):
        """
        Envoie un email de test pour vérifier la configuration
        """
        try:
            send_mail(
                subject='Test de configuration email - Impact Data Platform',
                message='Ceci est un email de test pour vérifier la configuration email.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_address],
                fail_silently=False,
            )
            
            logger.info(f"Email de test envoyé avec succès à {email_address}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de test à {email_address}: {str(e)}")
            return False 