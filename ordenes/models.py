from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class Empresa(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, verbose_name="Nombre de la Empresa", null=False)
    direccion = models.CharField(max_length=100, verbose_name="Dirección", null=True, blank=True)
    telefono = models.CharField(max_length=20, verbose_name="Teléfono", null=True, blank=True)
    activo = models.BooleanField(verbose_name="Activo", default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "empresa"
        verbose_name_plural = "empresas"
        db_table = "empresa"
        ordering = ["nombre"]



class Comercio(models.Model):
    id = models.AutoField(primary_key=True)
    comercio = models.CharField(max_length=30,verbose_name='Comercio',null=False) # VERBOSE nombre de las filas en superususario #
    titular = models.CharField(max_length=30,verbose_name='Titular de Comercio',null=False)
    activo = models.BooleanField(verbose_name='Activo',null=True,default=True)

    def __str__(self):
        fila = "Comercio: "+" - "+ str(self.comercio)+" Activo: "+" - "+ str(self.activo)
        return fila
    
    def get_fields(self):
        return [
            (field.verbose_name, field.value_from_object(self))
            for field in self.__class__._meta.fields[1:]
        ]
    
    class Meta:
        verbose_name = 'Comercio'
        verbose_name_plural = 'Comercios'
        db_table = 'comercio'
        ordering = ['comercio']

class CustomUser(AbstractUser):
    comercio = models.ForeignKey('Comercio', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Comercio")
    TIPO_ACCESO_CHOICES = [
        ('tipo_1', 'Administrador Tipo full'),
        ('tipo_2', 'Administrador Tipo emite ordenes'),
        ('tipo_3', 'Administrador Tipo Comercio'),
    ]
    tipo_acceso = models.CharField(max_length=10, choices=TIPO_ACCESO_CHOICES, null=True, blank=True, verbose_name="Tipo de Acceso",default="tipo_3")

    def __str__(self):
        return f"{self.username} - {self.comercio.comercio if self.comercio else 'Sin comercio'} - {self.tipo_acceso}"                

class Empleado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, verbose_name="Nombre y Apellido", null=False)
    legajo = models.IntegerField(verbose_name="Legajo N°", null=False, unique=True)
    correoEmpleado = models.EmailField(max_length=50, verbose_name="Correo Electrónico", null=False)
    dni = models.IntegerField(verbose_name="DNI", null=False, unique=True)
    activo = models.BooleanField(verbose_name="Activo", null=True, default=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa", null=True, blank=True)  # Relación con Empresa
    autorizado = models.CharField(max_length=30, verbose_name="Nombre y Apellido Autorizado", blank=True)
    dniautorizado = models.IntegerField(verbose_name="DNI Autorizado", null=True, blank=True)
    correoAutorizado = models.EmailField(max_length=50, verbose_name="Correo Electrónico Autorizado", null=True, blank=True, default="")
    autorizado2 = models.CharField(max_length=30, verbose_name="Nombre y Apellido Autorizado", blank=True)
    dniautorizado2 = models.IntegerField(verbose_name="DNI Autorizado", null=True, blank=True)
    correoAutorizado2 = models.EmailField(max_length=50, verbose_name="Correo Electrónico Autorizado", null=True, blank=True, default="")

    def __str__(self):
        fila = f"Empleado: {self.nombre} - Empresa: {self.empresa.nombre if self.empresa else 'Sin empresa'} - Activo: {self.activo}"
        return fila

    class Meta:
        verbose_name = "empleado"
        verbose_name_plural = "empleados"
        db_table = "empleado"
        ordering = ["nombre"]

class Orden(models.Model):
    id = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(Empleado,on_delete=models.CASCADE,null=False, blank=False)
    comercio = models.ForeignKey(Comercio,on_delete=models.CASCADE,null=False, blank=False)
    importe = models.DecimalField(max_digits=10, decimal_places=2,verbose_name='Total Compra',null=False)
    cuotas = models.IntegerField(verbose_name='Cuotas',null=False)
    valorcuota = models.DecimalField(max_digits=10, decimal_places=2,verbose_name='Valor de Cuota',null=False)
    fecha = models.DateField(verbose_name='Fecha de Compra', auto_now=True,null=False)
    activo = models.BooleanField(verbose_name='Activo',null=True,default=True)
    usuario = models.CharField(verbose_name='Usuario de carga', max_length=25,null=True)
    compro = models.CharField(verbose_name='Persona que compró', max_length=25,null=True)
    
    
    def __str__(self):
        fila = "Empleado: " + str(self.empleado) + " - " + " Comercio: " + str(self.comercio) + " Importe: " + str(self.importe) + " Cuotas: " + str(self.cuotas)+ " Valor de Cuota: " + str(self.valorcuota) + " Fecha y hora: " + str(self.fecha)+ " Activa: " + str(self.activo)
        return fila
    
    def get_fields(self):
        return [
            (field.verbose_name, field.value_from_object(self))
            for field in self.__class__._meta.fields[1:]
        ]

    class Meta:
        verbose_name='orden'
        verbose_name_plural='ordenes'
        db_table = 'ordenes_orden'
    

class Margen(models.Model):
    id=models.AutoField(primary_key=True)
    margen = models.IntegerField(verbose_name='Margen',null=False)

    def __str__(self):
        fila = "Margen: " + str(self.margen)
        return fila

    class Meta:
        verbose_name='margen'
        verbose_name_plural='margenes'
        db_table = 'margen'

class Deuda(models.Model):
    id = models.AutoField(primary_key=True)
    importe = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Importe')
    year = models.IntegerField(verbose_name='Año')
    mes = models.IntegerField(verbose_name='Mes')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, verbose_name='Empleado')
    comercio = models.ForeignKey(Comercio, on_delete=models.CASCADE, verbose_name='Comercio')
    activo = models.BooleanField(verbose_name='Activo', default=True)

    def __str__(self):
        return f"Empleado: {self.empleado} - Comercio: {self.comercio} - Importe: {self.importe} - {self.mes}/{self.year}"

    class Meta:
        verbose_name = 'deuda'
        verbose_name_plural = 'deudas'
        db_table = 'deuda'
        ordering = ['year', 'mes', 'empleado']


