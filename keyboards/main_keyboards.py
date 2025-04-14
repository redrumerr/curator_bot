from global_variables.variables import green, red, blue, ctx, predsed_team_ids
from vkbottle import Keyboard, Text


def main_kb(vk_id) -> Keyboard:
    kb = Keyboard()
    kb.add(Text('Мой профиль'), color=green)
    kb.add(Text('Найти человека'), color=green)
    kb.row()
    kb.add(Text('Календарь'), color=blue)
    if vk_id in predsed_team_ids:
        kb.row()
        kb.add(Text('Админ-панель'), color=red)
    else:
        kb.row()
        kb.add(Text('Сдать домашку'), color=blue)

    return kb


def admin_kb() -> Keyboard:
    kb = Keyboard()
    kb.add(Text('Матрица компетенций'), color=blue)
    kb.add(Text('Топы'), color=blue)
    kb.row()
    kb.add(Text('Отметить отсутствующих'), color=blue)
    kb.row()
    kb.add(Text('Домашка'), color=green)
    kb.row()
    kb.add(Text('Загрузить календарь'), color=green)
    kb.row()
    kb.add(Text('Страйки'), color=red)
    kb.add(Text('Кикнуть'), color=red)
    kb.row()

    kb.add(Text("Выход"), color=red)

    return kb


def strikes_kb() -> Keyboard:
    kb = Keyboard()
    kb.add(Text('Выдать страйк'), color=red)
    kb.add(Text('Убрать страйк'), color=green)
    kb.row()

    kb.add(Text('Выход'), color=red)

    return kb


def competition_kb() -> Keyboard:
    kb = Keyboard()
    kb.add(Text('Активность'), color=blue)
    kb.row()
    kb.add(Text('Ответственность'), color=blue)
    kb.row()
    kb.add(Text('Взаимодействия'), color=blue)
    kb.row()
    kb.add(Text('Соблюдение правил'), color=blue)
    kb.row()
    kb.add(Text('Доп комментарий'), color=blue)
    kb.row()

    kb.add(Text('Выход'), color=red)

    return kb


def homework_kb() -> Keyboard:
    kb = Keyboard()
    kb.add(Text('Поставить дедлайн'), color=blue)
    kb.row()
    kb.add(Text('Выгрузить домашку'), color=green)
    kb.row()

    kb.add(Text('Выход'), color=red)

    return kb


def accept_spam_kb() -> Keyboard:
    kb = Keyboard()
    kb.add(Text("Подтвердить"), color=green)
    kb.add(Text("Отмена"), color=red)

    return kb


def back_kb() -> Keyboard:
    kb = Keyboard()
    kb.add(Text('Выход'), color=red)

    return kb


def choose_deadline_kb(*deadlines) -> Keyboard:
    kb = Keyboard()
    for deadline in deadlines:
        kb.add(Text(deadline), color=blue)
        kb.row()

    kb.add(Text('Выход'), color=red)
    return kb


def top_kb() -> Keyboard:
    kb = Keyboard()
    kb.add(Text('По рейтингу'), color=green)
    kb.add(Text('По пропускам'), color=blue)
    kb.add(Text('По страйкам'), color=red)
    kb.row()

    kb.add(Text('Выход'), color=red)
    return kb


def top_asc_desc_kb() -> Keyboard:
    kb = Keyboard()
    kb.add(Text('По возрастанию'), color=green)
    kb.add(Text('По убыванию'), color=red)
    kb.row()

    kb.add(Text('Выход'), color=red)
    return kb
