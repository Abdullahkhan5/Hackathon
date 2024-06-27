from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import re
import textwrap

def generate_pdf(text):
    # Create a new PDF with Reportlab
    c = canvas.Canvas("interview_questions.pdf", pagesize=letter)
    width, height = letter
    margin = 30
    max_width = width - 2 * margin  # Maximum text width
    line_height = 20  # Line height

    # Add the title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, height - 40, "Interview Questions")

    # Split the text into sections
    sections = re.split(r'(?=### [^\n]+:)', text)

    y = height - 60  # Start position for the text
    for section in sections:
        if section.strip():  # Skip empty sections
            lines = section.split('\n')
            heading = lines[0].strip()  # Get the section heading
            questions = [line.strip() for line in lines[1:] if line.strip()]  # Get the questions

            # Draw the heading
            c.setFont("Helvetica-Bold", 14)
            y -= line_height * 2
            c.drawString(margin, y, heading)
            
            # Draw the questions
            c.setFont("Helvetica", 12)
            for question in questions:
                wrapped_text = textwrap.wrap(question, width=int(max_width / 6))  # Wrap the text
                for line in wrapped_text:
                    y -= line_height
                    if y < margin:  # Create a new page if there is not enough space on the current page
                        c.showPage()
                        c.setFont("Helvetica-Bold", 18)
                        c.drawString(margin, height - 40, "Interview Questions (cont.)")
                        y = height - 60
                        c.setFont("Helvetica", 12)
                    c.drawString(margin, y, line)

    # Save the PDF
    c.save()
