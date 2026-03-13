from PIL import Image, ImageDraw

# Create a simple test image with some text
img = Image.new('RGB', (400, 200), color='white')
draw = ImageDraw.Draw(img)
draw.text((10, 10), "Test Data: Name, Age, Email", fill='black')
draw.text((10, 50), "John Doe, 25, john@example.com", fill='black')
draw.text((10, 90), "Student ID: S12345", fill='black')

# Save the image
img.save('/Users/vigneshjumpula/studentPerformnace/student-risk-sys/sars/image.png')
print("Test image created: image.png")
