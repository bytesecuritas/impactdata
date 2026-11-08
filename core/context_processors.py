from .models import AdherentRegistrationRequest


def pending_registration_count(request):
    """Nombre de demandes d'inscription en attente, pour le badge du menu
    (superviseurs/admins — issue impactdata inscription publique)."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    if not (user.is_superuser or user.role in ('admin', 'superviseur')):
        return {}

    return {
        'pending_registration_count': AdherentRegistrationRequest.objects.filter(
            status='pending'
        ).count(),
    }
