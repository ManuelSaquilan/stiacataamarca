from django.urls import path, include
from . import views

from .views import      OrdenListView\
                    ,   OrdenDetailView\
                    ,   OrdenCreateView\
                    ,   OrdenUpdateView\
                    ,   ComercioListView\
                    ,   ComercioDetailView\
                    ,   ComercioCreateView\
                    ,   ComercioUpdateView\
                    ,   EmpleadoListView\
                    ,   EmpleadoDetailView\
                    ,   EmpleadoCreateView\
                    ,   EmpleadoUpdateView\
                    ,   preconsulta\
                    ,   CrearOrden\
                    ,   Imprimir\
                    ,   ImprimirUltima\
                    ,   MargenEmpleado\
                    ,   OrdenEmpleado\
                    ,   ConsultaCompraEmpleado\
                    ,   Buscaempleado\
                    ,   Buscaorden\
                    ,   Art34\
                    ,   ComercioLiquidacion\
                    ,   orden_update\
                    ,   orden_updaterecord\
                    ,   MargenListView\
                    ,   MargenUpdateView\
                    ,   registrar_comercio\
                    ,   lista_usuarios\
                    ,   usuarios_editar\
                    ,   MargenCreateView\
                    ,   CustomPasswordChangeView\
                    ,   admin_list\
                    ,   admin_create\
                    ,   admin_edit\
                    ,   DeudaListView\
                    ,   DeudaUpdate\
                    ,   DeudaCreateView\
                    ,   ComunicadoMasivoView\
                    ,   EmpleadoEmailView\
                    ,   ImprimirMargen\
                    ,   ImprimirCompras\
                    ,   crear_empresa\
                    ,   EmpresaListView\
                    ,   empresa_update\
                    ,   ConsultaDeudaTotalEmpleado\
                    ,   ConsultaDeudaPDF
                    

from django.conf import settings
from django.contrib.staticfiles.urls import static
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from .forms import CustomPasswordChangeForm

app_name = "ordenes"

urlpatterns = [
    path("", login_required(Buscaorden), name="orden_all"),
    path("create/<int:empleado>/<int:comercio>/<margen>", CrearOrden,name="create_orden"),
    #path("create/", CrearOrden,name="create_orden"),
    path("<int:pk>/orden/detail/", OrdenDetailView.as_view(), name="orden_detail"),
    path("orden/update/<int:id>", orden_update, name="orden_update"),
    path('orden/update/orden_updaterecord/<int:id>', orden_updaterecord, name='orden_updaterecord'),
    path("comercio", login_required(ComercioListView.as_view()), name="comercio_all"),
    path("comercio/create/", ComercioCreateView.as_view(), name="comercio_create"),
    path("<int:pk>/comercio/detail/", ComercioDetailView.as_view(), name="comercio_detail"),
    path("<int:pk>/comercio/update/", ComercioUpdateView.as_view(), name="comercio_update"),
    #path("empleado", login_required(EmpleadoListView.as_view()), name="empleado_all"),
    path("empleado", login_required(Buscaempleado), name="empleado_all"),
    path("empleado/create/", EmpleadoCreateView.as_view(), name="empleado_create"),
    path("create/preconsulta/", preconsulta, name="preconsulta"),
    path("<int:pk>/empleado/detail/", EmpleadoDetailView.as_view(), name="empleado_detail"),
    path("<int:pk>/empleado/update/", EmpleadoUpdateView.as_view(), name="empleado_update"),
    path("<int:pk>/export/", Imprimir.as_view(), name="export_pdf"),
    path("export/", ImprimirUltima.as_view(), name="imprime_last"),
    path("consulta/margen/", MargenEmpleado, name="consulta_saldo"),
    path("consulta/orden/", OrdenEmpleado, name="consulta_orden"),
    path("consulta/compras/", ConsultaCompraEmpleado, name="consulta_compras"),
    path("liquidaciones/art34/", Art34, name="liquidacion_art34"),
    path("liquidaciones/comercios/", ComercioLiquidacion, name="liquidacion_comercios"),
    path("margen/", login_required(MargenListView.as_view()), name="margen"),
    path("margenupdate/<int:pk>", MargenUpdateView.as_view(), name="margen_update"),
    path('registrar_comercio/', registrar_comercio, name='usuarios_registrar'),
    path('lista/', lista_usuarios, name='usuarios_lista'),
    path('usuarios/editar/<int:usuario_id>/', usuarios_editar, name='usuarios_editar'),
    path('margencreate/', MargenCreateView.as_view(), name='margen_create'),
    path('cambio-contraseña/', CustomPasswordChangeView.as_view(
        template_name='usuarios_cambio_pass.html',
        form_class=CustomPasswordChangeForm,
        success_url=reverse_lazy('login')  # Redirige al login después del cambio
    ), name='password_change'),
    path('admin_list/', admin_list, name='admin_list'),
    path('admin_create/', admin_create, name='admin_create'),
    path('admin_edit/<int:usuario_id>/', admin_edit, name='admin_edit'),
    path('deuda/', DeudaListView.as_view(), name='deuda_list'),
    path('deuda/create/', DeudaCreateView, name='deuda_create'),
    path('deuda/update/<int:id>', DeudaUpdate, name='deuda_update'),
    path('comunicado-masivo/', ComunicadoMasivoView, name='comunicado_masivo'),
    path('empleado/email/<int:empleado_id>/', EmpleadoEmailView, name='empleado_email'),
    path('margen/imprimir/<int:empleado_id>/', ImprimirMargen, name='imprimir_margen'),
    path('compras/imprimir/<int:empleado_id>/<str:fecha1>/<str:fecha2>/', ImprimirCompras, name='imprimir_compras'),
    path('empresa/crear/', crear_empresa, name='empresa_create'),
    path('empresa/', EmpresaListView.as_view(), name='empresa_list'),
    path('empresa/update/<int:id>', empresa_update, name='empresa_update'),
    path('consulta-deuda-total/', ConsultaDeudaTotalEmpleado, name='consulta_deuda_total'),
    path('consulta-deuda-pdf/', ConsultaDeudaPDF, name='consulta_deuda_pdf'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

