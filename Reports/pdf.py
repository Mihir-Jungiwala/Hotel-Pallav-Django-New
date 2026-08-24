# reports/pdf.py

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict):
    """
    Generates a PDF from the given template and context.
    
    Args:
        template_src (str): Path to the HTML template.
        context_dict (dict): Context data to render the template.
    
    Returns:
        HttpResponse: PDF response to be returned from a view.
    """
    template = get_template(template_src)
    html = template.render(context_dict)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="document.pdf"'  # Changed to inline

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    return response
