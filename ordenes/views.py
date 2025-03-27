from decimal import Decimal
from typing import Any
from django import forms
from django.db import models
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect

from ordenes import admin
from .models import CustomUser, Orden, Comercio, Empleado, Margen
from django.views import View

from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView, UpdateView, CreateView
from django.views.generic.detail import DetailView

import datetime
from django.db.models import Q

from django.contrib import messages

from django.template.loader import render_to_string
from weasyprint import HTML
import datetime as dt
from datetime import date, timedelta, datetime
from collections import defaultdict

from django.template import loader

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
#  O R D E N E S #

class OrdenBaseView(View):
    login_url = "/login/"
    redirect_field_name = "landing"
    template_name = "orden.html"
    model         = Orden
    fields        = "__all__"
    success_url   = reverse_lazy('ordenes:orden_all')

    def get_queryset(self):
        # Verificar si el usuario tiene un comercio asignado
        print(self.request.user.comercio)
        if self.request.user.is_authenticated and self.request.user.comercio:
            # Filtrar las órdenes por el comercio del usuario
            return Orden.objects.filter(comercio=self.request.user.comercio).order_by('-id')[:8]
        else:
            # Si no tiene comercio asignado, devolver todas las órdenes
            return Orden.objects.all().order_by('-id')[:8]
    

class OrdenListView(OrdenBaseView,ListView):
    '''ESTO ME PERMITE CREAR UNA VISTA CON LOS ORDENES'''

class OrdenDetailView(OrdenBaseView,ListView):
    template_name = 'orden_template.html'

class OrdenUpdateView(OrdenBaseView,UpdateView):
    template_name = 'orden_update.html'
    #model: Orden
    #fields        = "__all__"
    #success_url   = reverse_lazy('ordenes:orden_all')
    extra_context = {"tipo": "Actualizar Orden"}
    #def get_queryset(self):
    #    return Orden.objects.all()


class OrdenCreateView(CreateView):
    empleados = Empleado.objects.all()
    comercios = Comercio.objects.all()
    margen =  Margen.objects.all()[:1]
    template_name = 'orden_create.html'
    extra_context = {"tipo": "Crear Orden",'empleados':empleados,
                     'comercios':comercios,'limite':margen,}
  
    success_url   = reverse_lazy('ordenes:orden_all')


from datetime import datetime, timedelta

def CrearOrden(request, empleado, comercio, margen):
    lista_empleados = []
    try:
        # Obtener el empleado que realiza la compra
        empleado_compra = Empleado.objects.get(id=empleado)
        
        # Agregar el nombre y correo del empleado
        lista_empleados.append({
            "nombre": empleado_compra.nombre,
            "correo": empleado_compra.correoEmpleado
        })

        # Agregar autorizados solo si existen
        if empleado_compra.autorizado:
            lista_empleados.append({
                "nombre": empleado_compra.autorizado,
                "correo": empleado_compra.correoAutorizado
            })
        if empleado_compra.autorizado2:
            lista_empleados.append({
                "nombre": empleado_compra.autorizado2,
                "correo": empleado_compra.correoAutorizado2
            })
    except Empleado.DoesNotExist:
        pass
    
    if request.method == 'POST':
        # Verificar si el usuario ya ingresó el código
        if 'codigo_verificacion' in request.POST:
            codigo_ingresado = request.POST.get('codigo_verificacion')
            codigo_correcto = request.session.get('codigo_verificacion')
            tiempo_creacion = request.session.get('codigo_creacion')

            # Verificar si el código ha expirado
            if not tiempo_creacion or datetime.datetime.now() > datetime.datetime.strptime(tiempo_creacion, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(minutes=2):
                messages.error(request, 'El código ha expirado. Por favor, solicita uno nuevo.')
                del request.session['codigo_verificacion']
                del request.session['codigo_creacion']
                return redirect('ordenes:create_orden', empleado=empleado, comercio=comercio, margen=margen)

            # Verificar si el código ingresado es correcto
            if not codigo_correcto or codigo_ingresado != codigo_correcto:
                messages.error(request, 'El código ingresado es incorrecto.')
                return redirect('ordenes:create_orden', empleado=empleado, comercio=comercio, margen=margen)

            # Código correcto, proceder con la creación de la orden
            emp = request.POST.get('empleado')
            empleado = Empleado.objects.get(pk=emp)
            com = request.POST.get('comercio')
            comercio = Comercio.objects.get(pk=com)
            imp = request.POST.get('importe')
            cuo = request.POST.get('cuotas')
            usuario = request.POST.get('usuario')
            compro = request.POST.get('compro')
            valorcuota = int(imp) / int(cuo)
            
            # Asignar la fecha actual automáticamente
            fecha = date.today()

            nuevaorden = Orden(
                empleado=empleado,
                comercio=comercio,
                importe=imp,
                cuotas=cuo,
                valorcuota=valorcuota,
                fecha=fecha,
                usuario=usuario,
                compro=compro
            )
            
            nuevaorden.save()

            # Lista de correos a quienes se enviará el mail
            recipients = [empleado.correoEmpleado]

            # Agregar correos a la lista de destinatarios sin duplicados
            recipients.extend([e["correo"] for e in lista_empleados if e["correo"]])
            
            # Obtener el correo del comercio desde CustomUser
            try:
                comercio_user = CustomUser.objects.get(comercio=comercio)
                if comercio_user.email:
                    recipients.append(comercio_user.email)
            except CustomUser.DoesNotExist:
                pass  # Si no hay un usuario asociado al comercio, simplemente no agregamos nada

            recipients = list(set(recipients))  # Eliminar duplicados

            # Formatear la fecha como "día-mes-año"
            fecha_formateada = fecha.strftime("%d-%m-%Y")

            # Enviar correo
            subject = "Orden de Compra"
            message = f"""
            Hola {empleado.nombre},

            Se ha generado una nueva orden de compra con los siguientes datos:

            - Comercio: {comercio.comercio}
            - Importe: {imp}
            - Cuotas: {cuo}
            - Fecha: {fecha_formateada}
            - Compró: {compro}

            Saludos,
            El equipo de STIA.
            """
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)

            # Eliminar el código de verificación de la sesión
            del request.session['codigo_verificacion']
            del request.session['codigo_creacion']
            
            messages.success(request, 'Orden de Compra creada con éxito')
            return redirect('ordenes:orden_all')
        else:
            importe = request.POST.get('importe')
            cuotas = request.POST.get('cuotas')
            
            # Generar código de verificación
            codigo_verificacion = str(random.randint(100000, 999999))

            # Guardar el código y su tiempo de creación en la sesión
            request.session['codigo_verificacion'] = codigo_verificacion
            request.session['codigo_creacion'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


            # Enviar el código por correo
            compro = request.POST.get('compro')
            
            # Obtener correo del comprador
            correo_compra = None
            for persona in lista_empleados:
                if persona["nombre"].strip().lower() == compro.strip().lower():
                    correo_compra = persona["correo"]
                    break

            if correo_compra:
                # Enviar el código por correo
                subject = "Código de verificación para la orden de compra"
                message = f"Su código de verificación es: {codigo_verificacion}"
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [correo_compra])

                messages.success(request, 'Se ha enviado un código de verificación al correo del comprador.')
               
                return render(request, 'orden_create.html', {
                    'empleado': empleado,
                    'margen': margen,
                    'comercios': Comercio.objects.filter(id=comercio),
                    'comercio': comercio,
                    'orden': Orden.objects.all(),
                    'empleados': Empleado.objects.filter(id=empleado),
                    'lista_empleados': Empleado.objects.all(),
                    'compro': compro,  # Mantener los datos en el formulario
                    'importe': importe,
                    'cuotas': cuotas,
                    'codigo_verificacion': True  # Para mostrar el campo en el template
                })
            else:
                messages.error(request, 'No se encontró el correo del comprador.')
                return redirect('ordenes:create_orden', empleado=empleado, comercio=comercio, margen=margen)

    if request.method == 'GET':
        orden = Orden.objects.all()
        comercios = Comercio.objects.filter(Q(id=comercio))
        empleados = Empleado.objects.filter(Q(id=empleado))
        empleado_compra = Empleado.objects.get(id=empleado)
        
        empleado = empleado
        comercio = comercio
        margen = margen
        #messages.success(request, 'Empleado y Comercio agregado con éxito')
        return render(request, 'orden_create.html', {
            'empleado': empleado,
            'margen': margen,
            'comercios': comercios,
            'comercio': comercio,
            'orden': orden,
            'empleados': empleados,
            'lista_empleados': lista_empleados
        })

import random
from django.core.mail import send_mail
from django.conf import settings

def generar_codigo():
    return str(random.randint(100000, 999999))  # Código de 6 dígitos

def enviar_codigo_verificacion(correo, codigo):
    subject = "Código de verificación para tu orden"
    message = f"""
    Hola,

    Tu código de verificación es: {codigo}

    Por favor, ingrésalo en la página para confirmar tu compra.

    Saludos,
    El equipo de STIA.
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [correo])



# C O M E R C I O S #
class ComercioBaseView(View):
    template_name = "comercio.html"
    model         = Comercio
    fields        = "__all__"
    success_url   = reverse_lazy('ordenes:comercio_all')

class ComercioListView(ComercioBaseView, ListView):
    '''ESTO ME PERMITE CREAR UNA VISTA CON LOS COMERCIOS'''

class ComercioDetailView(ComercioBaseView, ListView):
    template_name = 'comercio_template.html'

class ComercioCreateView(ComercioBaseView, CreateView):
    template_name = 'comercio_create.html'
    extra_context = {"tipo": "Crear Comercio"}

class ComercioUpdateView(ComercioBaseView, UpdateView):
    template_name = 'comercio_update.html'
    extra_context = {"tipo": "Actualizar Comercio"}

# E M P L E A D O S #

class EmpleadoBaseView(View):
    template_name = "empleado.html"
    model         = Empleado
    fields        = "__all__"
    success_url   = reverse_lazy('ordenes:empleado_all')

class EmpleadoListView(EmpleadoBaseView, ListView):
    '''ESTO ME PERMITE CREAR UNA VISTA CON LOS EMPLEADOS'''


class EmpleadoDetailView(EmpleadoBaseView, ListView):
    template_name = 'empleado_template.html'
    

class EmpleadoCreateView(EmpleadoBaseView, CreateView):
    template_name = 'empleado_create.html'
    extra_context = {"tipo": "Crear Empleado"}

    def post(self, request, *args, **kwargs):
            # Capturar los datos del formulario
            dni = request.POST.get('dni')
            legajo = request.POST.get('legajo')
            nombre = request.POST.get('nombre')
            correoEmpleado = request.POST.get('email', '') 
            activo = request.POST.get('activo') == "True"  # Convertir a booleano

            autorizado = request.POST.get('autorizado', '')  # Campo opcional
            dniautorizado = request.POST.get('dniautorizado') or None  # Campo opcional
            correoAutorizado = request.POST.get('emailautorizado', '')  # Campo opcional

            autorizado2 = request.POST.get('autorizado2', '')  # Campo opcional
            dniautorizado2 = request.POST.get('dniautorizado2') or None # Campo opcional
            correoAutorizado2 = request.POST.get('emailautorizado2', '')  # Campo opcional
            # Verificar si el DNI o el legajo ya existen
            if Empleado.objects.filter(dni=dni).exists() or Empleado.objects.filter(legajo=legajo).exists():
                return render(request, 'empleado_create.html', {
                    'error1': Empleado.objects.filter(dni=dni).exists(),
                    'error2': Empleado.objects.filter(legajo=legajo).exists(),
                    'tipo': 'Crear Empleado'
                })

            # Crear el nuevo empleado
            nuevo_empleado = Empleado(
                dni=dni,
                legajo=legajo,
                nombre=nombre,
                correoEmpleado=correoEmpleado,
                activo=activo,
                autorizado=autorizado,
                dniautorizado=dniautorizado,  # Ya manejado correctamente
                correoAutorizado=correoAutorizado,
                autorizado2=autorizado2,
                dniautorizado2=dniautorizado2,  # Ya manejado correctamente
                correoAutorizado2=correoAutorizado2
            )
            nuevo_empleado.save()

            # 📧 Construir cuerpo del correo dinámicamente
            subject = "Bienvenido a la empresa"
            message = f"""
            Hola {nombre},

            Bienvenido a STIA. Estos son los datos registrados:

            - DNI: {dni}
            - Legajo: {legajo}
            - Activo: {"Sí" if activo else "No"}
            """

            # Agregar datos de los autorizados si existen
            if autorizado and dniautorizado:
                message += f"""
                
            Información del Autorizado 1:
            - Nombre: {autorizado}
            - DNI: {dniautorizado}
            - Correo: {correoAutorizado if correoAutorizado else "No registrado"}
            """

            if autorizado2 and dniautorizado2:
                message += f"""
                
            Información del Autorizado 2:
            - Nombre: {autorizado2}
            - DNI: {dniautorizado2}
            - Correo: {correoAutorizado2 if correoAutorizado2 else "No registrado"}
            """

            message += """

            Cualquier duda, estamos a tu disposición.

            Saludos,
            El equipo de STIA.
            """

            recipients = [correoEmpleado] if correoEmpleado else []
            if correoAutorizado:
                recipients.append(correoAutorizado)
            if correoAutorizado2:
                recipients.append(correoAutorizado2)

            if recipients:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
            return redirect('ordenes:empleado_all')


class EmpleadoUpdateView(EmpleadoBaseView, UpdateView):
    template_name = 'empleado_update.html'
    model = Empleado
    fields = ['nombre', 'legajo', 'dni', 'correoEmpleado', 'empresa', 'activo',
                'autorizado', 'dniautorizado', 'correoAutorizado',
                'autorizado2','dniautorizado2', 'correoAutorizado2']
    success_url = reverse_lazy('ordenes:empleado_all')
    extra_context = {"tipo": "Actualizar Empleado"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresas'] = Empresa.objects.filter(activo=True)  # Obtener empresas activas
        return context

    def form_valid(self, form):
        empleado = form.save()

        # 📧 Construir cuerpo del correo dinámicamente
        subject = "Actualización de datos"
        message = f"""
        Hola {empleado.nombre},

        Tus datos han sido actualizados. Aquí están los nuevos datos registrados:

        - DNI: {empleado.dni}
        - Legajo: {empleado.legajo}
        - Activo: {"Sí" if empleado.activo else "No"}
        """

        # Agregar información de los autorizados si existen
        if empleado.autorizado and empleado.dniautorizado:
            message += f"""
            
        Información del Autorizado 1:
        - Nombre: {empleado.autorizado}
        - DNI: {empleado.dniautorizado}
        - Correo: {empleado.correoAutorizado if empleado.correoAutorizado else "No registrado"}
        """

        if empleado.autorizado2 and empleado.dniautorizado2:
            message += f"""
            
        Información del Autorizado 2:
        - Nombre: {empleado.autorizado2}
        - DNI: {empleado.dniautorizado2}
        - Correo: {empleado.correoAutorizado2 if empleado.correoAutorizado2 else "No registrado"}
        """

        message += """

        Si no solicitaste este cambio, por favor comunícate con STIA.

        Saludos,
        El equipo de STIA.
        """


        recipients = [empleado.correoEmpleado] if empleado.correoEmpleado else []
        if empleado.correoAutorizado:
            recipients.append(empleado.correoAutorizado)
        if empleado.correoAutorizado2:
            recipients.append(empleado.correoAutorizado2)

        if recipients:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)

        return super().form_valid(form)
    
#def nuevaorden(request):
#    resultado = Empleado.objects.all()
#    resultado2 = Comercio.objects.all()
#    return render(request,"orden_create.html",{"nombres":resultado,"comercios":resultado2})

#  M A R G E N  #
class MargenBaseView(View):
    template_name = "margen.html"
    model         = Margen
    fields        = "__all__"
    margen =  Margen.objects.all()[:1]
    success_url   = reverse_lazy('ordenes:margen')
    extra_context = {"margen": margen}

class MargenListView(MargenBaseView,ListView):
    '''ESTO ME PERMITE CREAR UNA VISTA DEL MARGEN'''
    
class MargenUpdateView(MargenBaseView,UpdateView):
    template_name = 'margen_update.html'
    extra_context = {"tipo": "Actualizar Margen"}

class MargenCreateView(MargenBaseView,CreateView):
    template_name = 'margen_create.html'
    extra_context = {"tipo": "Crear Margen"}

    
        

# OTRAS FUNCIONES #
# PRE CONSULTA #
import datetime
from django.shortcuts import render
from django.db.models import Q
from .models import Empleado, Comercio, Orden, Margen

def preconsulta(request):
    empleados = Empleado.objects.filter(activo=True)
    comercios = Comercio.objects.filter(activo=True)
    busqueda = request.POST.get("buscarempleado")
    busqueda2 = request.POST.get("buscarcomercio") if not request.user.comercio else request.user.comercio.id

    mensajeerror = ""
    errorempleado = ""
    errorcomercio = ""

    empleado = Empleado.objects.filter(id=busqueda).first()
    comercio = Comercio.objects.filter(id=busqueda2).first()

    if not empleado:
        errorempleado = ' El empleado no existe.'
    if not comercio:
        errorcomercio = ' El comercio no existe.'
    
    mensajeerror += errorempleado + errorcomercio

    try:
        datoscorrectos = True
        ordenes = Orden.objects.all()
        margen = Margen.objects.first()
        hoy = datetime.date.today()
        mes = str(hoy.month).zfill(2)
        fechahoy = int(f"{hoy.year}{mes}")
        saldo = 0
        valorcuota = 0
        margendisponible = margen.margen if margen else 0
        limite = margendisponible

        if empleado and comercio:
            ordenes = Orden.objects.filter(empleado_id=empleado.id)
            for orden in ordenes:
                valorcuota = orden.importe / orden.cuotas
                saldo += sum(valorcuota for i in range(orden.cuotas) if int(f"{hoy.year}{str(orden.fecha.month).zfill(2)}") >= fechahoy)

            margendisponible -= saldo
            return render(request, 'preconsulta.html', {
                'comercio': comercio,
                'comercios': comercios,
                'empleado': empleado,
                'empleados': empleados,
                'margen': f"{margendisponible:.2f}",
                'limite': limite,
                'datoscorrectos': datoscorrectos
            })

        return render(request, 'preconsulta.html', {'comercios': comercios, 'empleados': empleados, 'error': False})
    except Exception as e:
        print(f"Error en preconsulta: {e}")
        return render(request, 'preconsulta.html', {
            'comercios': comercios,
            'empleados': empleados,
            'error': True,
            'mensajeerror': mensajeerror
        })


# MARGEN EMPLEADO


def MargenEmpleado(request):
    error = False
    msjerror = ""
    try:
        busqueda = request.POST.get("margenempleado")
        empleados = Empleado.objects.filter(activo=True)
        margen_total = sum(m.margen for m in Margen.objects.all())  # Sumar todos los márgenes

        if busqueda:
            empleado = Empleado.objects.filter(id=busqueda).first()
            if not empleado:
                error = True
                msjerror = "El empleado no existe en la base de datos"
                return render(request, 'consulta_margen.html', {
                    'empleados': empleados,
                    'error': error,
                    'msjerror': msjerror
                })

            # Obtener las órdenes y deudas del empleado
            ordenes = Orden.objects.filter(empleado_id=busqueda)
            deudas = Deuda.objects.filter(empleado_id=busqueda, activo=True)

            # Crear un diccionario para almacenar los datos por año-mes
            datos_mensuales = defaultdict(lambda: {"compras": 0, "deudas": 0, "limite": margen_total})

            # Procesar las órdenes (compras)
            for orden in ordenes:
                valor_cuota = orden.importe / orden.cuotas if orden.cuotas else 0
                for i in range(orden.cuotas):
                    mes = orden.fecha.month + i
                    año = orden.fecha.year
                    if mes > 12:  # Ajustar el año si el mes sobrepasa diciembre
                        mes -= 12
                        año += 1
                    clave_mes = f"{año}{mes:02d}"
                    datos_mensuales[clave_mes]["compras"] += valor_cuota

            # Procesar las deudas
            for deuda in deudas:
                clave_mes = f"{deuda.year}{deuda.mes:02d}"
                datos_mensuales[clave_mes]["deudas"] += deuda.importe

            # Extender los resultados a los próximos 11 meses
            hoy = datetime.now()
            for i in range(12):  # Incluye el mes actual y los próximos 11 meses
                mes = hoy.month + i
                año = hoy.year
                if mes > 12:  # Ajustar el año si el mes sobrepasa diciembre
                    mes -= 12
                    año += 1
                clave_mes = f"{año}{mes:02d}"
                if clave_mes not in datos_mensuales:
                    datos_mensuales[clave_mes] = {"compras": 0, "deudas": 0, "limite": margen_total}

            # Calcular el límite disponible para cada mes
            for clave_mes, datos in datos_mensuales.items():
                datos["limite"] = margen_total - datos["compras"] - datos["deudas"]

            # Convertir los datos a una lista para renderizar en la tabla
            datos_mensuales_lista = [
                {"año_mes": clave, "compras": f"{datos['compras']:.2f}", "deudas": f"{datos['deudas']:.2f}", "limite": f"{datos['limite']:.2f}"}
                for clave, datos in sorted(datos_mensuales.items())
            ]

            # Enviar correo al empleado
            subject = "Consulta de Margen"
            message = f"""
            Hola {empleado.nombre},

            Aquí tienes la información de tu consulta de margen:

            """
            for dato in datos_mensuales_lista:
                message += f"Año-Mes: {dato['año_mes']}, Compras: {dato['compras']}, Deudas: {dato['deudas']}, Límite: {dato['limite']}\n"

            message += "\nSaludos,\nEl equipo de STIA."

            if empleado.correoEmpleado:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [empleado.correoEmpleado])

            return render(request, 'consulta_margen.html', {
                'empleado': empleado,
                'empleados': empleados,
                'datos_mensuales': datos_mensuales_lista,
                'margen_total': f"{margen_total:.2f}",
                'error': error,
                'msjerror': msjerror,
            })

        return render(request, 'consulta_margen.html', {'empleados': empleados})

    except Exception as e:
        error = True
        msjerror = f"Los datos ingresados son incorrectos: {str(e)}"
        return render(request, 'consulta_margen.html', {'empleados': empleados, 'error': error, 'msjerror': msjerror})

def ConsultaCompraEmpleado(request):
    error = False
    msjerror = ""
    empleados = Empleado.objects.all().filter(activo=True)

    if request.method == 'POST':
        try:
            busqueda = request.POST.get("empleado")
            fecha1 = request.POST.get("fecha1")
            fecha2 = request.POST.get("fecha2")
            msjerror1 = ""
            msjerror2 = ""

            if fecha1 > fecha2:
                error = True
                msjerror1 = "La fecha de inicio debe ser anterior a la fecha de fin."

            empleados = Empleado.objects.all()
            ordenes = Orden.objects.all()

            if busqueda:
                empleado = Empleado.objects.filter(Q(id__icontains=busqueda)).first()
                ordenes = Orden.objects.filter(Q(empleado_id=busqueda)).filter(fecha__range=(fecha1, fecha2)).order_by('-id')

                if not empleado:
                    error = True
                    msjerror2 = "El empleado no existe en la base de datos."
                msjerror += msjerror2 + msjerror1

                # Enviar correo al empleado
                if empleado and empleado.correoEmpleado:
                    subject = "Consulta de Compras"
                    message = f"""
                    Hola {empleado.nombre},

                    Aquí tienes la información de tus compras realizadas entre {fecha1} y {fecha2}:

                    """

                    for orden in ordenes:
                        message += f"\n- Fecha: {orden.fecha}, Importe: $ {orden.importe}, Cuotas: {orden.cuotas}, Comercio: {orden.comercio.comercio}"

                    message += "\nSaludos,\nEl equipo de STIA."
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [empleado.correoEmpleado])

                return render(request, 'consulta_compras.html', {
                    'empleados': empleados,
                    'orden': ordenes,
                    'error': error,
                    'msjerror': msjerror,
                    'empleado': empleado,
                    'fecha1': fecha1,
                    'fecha2': fecha2,
                })

            else:
                return render(request, 'consulta_compras.html', {'empleados': empleados})

        except Exception as e:
            error = True
            msjerror = f"Los datos ingresados son incorrectos: {str(e)}"
            return render(request, 'consulta_compras.html', {'error': error, 'msjerror': msjerror})

    if request.method == 'GET':
        return render(request, 'consulta_compras.html', {'empleados': empleados})



def OrdenEmpleado(request):
    error= False
    msjerror=""
    try:
        busqueda = request.POST.get("ordenempleado")
        ordenes=Orden.objects.all()
        grupo = list(request.user.groups.all())
        usuario = '[<Group: UsuarioAdmin>]'
        if str(grupo) == str(usuario):
            usuarioadmin=True
        else:
            usuarioadmin=False
        
        if busqueda:
            ordenes = Orden.objects.filter(Q(id=busqueda))
            if not(ordenes):
                error=True
                msjerror = "La Orden de Compra no existe en la base de datos"
            return render(request, 'consulta_orden.html',{'orden_list':ordenes,'grupo':grupo,
                                                'usuarioadmin':usuarioadmin,'error':error,'msjerror':msjerror})
        else:
            return render(request, 'consulta_orden.html',)
    
    except:
        error=True
        msjerror='Los datos ingresados son incorrectos'
        return render(request, 'consulta_orden.html',{'error':error,'msjerror':msjerror})

# impresion de comprobantes #

class Imprimir(View):
    success_url   = reverse_lazy('ordenes:orden_all')
    
    #def get(self,request,*args, **kwargs):
    def get(self,request,*args, **kwargs):
        #ultimaorden= Orden.objects.last()
        ultimaorden= Orden.objects.get(pk=self.kwargs['pk'])
        dni = ultimaorden.empleado.dni
        mes=ultimaorden.fecha.month
        year=ultimaorden.fecha.year
        context = {
                'id':ultimaorden.id,
                'empleado':ultimaorden.empleado.nombre,
                'comercio':ultimaorden.comercio.comercio,
                'importe':ultimaorden.importe,
                'cuotas':ultimaorden.cuotas,
                'fecha':ultimaorden.fecha,
                'valorcuota':ultimaorden.valorcuota,
                'mes':mes,
                'year':year,
                'dni':dni,
                'usuario':ultimaorden.usuario,
                'compro':ultimaorden.compro,
                'activa':ultimaorden.activo
                }
        html = render_to_string("pdf_orden.html", context)

        response = HttpResponse(content_type="application/pdf")
        #response["Content-Disposition"] = "attachment; report.pdf"
        response["Content-Disposition"] = f"inline; report.pdf"
        HTML(string=html).write_pdf(response)
        
        return response

class ImprimirUltima(View):
    
    success_url   = reverse_lazy('ordenes:orden_all')
    
    def get(self,request,*args, **kwargs):
        ultimaorden= Orden.objects.last()
        #ultimaorden= Orden.objects.get(pk=self.kwargs['pk'])
        context = {
                'id':ultimaorden.id,
                'empleado':ultimaorden.empleado.nombre,
                'comercio':ultimaorden.comercio,
                'importe':ultimaorden.importe,
                'cuotas':ultimaorden.cuotas,
                'fecha':ultimaorden.fecha,
                }
        html = render_to_string("pdf_orden.html", context)

        response = HttpResponse(content_type="application/pdf")
        #response["Content-Disposition"] = "attachment; report.pdf"
        response["Content-Disposition"] = f"inline; report.pdf"

        HTML(string=html).write_pdf(response)
        
        return response


from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Empleado

def Buscaempleado(request):
    if request.method == 'POST':
        buscaempleado = request.POST.get("updateempleado")

        # Buscar el empleado específico
        if buscaempleado:
            try:
                empleado = Empleado.objects.get(id=buscaempleado)
            except Empleado.DoesNotExist:
                empleado = None  # Si no se encuentra, evita el error

            return render(request, 'empleado.html', {'empleado': empleado})
    
    # Si es GET o no hay búsqueda, mostrar todos
    empleado_list = Empleado.objects.all()
    return render(request, 'empleado.html', {'empleado_list': empleado_list})


def Buscaorden(request):
    if request.user.comercio:
        orden = Orden.objects.filter(comercio=request.user.comercio).order_by('-id')[:6]
    else:
        orden = Orden.objects.all().order_by('-id')[:6]
    grupo = request.user.groups.all()
    usuarioadmin = 'UsuarioAdmin'
    usuarioestarndar = 'UsuarioEstandar'
    if request.method == 'POST':

        buscaorden = request.POST.get("updateorden")
        
        if buscaorden:
            if request.user.comercio:
                updateorden = Orden.objects.filter(Q(id__icontains=buscaorden,comercio=request.user.comercio))
            else:
                updateorden = Orden.objects.filter(Q(id__icontains=buscaorden))

            return render(request, 'orden.html',{'orden':updateorden,'orden_list':orden,'grupo':grupo,
                                                'usuarioadmin':usuarioadmin,'usuarioestandar':usuarioestarndar})
                        
        else:
            return render(request, 'orden.html',{'orden':orden,})

    if request.method == 'GET':
        
        return render(request, 'orden.html',{'orden_list':orden,'grupo':grupo,
                                             'usuarioadmin':usuarioadmin,'usuarioestandar':usuarioestarndar})

##  LIQUIDACIONES ##

def Art34(request):
    years = ('2025','2026','2027','2028','2029','2030','2031','2032','2033','2034',
                '2035','2036','2037','2038','2039','2040')
    empresas = Empresa.objects.all().filter(activo=True)

    if request.method == 'POST':
        buscayear = request.POST.get("periodoyear")
        buscamonth = request.POST.get("periodomonth")
        empresa_id = request.POST.get("empresa")
        empresa = Empresa.objects.get(id=empresa_id)

        if (buscayear and buscamonth):
            fechainicio=str((int(buscayear)-2))+'-01-01'
            mesfin =str((int(buscamonth)+1))
            yearfin =str(int(buscayear))
            if int(mesfin)>12:
                mesfin = str(int(mesfin)-12)
                yearfin = str(int(buscayear)+1)
            if int(mesfin)<10:
                mesfin='0'+mesfin
            fechafin = yearfin+'-'+mesfin+'-01'
            periodo = buscayear+buscamonth

            # Filtrar empleados por la empresa seleccionada
            empleados = Empleado.objects.filter(empresa_id=empresa_id)

            # Obtener las órdenes dentro del rango de fechas
            ordenes =Orden.objects.filter(empleado__in=empleados,fecha__range=(fechainicio,fechafin)).order_by('empleado')
            deudas = Deuda.objects.filter(empleado__in=empleados,year=buscayear, mes=buscamonth,activo=True).order_by('empleado')
            

            liquidacion ={}
            total_general = 0

            # Procesar cada orden
            for orden in ordenes:
                if not orden.activo:
                    continue

                cuotas_restantes = orden.cuotas
                valor_cuota = orden.importe / orden.cuotas
                fecha_cuota = orden.fecha

                # Generar los períodos para las cuotas
                while cuotas_restantes > 0:
                    year = fecha_cuota.year
                    month = fecha_cuota.month
                    periodo_cuota = f"{year}{month:02d}"  # Formato YYYYMM

                    # Si el período coincide con el buscado, sumar el valor de la cuota
                    if periodo_cuota == periodo:
                        if orden.empleado not in liquidacion:
                            liquidacion[orden.empleado] = 0
                        liquidacion[orden.empleado] += valor_cuota
                        total_general += valor_cuota

                    # Avanzar al siguiente mes
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                    fecha_cuota = date(year, month, 1)
                    cuotas_restantes -= 1
                    
            # Procesar cada deuda
            for deuda in deudas:
                if deuda.empleado not in liquidacion:
                    liquidacion[deuda.empleado] = 0
                liquidacion[deuda.empleado] += deuda.importe
                total_general += deuda.importe

            return render(request, 'liquidacion_art34.html', {
                'periodo': periodo,
                'years': years,
                'empresa': empresa,
                'empresas': empresas,
                'liquidacion': liquidacion,
                'total': total_general
            })

        else:
            return render(request, 'liquidacion_art34.html', {'periodo': '', 'years': years,'empresas':empresas})

    if request.method == 'GET':
        periodo = request.GET.get("periodoart34")
        empresa = request.GET.get("empresaart34")

        if periodo:
            buscayear = periodo[:4]
            buscamonth = periodo[4:6]
            fechainicio = f"{int(buscayear) - 2}-01-01"
            fechafin = f"{buscayear}-{int(buscamonth) + 1:02d}-01"
            ordenes = Orden.objects.filter(fecha__range=(fechainicio, fechafin)).order_by('empleado')

            liquidacion = {}
            total_general = 0

            for orden in ordenes:
                if not orden.activo:
                    continue

                cuotas_restantes = orden.cuotas
                valor_cuota = orden.importe / orden.cuotas
                fecha_cuota = orden.fecha

                while cuotas_restantes > 0:
                    year = fecha_cuota.year
                    month = fecha_cuota.month
                    periodo_cuota = f"{year}{month:02d}"  # Formato YYYYMM

                    if periodo_cuota == periodo:
                        if orden.empleado not in liquidacion:
                            liquidacion[orden.empleado] = 0
                        liquidacion[orden.empleado] += valor_cuota
                        total_general += valor_cuota

                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                    fecha_cuota = date(year, month, 1)
                    cuotas_restantes -= 1

            # Generar el PDF
            context = {
                'empresa': empresa,
                'periodo': periodo,
                'liquidacion': liquidacion,
                'total': total_general
            }
            html = render_to_string("pdf_art34.html", context)
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = f"inline; filename=art34_{periodo}.pdf"
            HTML(string=html).write_pdf(response)
            return response

    return render(request, 'liquidacion_art34.html', {'years': years,'empresas':empresas})


def ComercioLiquidacion(request):
    years = ('2025', '2026', '2027', '2028', '2029', '2030', '2031', '2032', '2033', '2034',
             '2035', '2036', '2037', '2038', '2039', '2040')

    if request.method == 'POST':
        buscayear = request.POST.get("periodoyearcomercio")
        buscamonth = request.POST.get("periodomonthcomercio")

        if buscayear and buscamonth:
            fechainicio = f"{int(buscayear) - 2}-01-01"
            mesfin = str(int(buscamonth) + 1)
            yearfin = str(int(buscayear))
            if int(mesfin) > 12:
                mesfin = str(int(mesfin) - 12)
                yearfin = str(int(buscayear) + 1)
            if int(mesfin) < 10:
                mesfin = f"0{mesfin}"
            fechafin = f"{yearfin}-{mesfin}-01"
            periodo = f"{buscayear}{buscamonth}"

            # Obtener las órdenes dentro del rango de fechas
            ordenes = Orden.objects.filter(fecha__range=(fechainicio, fechafin)).order_by('comercio')
            deudas = Deuda.objects.filter(year=buscayear, mes=buscamonth, activo=True).order_by('comercio')

            liquidacion = {}
            total_general = 0

            # Procesar cada orden
            for orden in ordenes:
                if not orden.activo:
                    continue

                cuotas_restantes = orden.cuotas
                valor_cuota = orden.importe / orden.cuotas
                fecha_cuota = orden.fecha

                # Generar los períodos para las cuotas
                while cuotas_restantes > 0:
                    year = fecha_cuota.year
                    month = fecha_cuota.month
                    periodo_cuota = f"{year}{month:02d}"  # Formato YYYYMM

                    # Si el período coincide con el buscado, sumar el valor de la cuota
                    if periodo_cuota == periodo:
                        if orden.comercio not in liquidacion:
                            liquidacion[orden.comercio] = 0
                        liquidacion[orden.comercio] += valor_cuota
                        total_general += valor_cuota

                    # Avanzar al siguiente mes
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                    fecha_cuota = date(year, month, 1)
                    cuotas_restantes -= 1

            # Procesar cada deuda
            for deuda in deudas:
                if deuda.comercio not in liquidacion:
                    liquidacion[deuda.comercio] = 0
                liquidacion[deuda.comercio] += deuda.importe
                total_general += deuda.importe

            # Calcular el descuento y el total a pagar por comercio
            liquidacion_detallada = {}
            for comercio, importe in liquidacion.items():
                descuento = importe * Decimal(0.05)  # 5% de descuento
                total_a_pagar = importe - descuento
                liquidacion_detallada[comercio] = {
                    'importe': importe,
                    'descuento': descuento,
                    'total_a_pagar': total_a_pagar
                }

            total_a_pagar_general = total_general - (total_general * Decimal(0.05))

            return render(request, 'liquidacion_comercios.html', {
                'periodo': periodo,
                'years': years,
                'liquidacion': liquidacion_detallada,
                'total_a_pagar_general': total_a_pagar_general
            })

        else:
            return render(request, 'liquidacion_comercios.html', {'periodo': '', 'years': years})

    if request.method == 'GET':
        periodo = request.GET.get("periodocomercio")

        if periodo:
            buscayear = periodo[:4]
            buscamonth = periodo[4:6]
            fechainicio = f"{int(buscayear) - 2}-01-01"
            fechafin = f"{buscayear}-{int(buscamonth) + 1:02d}-01"
            ordenes = Orden.objects.filter(fecha__range=(fechainicio, fechafin)).order_by('comercio')
            deudas = Deuda.objects.filter(year=buscayear, mes=buscamonth, activo=True).order_by('comercio')

            liquidacion = {}
            total_general = 0

            # Procesar cada orden
            for orden in ordenes:
                if not orden.activo:
                    continue

                cuotas_restantes = orden.cuotas
                valor_cuota = orden.importe / orden.cuotas
                fecha_cuota = orden.fecha

                while cuotas_restantes > 0:
                    year = fecha_cuota.year
                    month = fecha_cuota.month
                    periodo_cuota = f"{year}{month:02d}"  # Formato YYYYMM

                    if periodo_cuota == periodo:
                        if orden.comercio not in liquidacion:
                            liquidacion[orden.comercio] = 0
                        liquidacion[orden.comercio] += valor_cuota
                        total_general += valor_cuota

                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                    fecha_cuota = date(year, month, 1)
                    cuotas_restantes -= 1

            # Procesar cada deuda
            for deuda in deudas:
                if deuda.comercio not in liquidacion:
                    liquidacion[deuda.comercio] = 0
                liquidacion[deuda.comercio] += deuda.importe
                total_general += deuda.importe

            # Calcular el descuento y el total a pagar por comercio
            liquidacion_detallada = {}
            for comercio, importe in liquidacion.items():
                descuento = importe * Decimal(0.05)  # 5% de descuento
                total_a_pagar = importe - descuento
                liquidacion_detallada[comercio] = {
                    'importe': importe,
                    'descuento': descuento,
                    'total_a_pagar': total_a_pagar
                }

            total_a_pagar_general = total_general - (total_general * Decimal(0.05))

            # Generar el PDF
            context = {
                'periodo': periodo,
                'liquidacion': liquidacion_detallada,
                'total_a_pagar_general': total_a_pagar_general
            }
            html = render_to_string("pdf_comercio.html", context)
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = f"inline; filename=comercio_liquidacion_{periodo}.pdf"
            HTML(string=html).write_pdf(response)
            return response

    return render(request, 'liquidacion_comercios.html', {'years': years})



def orden_update(request, id):
  orden = Orden.objects.get(id=id)
  template = loader.get_template('orden_update.html')
  context = {
    'orden': orden,'tipo':'Actualiza Orden'
  }
  return HttpResponse(template.render(context, request))

def orden_updaterecord(request, id):
  activo = request.POST['activo']
  #empleado = request.POST['empleado']
  #comercio = request.POST['comercio']
  #importe = request.POST['importe']
  #cuotas = request.POST['cuotas']
  #valorcuota = request.POST['valorcuota']
  orden = Orden.objects.get(id=id)
  orden.activo = activo
  #orden.empleado = empleado
  #orden.comercio = comercio
  #orden.importe = importe
  #orden.cuotas = cuotas
  #orden.valorcuota = valorcuota
  orden.save()
  return HttpResponseRedirect(reverse('ordenes:orden_all'))
  

from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
import random
import string
from .models import CustomUser, Comercio



@login_required
def registrar_comercio(request):
    """comercios = Comercio.objects.all()  # Obtiene todos los comercios"""
    comercios = Comercio.objects.filter(customuser__isnull=True)  # Solo comercios no asociados
    if request.method == 'POST':
        
        
        # Capturar los datos del formulario
        email = request.POST.get('email')
        comercio = request.POST.get('comercio')
        nombre = email.split('@')[0]  # Extraer el nombre del correo
        contraseña = nombre + '1234++';
        
        # Crear el nuevo usuario
        usuario = CustomUser(
            username=email,
            email=email,
            password=contraseña,
            comercio_id=comercio
        )
        usuario.set_password(contraseña)
        
        usuario.save()

        # 📧 Enviar correo con los datos y la contraseña
        subject = "Registro Exitoso - Acceso a la Plataforma STIA ordenes"
        message = f"""
        Hola {usuario.comercio.comercio},

        Te damos la bienvenida a nuestra plataforma. Estos son tus datos de acceso:

        - Usuario: {usuario.username}
        - Correo electrónico: {usuario.email}
        - Contraseña temporal: {contraseña}

        Recomendamos cambiar tu contraseña en tu primer inicio de sesión.

        Si tienes alguna consulta, contáctanos.

        Saludos,
        El equipo de STIA.
        """

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.email])

        return redirect('ordenes:usuarios_lista')

    return render(request, 'usuarios_registro.html', {'comercios': comercios})


@login_required
def lista_usuarios(request):
    usuarios = CustomUser.objects.all()
    return render(request, 'usuarios_lista.html', {'usuarios': usuarios})


@login_required
def usuarios_editar(request, usuario_id):
    usuario = get_object_or_404(CustomUser, id=usuario_id)
    comercios = Comercio.objects.all()

    if request.method == 'POST':
        nuevo_email = request.POST.get('email')
        comercio_id = request.POST.get('comercio')

        # Verificar si el correo ya existe en otro usuario
        if CustomUser.objects.filter(email=nuevo_email).exclude(id=usuario.id).exists():
            messages.error(request, "El correo electrónico ya está en uso por otro usuario.")
            return render(request, 'usuarios_editar.html', {'usuario': usuario, 'comercios': comercios})

        # Actualizar el correo electrónico
        usuario.email = nuevo_email

        # Actualizar el nombre de usuario con el nuevo correo electrónico
        usuario.username = usuario.email

        # Verificar si se proporcionó una nueva contraseña
        password = request.POST.get('password')
        nueva_contrasena = None
        if password:
            usuario.set_password(password)
            nueva_contrasena = password  # Guardamos la contraseña para incluirla en el correo

        usuario.save()

        # 📧 Enviar correo notificando los cambios
        subject = "Actualización de Datos"
        message = f"""
        Hola {usuario.comercio.comercio},

        Tus datos han sido actualizados correctamente. Aquí están los nuevos datos:

        - Nombre de usuario: {usuario.username}
        - Correo electrónico: {usuario.email}
        """

        # Incluir la nueva contraseña si se cambió
        if nueva_contrasena:
            message += f"\n- Nueva contraseña: {nueva_contrasena}\n\nPor favor, guárdala en un lugar seguro."

        message += "\nSi no realizaste esta actualización, por favor contáctanos.\n\nSaludos,\nEl equipo de administración."

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.email])

        return redirect('ordenes:usuarios_lista')

    return render(request, 'usuarios_editar.html', {'usuario': usuario, 'comercios': comercios})

from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth import logout

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'usuarios_cambio_pass.html'
    success_url = reverse_lazy('login')  # Redirige al login después del cambio

    def form_valid(self, form):
        # Enviar correo al usuario
        user = self.request.user
        subject = "Cambio de Contraseña"
        message = f"""
        Hola {user.username},

        Tu contraseña ha sido cambiada exitosamente. Si no realizaste este cambio, por favor contáctanos de inmediato.

        Saludos,
        El equipo de STIA.
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        # Hacer logout del usuario
        logout(self.request)

        return super().form_valid(form)
    
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType



@login_required
def admin_list(request):
    usuarios = CustomUser.objects.filter(comercio__isnull=True,is_superuser=False)
    return render(request, 'admin_list.html', {'usuarios': usuarios})

@login_required
def admin_create(request):
    
    if request.method == 'POST':
        
        
        # Capturar los datos del formulario
        username = request.POST.get('username')
        email = request.POST.get('email')
        tipo_acceso = request.POST.get('tipo_acceso')
        nombre = email.split('@')[0]  # Extraer el nombre del correo
        contraseña = nombre + '1234++';
        
        # Crear el nuevo usuario
        usuario = CustomUser(
            username=username,
            email=email,
            password=contraseña,
            comercio_id=None,
            tipo_acceso=tipo_acceso
        )
        usuario.set_password(contraseña)
        
        usuario.save()

        # 📧 Enviar correo con los datos y la contraseña
        subject = "Registro Exitoso - Acceso a la Plataforma STIA ordenes"
        message = f"""
        Hola {usuario.username},

        Te damos la bienvenida a nuestra plataforma. Estos son tus datos de acceso:

        - Usuario: {usuario.username}
        - Correo electrónico: {usuario.email}
        - Contraseña temporal: {contraseña}

        Recomendamos cambiar tu contraseña en tu primer inicio de sesión.

        Si tienes alguna consulta, contáctanos.

        Saludos,
        El equipo de STIA.
        """

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.email])

        return redirect('ordenes:admin_list')

    return render(request, 'admin_create.html',{'tipo_acceso_choices': CustomUser.TIPO_ACCESO_CHOICES})

@login_required
def admin_edit(request, usuario_id):
    usuario = get_object_or_404(CustomUser, id=usuario_id)
    if request.method == 'POST':
        email = request.POST.get('email')
        print('email',email)
        tipo_acceso = request.POST.get('tipo_acceso')
        print('tipo acceso',tipo_acceso)
        nombre = request.POST.get('nombre')
        print('nombre',nombre)

        # Verificar si el correo ya existe en otro usuario
        if CustomUser.objects.filter(email=email).exclude(id=usuario.id).exists():
            messages.error(request, "El correo electrónico ya está en uso por otro usuario.")
            return render(request, 'usuarios_editar.html', {'usuario': usuario})

        # Actualizar el correo electrónico
        usuario.email = email

        # Actualiza Nivel
        usuario.tipo_acceso = tipo_acceso
        usuario.username = nombre


        # Actualizar el nombre de usuario con el nuevo correo electrónico

        # Verificar si se proporcionó una nueva contraseña
        password = request.POST.get('password')
        print('password',password)
        nueva_contrasena = None
        if password:
            usuario.set_password(password)
            nueva_contrasena = password  # Guardamos la contraseña para incluirla en el correo

        usuario.save()

        # 📧 Enviar correo notificando los cambios
        subject = "Actualización de Datos"
        message = f"""
        Hola {usuario.username},

        Tus datos han sido actualizados correctamente. Aquí están los nuevos datos:

        - Nombre de usuario: {usuario.username}
        - Correo electrónico: {usuario.email}
        """

        # Incluir la nueva contraseña si se cambió
        if nueva_contrasena:
            message += f"\n- Nueva contraseña: {nueva_contrasena}\n\nPor favor, guárdala en un lugar seguro."

        message += "\nSi no realizaste esta actualización, por favor contáctanos.\n\nSaludos,\nEl equipo de administración."

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.email])

        return redirect('ordenes:admin_list')

    return render(request, 'admin_edit.html', {'usuario': usuario,'tipo_acceso_choices': CustomUser.TIPO_ACCESO_CHOICES})

from .models import Deuda

class DeudaListView(ListView):
    model = Deuda
    template_name = 'deuda_list.html'
    context_object_name = 'deudas'
    ordering = ['year', 'mes', 'empleado']

def DeudaCreateView(request):
    empleados = Empleado.objects.all().filter(activo=True)
    comercios = Comercio.objects.all().filter(activo=True)
    meses=[('01','Enero'),('02','Febrero'),('03','Marzo'),('04','Abril'),('05','Mayo'),('06','Junio'),('07','Julio'),('08','Agosto'),('09','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')]
    years = ('2025', '2026', '2027', '2028', '2029', '2030', '2031', '2032', '2033', '2034',
             '2035', '2036', '2037', '2038', '2039', '2040')

    if request.method == 'POST':
        # capturar los datos del formulario
        empleado = request.POST.get('empleado')
        comercio= request.POST.get('comercio')
        importe = request.POST.get('importe')
        year = request.POST.get('year')
        mes = request.POST.get('mes')

        # Crear el nuevo usuario
        deuda = Deuda(
            empleado_id=empleado,
            comercio_id=comercio,
            importe=importe,
            year=year,
            mes=mes,
            activo=True
        )
        
        deuda.save()

        return redirect('ordenes:deuda_list')
    
    return render(request, 'deuda_create.html', {'empleados': empleados, 'comercios': comercios, 'meses': meses, 'years': years})
    
    

def DeudaUpdate(request, id):
    # Obtener la deuda o devolver un error 404 si no existe
    deuda = get_object_or_404(Deuda, id=id)

    if request.method == 'POST':
        # Capturar los datos enviados por el formulario
        importe = request.POST.get('importe').replace(',', '.')  # Reemplazar coma por punto
        activo = request.POST.get('activo') == 'True'  # Convertir el valor a booleano

        # Actualizar los campos de la deuda
        deuda.importe = float(importe)  # Convertir el importe a un número decimal
        deuda.activo = activo
        deuda.save()

        # Redirigir a la lista de deudas después de guardar
        return redirect('ordenes:deuda_list')

    # Si el método es GET, renderizar el formulario con los datos actuales de la deuda
    return render(request, 'deuda_update.html', {'deuda': deuda})


def ComunicadoMasivoView(request):
    if request.method == 'POST':
        # Capturar los datos del formulario
        asunto = request.POST.get('asunto')
        cuerpo = request.POST.get('cuerpo')

        # Obtener los correos de los empleados activos
        empleados_activos = Empleado.objects.filter(activo=True)
        correos = [empleado.correoEmpleado for empleado in empleados_activos]

        if not correos:
            messages.error(request, "No hay empleados activos para enviar el comunicado.")
            return redirect('ordenes:comunicado_masivo')

        # Enviar el correo
        try:
            send_mail(
                asunto,
                cuerpo,
                settings.DEFAULT_FROM_EMAIL,
                correos,
                fail_silently=False,
            )
            messages.success(request, "El comunicado se envió correctamente a los empleados activos.")
        except Exception as e:
            messages.error(request, f"Error al enviar el comunicado: {str(e)}")

        return redirect('ordenes:comunicado_masivo')

    return render(request, 'comunicado_masivo.html')

def EmpleadoEmailView(request, empleado_id):
    # Obtener el empleado o devolver un error 404 si no existe
    empleado = get_object_or_404(Empleado, id=empleado_id)

    if request.method == 'POST':
        # Capturar los datos del formulario
        asunto = request.POST.get('asunto')
        cuerpo = request.POST.get('cuerpo')

        # Enviar el correo
        try:
            send_mail(
                asunto,
                cuerpo,
                settings.DEFAULT_FROM_EMAIL,
                [empleado.correoEmpleado],
                fail_silently=False,
            )
            messages.success(request, f"El correo se envió correctamente a {empleado.nombre}.")
        except Exception as e:
            messages.error(request, f"Error al enviar el correo: {str(e)}")

        return redirect('ordenes:empleado_all')

    return render(request, 'empleado_email.html', {'empleado': empleado})


from django.http import HttpResponse
from weasyprint import HTML

def ImprimirMargen(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    margen_total = sum(m.margen for m in Margen.objects.all())
    ordenes = Orden.objects.filter(empleado_id=empleado_id)
    deudas = Deuda.objects.filter(empleado_id=empleado_id, activo=True)

    # Crear un diccionario para almacenar los datos por año-mes
    datos_mensuales = defaultdict(lambda: {"compras": 0, "deudas": 0, "limite": margen_total})

    # Procesar las órdenes (compras)
    for orden in ordenes:
        valor_cuota = orden.importe / orden.cuotas if orden.cuotas else 0
        for i in range(orden.cuotas):
            mes = orden.fecha.month + i
            año = orden.fecha.year
            if mes > 12:
                mes -= 12
                año += 1
            clave_mes = f"{año}{mes:02d}"
            datos_mensuales[clave_mes]["compras"] += valor_cuota

    # Procesar las deudas
    for deuda in deudas:
        clave_mes = f"{deuda.year}{deuda.mes:02d}"
        datos_mensuales[clave_mes]["deudas"] += deuda.importe

    # Calcular el límite disponible para cada mes
    for clave_mes, datos in datos_mensuales.items():
        datos["limite"] = margen_total - datos["compras"] - datos["deudas"]

    datos_mensuales_lista = [
        {"año_mes": clave, "compras": f"{datos['compras']:.2f}", "deudas": f"{datos['deudas']:.2f}", "limite": f"{datos['limite']:.2f}"}
        for clave, datos in sorted(datos_mensuales.items())
    ]

    # Renderizar el PDF
    context = {
        'empleado': empleado,
        'datos_mensuales': datos_mensuales_lista,
        'margen_total': f"{margen_total:.2f}",
    }
    html = render_to_string("pdf_margen.html", context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=margen_{empleado.nombre}.pdf"
    HTML(string=html).write_pdf(response)
    return response


def ImprimirCompras(request, empleado_id, fecha1, fecha2):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    ordenes = Orden.objects.filter(empleado_id=empleado_id, fecha__range=(fecha1, fecha2)).order_by('-id')

    # Renderizar el PDF
    context = {
        'empleado': empleado,
        'ordenes': ordenes,
        'fecha1': fecha1,
        'fecha2': fecha2,
    }
    html = render_to_string("pdf_compras.html", context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=compras_{empleado.nombre}.pdf"
    HTML(string=html).write_pdf(response)
    return response

from .models import Empresa

class EmpresaListView(ListView):
    model = Empresa
    template_name = 'empresa_list.html'  # Nombre del archivo HTML para la lista
    context_object_name = 'empresas'  # Nombre del contexto en la plantilla

def crear_empresa(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')

        Empresa.objects.create(
            nombre=nombre,
            direccion=direccion,
            telefono=telefono,
            activo=True
        )
        return redirect('ordenes:empresa_list')  # Redirigir después de crear la empresa

    return render(request, 'empresa_create.html')

def empresa_update(request, id):
    # Obtener la deuda o devolver un error 404 si no existe
    empresa = get_object_or_404(Empresa, id=id)

    if request.method == 'POST':
        # Capturar los datos enviados por el formulario
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')
        activo = request.POST.get('activo') == 'True'  # Convertir el valor a booleano

        # Actualizar los campos de la deuda
        empresa.direccion = direccion
        empresa.telefono = telefono
        empresa.activo = activo
        empresa.save()
        # Redirigir a la lista de deudas después de guardar
        return redirect('ordenes:empresa_list')

    # Si el método es GET, renderizar el formulario con los datos actuales de la deuda
    return render(request, 'empresa_update.html', {'empresa': empresa})

def ConsultaDeudaTotalEmpleado(request):
    empleados = Empleado.objects.filter(activo=True)  # Obtener empleados activos
    deuda_total = 0
    empleado = None
    ordenes = []
    deudas = []

    if request.method == 'POST':
        empleado_id = request.POST.get("empleado")  # Obtener el empleado seleccionado

        if empleado_id:
            empleado = get_object_or_404(Empleado, id=empleado_id)

            # Calcular la deuda de las órdenes
            ordenes = Orden.objects.filter(empleado=empleado, activo=True)
            for orden in ordenes:
                cuotas_restantes = orden.cuotas
                valor_cuota = orden.importe / orden.cuotas if orden.cuotas else 0
                deuda_total += cuotas_restantes * valor_cuota

            # Calcular la deuda registrada
            deudas = Deuda.objects.filter(empleado=empleado, activo=True)
            for deuda in deudas:
                deuda_total += deuda.importe

    return render(request, 'consulta_deuda_total.html', {
        'empleados': empleados,
        'empleado': empleado,
        'ordenes': ordenes,
        'deudas': deudas,
        'deuda_total': deuda_total,
    })


def ConsultaDeudaPDF(request):
    empleado_id = request.GET.get("empleado_id")
    empleado = get_object_or_404(Empleado, id=empleado_id)

    # Calcular la deuda total
    deuda_total = 0
    ordenes = Orden.objects.filter(empleado=empleado, activo=True)
    deudas = Deuda.objects.filter(empleado=empleado, activo=True)

    for orden in ordenes:
        cuotas_restantes = orden.cuotas
        valor_cuota = orden.importe / orden.cuotas if orden.cuotas else 0
        deuda_total += cuotas_restantes * valor_cuota

    for deuda in deudas:
        deuda_total += deuda.importe

    # Generar el PDF
    context = {
        'empleado': empleado,
        'ordenes': ordenes,
        'deudas': deudas,
        'deuda_total': deuda_total,
    }
    html = render_to_string("pdf_deuda_total.html", context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=deuda_total_{empleado.nombre}.pdf"
    HTML(string=html).write_pdf(response)
    return response