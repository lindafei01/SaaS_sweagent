
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create first PDF
c = canvas.Canvas("test1.pdf", pagesize=letter)
c.drawString(100, 750, "This is test file 1")
c.save()

# Create second PDF
c = canvas.Canvas("test2.pdf", pagesize=letter)
c.drawString(100, 750, "This is test file 2")
c.save()

print("PDF files created successfully")