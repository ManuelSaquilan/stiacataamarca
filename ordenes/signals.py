from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.utils import timezone

def cerrar_sesiones_anteriores(sender, user, request, **kwargs):
    # Obtiene la sesión actual del usuario
    sesion_actual = request.session.session_key
    
    # Obtiene todas las sesiones activas (aún no expiren)
    sesiones = Session.objects.filter(expire_date__gte=timezone.now())
    
    for sesion in sesiones:
        datos = sesion.get_decoded()
        # Verifica si la sesión pertenece al usuario y no es la actual
        if datos.get('_auth_user_id') == str(user.pk) and sesion.session_key != sesion_actual:
            sesion.delete()

user_logged_in.connect(cerrar_sesiones_anteriores)
