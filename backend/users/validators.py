from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _


class UsernameValidators(UnicodeUsernameValidator):
    message = _(
        'Вы ввели некорректный логин. Допускается вводить только буквы, '
        'числа и символы @/./+/-/_ '
    )
