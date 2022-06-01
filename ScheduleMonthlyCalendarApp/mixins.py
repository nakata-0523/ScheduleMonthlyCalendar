import calendar
import itertools
import datetime
from collections import deque


class BaseCalendarMixin:
    """カレンダー関連Mixinの、基底クラス"""
    first_weekday = 0  # 0は月曜から、1は火曜から。6なら日曜日からになります。お望みなら、継承したビューで指定してください。
    week_names = ['月', '火', '水', '木', '金', '土', '日']  # これは、月曜日から書くことを想定します。['Mon', 'Tue'...

    def setup_calendar(self):
        """内部カレンダーの設定処理

        calendar.Calendarクラスの機能を利用するため、インスタンス化します。
        Calendarクラスのmonthdatescalendarメソッドを利用していますが、デフォルトが月曜日からで、
        火曜日から表示したい(first_weekday=1)、といったケースに対応するためのセットアップ処理です。

        """
        self._calendar = calendar.Calendar(self.first_weekday)

    def get_week_names(self):
        """first_weekday(最初に表示される曜日)にあわせて、week_namesをシフトする"""
        week_names = deque(self.week_names)
        week_names.rotate(-self.first_weekday)  # リスト内の要素を右に1つずつ移動...なんてときは、dequeを使うと中々面白いです
        return week_names
    
class MonthCalendarMixin(BaseCalendarMixin):
    #月間カレンダーの機能を提供するMixin

    def get_previous_month(self, date):
        #前月を返す
        if date.month == 1:
            return date.replace(year=date.year-1, month=12, day=1)
        else:
            return date.replace(month=date.month-1, day=1)

    def get_next_month(self, date):
        #次月を返す
        if date.month == 12:
            return date.replace(year=date.year+1, month=1, day=1)
        else:
            return date.replace(month=date.month+1, day=1)

    def get_month_days(self, date):
        #その月の全ての日を返す
        return self._calendar.monthdatescalendar(date.year, date.month)

    def get_current_month(self):
        #現在の月を返す
        month = self.kwargs.get('month')
        year = self.kwargs.get('year')
        if month and year:
            month = datetime.date(year=int(year), month=int(month), day=1)
        else:
            month = datetime.date.today().replace(day=1)
        return month
    
    def get_month_calendar(self):
        #月間カレンダー情報の入った辞書を返す
        self.setup_calendar()
        current_month = self.get_current_month()
        calendar_data = {
            'now': datetime.date.today(),
            'month_days': self.get_month_days(current_month),#その月の全ての日を返しています
            'month_current': current_month,#そのカレンダーが表示している月です(datetime.date型)
            'month_previous': self.get_previous_month(current_month),#currentの、前の月です(datetime.date型)
            'month_next': self.get_next_month(current_month),#currentの、次の月です(datetime.date型)
            'week_names': self.get_week_names(),#['月', '火', '水'...]といった曜日のリストを返します。これはBaseCalendarMixinで提供されています。
        }
        return calendar_data

class MonthWithScheduleMixin(MonthCalendarMixin):
    def get_month_schedules(self, start, end, days):
        #それぞれの人スケジュールを返す
        lookup = {
            #例えばdata__range:(1日, 31日)を動的に作る
            '{}__range'.format(self.date_field): (start, end)
        }
        #例えば、Shedule.objects.filter(data__range=(1日, 31日))になる
        queryset = self.model.objects.filter(**lookup)
        
        #{1日のdatetime: 1日のスケジュール全て、2日のdatetime: 2日の全て...}のような辞書を作る
        day_schedules = {day: [] for week in days for day in week}
        for schedule in queryset:
            schedule_data = getattr(schedule, self.date_field)
            day_schedules[schedule_data].append(schedule)
            
        #day_schedules辞書を週毎に分割する。[{1日: 1日のスケジュール...}, {8日: 8日のスケジュール...}, ...]
        #7個ずつ取り出して分割しています。
        size = len(day_schedules)
        return [{key: day_schedules[key] for key in itertools.islice(day_schedules, i, i+7)} for i in range(0, size, 7)]

    def get_month_calendar(self):
        calendar_context = super().get_month_calendar()
        month_days = calendar_context['month_days']
        month_first = month_days[0][0]
        month_last = month_days[-1][-1]
        calendar_context['month_day_schedules'] = self.get_month_schedules(
            month_first,
            month_last,
            month_days
        )
        return calendar_context