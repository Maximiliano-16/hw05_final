from datetime import date


def year(request):
    """Добавляет переменную с текущим годом."""
    context = {
        'year': date.today().year,
    }

    return context
