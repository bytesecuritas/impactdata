"""Garde-fous pour les uploads du formulaire d'inscription public (non authentifié)."""
import io
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image, UnidentifiedImageError

MAX_PHOTO_BYTES = 2 * 1024 * 1024        # 2 Mo
MAX_PHOTO_PIXELS = 25_000_000            # protège contre les decompression bombs
MAX_PHOTO_SIDE = 1024                    # redimensionnement de sortie
ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}

# Limitation de débit par IP sur le formulaire public
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 3600  # secondes


def registration_photo_storage():
    """Stockage privé : hors de MEDIA_ROOT, donc jamais servi par /media/.
    Les photos ne sont lisibles que via la vue protégée."""
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)


def sanitize_profile_image(upload):
    """Valide l'image et la ré-encode (supprime EXIF, contenu embarqué,
    polyglottes). Retourne un ContentFile au nom aléatoire."""
    if upload.size > MAX_PHOTO_BYTES:
        raise ValidationError("La photo ne doit pas dépasser 2 Mo.")

    try:
        upload.seek(0)
        probe = Image.open(upload)
        probe.verify()  # détecte les fichiers tronqués / corrompus
        upload.seek(0)
        img = Image.open(upload)
        fmt = img.format
        if fmt not in ALLOWED_FORMATS:
            raise ValidationError("Format non accepté (JPEG, PNG ou WebP uniquement).")
        if img.width * img.height > MAX_PHOTO_PIXELS:
            raise ValidationError("Image trop grande.")
        img.load()
    except ValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError):
        raise ValidationError("Fichier image invalide.")

    img = img.convert('RGB')
    img.thumbnail((MAX_PHOTO_SIDE, MAX_PHOTO_SIDE))
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)
    return ContentFile(buffer.getvalue(), name=f"{uuid.uuid4().hex}.jpg")


def client_ip(request):
    # REMOTE_ADDR uniquement : X-Forwarded-For est falsifiable. Derrière un
    # reverse proxy, configurer le proxy pour fixer REMOTE_ADDR correctement.
    return request.META.get('REMOTE_ADDR', 'unknown')


def rate_limited(request):
    """True si l'IP a déjà atteint le quota de soumissions dans la fenêtre."""
    key = f"public_register_{client_ip(request)}"
    return cache.get(key, 0) >= RATE_LIMIT_MAX


def register_submission(request):
    key = f"public_register_{client_ip(request)}"
    cache.add(key, 0, RATE_LIMIT_WINDOW)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, RATE_LIMIT_WINDOW)
