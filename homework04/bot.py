import requests
import config
from datetime import datetime, date
import telebot
from bs4 import BeautifulSoup

days = ['', '/monday', '/tuesday', '/wednesday',
        '/thursday', '/friday', '/saturday', '/sunday']
bot = telebot.TeleBot(config.access_token)

named_days = ['', 'Понедельник', 'Вторник', 'Среда',
              'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


def get_page(group, week=''):
    if week:
        week = str(week) + '/'
    url = f'{config.domain}/{group}/{week}raspisanie_zanyatiy_{group}.htm'
    response = requests.get(url)
    web_page = response.text
    return web_page


def parse_schedule_for_a_day(web_page, day_num):
    soup = BeautifulSoup(web_page, "html5lib")

    # Получаем таблицу с расписанием на день недели
    schedule_table = soup.find("table", attrs={"id": day_num + "day"})

    # Время проведения занятий
    times_list = schedule_table.find_all("td", attrs={"class": "time"})
    times_list = [time.span.text for time in times_list]

    # Место проведения занятий
    locations_list = schedule_table.find_all("td", attrs={"class": "room"})
    locations_list = [room.span.text for room in locations_list]

    # Название дисциплин и имена преподавателей
    lessons_list = schedule_table.find_all("td", attrs={"class": "lesson"})
    lessons_list = [lesson.text.split('\n\n') for lesson in lessons_list]
    lessons_list = [', '.join([info for info in lesson_info if info]) for lesson_info in lessons_list]

    return times_list, locations_list, lessons_list


@bot.message_handler(commands=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'])
def get_schedule(message):
    """ Получить расписание на указанный день """
    try:
        info = message.text.split()
        if len(info) == 3:
            day, week, group = info
            web_page = get_page(group, week)
        else:
            day, group = info
            web_page = get_page(group)
        #name_day = rus_days[days.index(day)]
        day = str(days.index(day))
    except:
        bot.send_message(message.chat.id, 'Я не понял что вы написали Т.Т')
        return None

    try:
        times_lst, locations_lst, lessons_lst = parse_schedule_for_a_day(web_page, day)
        resp = ''
        for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):
            resp += '<b>{}</b>, {}, {}\n'.format(time, location, lesson)
    except:
        bot.send_message(message.chat.id, 'Сегодня нет занятий, отдыхайте.')
        return None

    bot.send_message(message.chat.id, resp, parse_mode='HTML')


def week_day(num_week, num_day):
    week = 1 if num_week % 2 else 2
    week = 2 if (week == 1 and num_day > 7) else 1
    day = 1 if num_day > 7 else str(num_day)

    return week, day


@bot.message_handler(commands=['near'])
def get_near_lesson(message):
    """ Получить ближайшее занятие """

    try:
        _, group = message.text.split()
        week = date.today().isocalendar()[1]
        w_day = date.today().isocalendar()[2]
        week, day = week_day(week, w_day)
        time_now = datetime.strftime(datetime.now(), "%H:%M")
        time_mas = time_now.split(":")
        time_now = str(int(time_mas[0]) + 3) + ":" + time_mas[1]
        web_page = get_page(group, str(week))
        resp = f' Следующее занятие :\n'
        i = 1
    except:
        bot.send_message(message.chat.id, 'Я не понял что вы написали Т.Т')
        return None

    try:
        times_lst, locations_lst, lessons_lst = parse_schedule_for_a_day(web_page, day)

        for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):

            class_time = datetime.strftime(
                datetime.strptime(time[:4], "%H:%M"), "%H:%M")
            if class_time > time_now:
                resp += f'<b>{time}</b>\n {location}\n {lesson}\n'
                i += 1
                break
        if i == 1:
            w_day = date.today().isocalendar()[2] + 1
            week, day = week_day(week, w_day)
            times_lst, locations_lst, lessons_lst = parse_schedule_for_a_day(web_page, day)
            while parse_schedule_for_a_day(web_page, day) == None:
                w_day += 1
                print(week, w_day)
                week, day = week_day(week, w_day)
                print(week, day)
                times_lst, locations_lst, lessons_lst = parse_schedule_for_a_day(web_page, day)
            #name_day = rus_days[int(day)]
            resp = f'<b>{times_lst[0]}</b>\n {locations_lst[0]}\n {lessons_lst[0]}\n'
    except:
        resp = 'У вас нет занятий в ближайшее время.'
    bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['tommorow'])
def get_tommorow(message):
    """ Получить расписание на следующий день """

    _, group = message.text.split()
    week = date.today().isocalendar()[1]
    w_day = date.today().isocalendar()[2] + 1
    week, day = week_day(week, w_day)

    try:
        web_page = get_page(group, str(week))
    except:
        bot.send_message(message.chat.id, 'Я не понял что вы написали Т.Т')
        return None

    try:
        times_lst, locations_lst, lessons_lst = parse_schedule_for_a_day(web_page, day)
        resp = ''
        for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):
            resp += f'<b>{time}</b>\n {location}\n {lesson}\n'
        bot.send_message(message.chat.id, resp, parse_mode='HTML')

    except:
        resp = 'Завтра нет пар'
        bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['all'])
def get_all_schedule(message):
    """ Получить расписание на всю неделю для указанной группы """
    try:
        info = message.text.split()
        if len(info) == 3:
            _, week, group = info
            web_page = get_page(group, week)
        else:
            _, group = info
            web_page = get_page(group)
        times_lst, locations_lst, lessons_lst = parse_schedule_for_a_day(web_page, '1')
    except:
        bot.send_message(
            message.chat.id, 'Я не понял что вы написали Т.Т')
        return None
    resp = ''
    for day in range(7):
        try:
            times_lst, locations_lst, lessons_lst = parse_schedule_for_a_day(web_page, str(day))
            resp += '<b>' + named_days[day] + '</b>\n\n'
        except:
            continue
        for time, location, lesson in zip(times_lst, locations_lst, lessons_lst):
            resp += f'<b>{time}</b>\n {location}\n {lesson}\n'

    bot.send_message(message.chat.id, resp, parse_mode='HTML')


if __name__ == '__main__':
    bot.polling(none_stop=True)