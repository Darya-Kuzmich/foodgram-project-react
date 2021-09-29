from django.contrib.auth.validators import UnicodeUsernameValidator


class UsernameValidators(UnicodeUsernameValidator):
    message = (
        'Вы ввели некорректный логин. Допускается вводить только буквы, '
        'числа и символы @/./+/-/_ '
    )
