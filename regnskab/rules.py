'''
Hvis din regning overstiger x kr., skal du betale den ned på højst y kr.
før du må bruge krydslisten.
x bestemmes af get_max_debt og y af get_max_debt_after_payment.
'''

from decimal import Decimal


def get_max_debt():
    return 250


def get_max_debt_after_payment():
    return 0


def get_default_prices():
    vand_price = Decimal('8.00')
    øl_price = Decimal('10.00')
    guld_price = Decimal('13.00')
    vandkasse_price = 25*vand_price
    ølkasse_price = 25*øl_price
    guldkasse_price = ølkasse_price + 30*(guld_price - øl_price)
    return [
        ('øl', øl_price),
        ('ølkasse', ølkasse_price),
        ('guldøl', guld_price),
        ('guldølkasse', guldkasse_price),
        ('sodavand', vand_price),
        ('sodavandkasse', vandkasse_price),
    ]
