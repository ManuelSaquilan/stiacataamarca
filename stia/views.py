from django.views.generic import TemplateView

class Landing(TemplateView):
    template_name = "page/landingpage.html"

class Consultas(TemplateView):
    template_name = "page/consultas.html"

class About(TemplateView):
    template_name = "page/about.html"

