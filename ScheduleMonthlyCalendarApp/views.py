from django.shortcuts import render
from .mixins import MonthWithScheduleMixin
from django.views.generic import TemplateView
from .models import Schedule

# Create your views here.
class MonthWithScheduleCalendar(MonthWithScheduleMixin, TemplateView):
    template_name = 'month_with_schedule.html'
    model = Schedule
    date_field = 'date'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar_context = self.get_month_calendar()
        context.update(calendar_context)
        return context
