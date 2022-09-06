import re


def get_hidden_email(raw_email: str):
    try:
        to_hide = raw_email[1:raw_email.index('@')-1]
        hidden_email = re.sub(to_hide, '*' * len(to_hide), raw_email)
        return hidden_email
    except ValueError:
        return raw_email


def get_hidden_pwd(raw_pwd: str = None):
    return '*' * 8


if __name__ == '__main__':
    print(get_hidden_email('dima29koz@yandex.ru'))

