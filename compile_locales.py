import polib
import os

po_file = 'locale/ml/LC_MESSAGES/django.po'
mo_file = 'locale/ml/LC_MESSAGES/django.mo'

if os.path.exists(po_file):
    po = polib.pofile(po_file)
    po.save_as_mofile(mo_file)
    print(f"Successfully compiled {po_file} to {mo_file}")
else:
    print(f"Error: {po_file} not found")
