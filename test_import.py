try:
    from xhtml2pdf import pisa
    print("Import successful")
except Exception as e:
    import traceback
    traceback.print_exc()
