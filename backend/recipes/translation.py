from googletrans import Translator

translator = Translator()


def get_translate_ru_to_en(string):
    response = translator.translate(string, dest='en')
    return response.text


def all_possible_translations(string):
    response = translator.translate(string, dest='en')
    target = response.extra_data['parsed'][1][0][0][5][0]

    queue, out = [target], []
    while queue:
        elem = queue.pop(-1)
        if isinstance(elem, list):
            queue.extend(elem)
        else:
            out.append(elem)

    return [item for item in out if isinstance(item, str)]


def get_alternative(string):
    translations = all_possible_translations(string)
    alternative = [item for item in translations if item != string]
    return alternative[0]
