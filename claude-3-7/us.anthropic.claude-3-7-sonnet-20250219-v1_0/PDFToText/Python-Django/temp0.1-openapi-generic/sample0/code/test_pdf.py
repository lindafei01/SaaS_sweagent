
from reportlab.pdfgen import canvas

def create_test_pdf(filename="test.pdf"):
    """Create a simple PDF file for testing"""
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "This is a test PDF file")
    c.drawString(100, 730, "Created for testing the PDF to Text API")
    c.drawString(100, 710, "It should be converted to plain text")
    c.save()

if __name__ == "__main__":
    create_test_pdf()