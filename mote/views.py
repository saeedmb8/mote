from cached_property import cached_property

from django.views.generic.base import TemplateView
from django.http import HttpResponse
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.templatetags.static import PrefixNode
from django.utils.six.moves.urllib.parse import urljoin
from django.conf import settings

from mote import PROJECT_PATHS
from mote.models import Project, Aspect, Pattern, Element, Variation


class HomeView(TemplateView):

    template_name = "mote/home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        li = []
        for id, pth in PROJECT_PATHS.items():
			li.append(Project(id))
        li.sort(lambda a, b: cmp(a.metadata.get("position"), a.metadata.get("position")))
        context["projects"] = li
        return context


class ProjectView(TemplateView):
    """Detail view for a project"""

    template_name = "mote/project.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectView, self).get_context_data(**kwargs)
        context["project"] = Project(kwargs["project"])
        return context


class AspectView(TemplateView):
    """Detail view for an aspect"""

    template_name = "mote/aspect.html"

    def get_context_data(self, **kwargs):
        context = super(AspectView, self).get_context_data(**kwargs)
        project = Project(kwargs["project"])
        context["aspect"] = Aspect(kwargs["aspect"], project)
        return context


class PatternView(TemplateView):
    """Detail view for a pattern"""

    template_name = "mote/pattern.html"

    def get_context_data(self, **kwargs):
        context = super(PatternView, self).get_context_data(**kwargs)
        project = Project(kwargs["project"])
        aspect = Aspect(kwargs["aspect"], project)
        pattern = Pattern(kwargs["pattern"], aspect)
        context["pattern"] = pattern

        # A pattern may have an intro view. First look in the pattern itself,
        # then fall back to normal template resolution.
        template_names = (
            "%s/%s/src/patterns/%s/mote/intro.html" % (project.id, aspect.id, pattern.id),
            "mote/pattern/intros/%s.html" % pattern.id,
        )
        intro = None
        for template_name in template_names:
            # todo: dont' render it here, only in the template. Just check that it loads.
            try:
                intro = render_to_string(template_name, {})
                break
            except TemplateDoesNotExist:
                pass
        context["intro"] = intro

        return context


class ElementBaseView(TemplateView):

    @cached_property
    def element(self):
        project = Project(self.kwargs["project"])
        aspect = Aspect(self.kwargs["aspect"], project)
        pattern = Pattern(self.kwargs["pattern"], aspect)
        element = Element(self.kwargs["element"], pattern)
        return element

    def get_context_data(self, **kwargs):
        context = super(ElementBaseView, self).get_context_data(**kwargs)
        context["element"] = self.element
        context["static_root"] = urljoin(PrefixNode.handle_simple("STATIC_URL"), self.element.aspect.relative_path)
        return context


class ElementIndexView(ElementBaseView):
    """Index view for an element. Provides common UI around an element."""

    def get_template_names(self):
        return [self.element.index_template_name]


class ElementPartialView(ElementBaseView):
    """Element view with no wrapping html and body tags"""

    def get_template_names(self):
        return [self.element.template_name]


class ElementIframeView(ElementBaseView):
    """Element view suitable for rendering in an iframe"""

    def get_template_names(self):
        return [
            "%s/mote/element/iframe.html" % self.element.project.id,
            "mote/element/iframe.html"
        ]


class VariationBaseView(ElementBaseView):

    @cached_property
    def variation(self):
        return Variation(self.kwargs["variation"], self.element)

    def get_context_data(self, **kwargs):
        context = super(VariationBaseView, self).get_context_data(**kwargs)
        # Rename some variables so we can re-use templates
        context["original_element"] = self.element
        context["element"] = self.variation
        return context


class VariationPartialView(VariationBaseView):

    def get_template_names(self):
        return [self.variation.template_name]


class VariationIframeView(VariationBaseView):
    """Element view suitable for rendering in an iframe"""

    def get_template_names(self):
        return ["mote/element/iframe.html"]
