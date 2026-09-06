from django import template

register = template.Library()

@register.filter
def mask_cpf(cpf):
    """
    Mascara o CPF para exibição em telas não-restritas, preservando
    apenas os 3 primeiros e 2 últimos dígitos (LGPD - minimização de dados).
    """
    if not cpf:
        return ''
    digits = ''.join(ch for ch in str(cpf) if ch.isdigit())
    if len(digits) != 11:
        return cpf
    return f"{digits[0:3]}.***.***-{digits[9:11]}"
