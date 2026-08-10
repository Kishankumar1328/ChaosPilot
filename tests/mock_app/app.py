from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

mock_app = FastAPI(title="Mock Vulnerable Target App for ChaosPilot")

@mock_app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
      <head><title>Mock Target App</title></head>
      <body>
        <h1>Welcome to Mock Shop</h1>
        <a href="/contact">Contact Support</a>
        <a href="/checkout">Checkout</a>
        <button id="crash-btn" onclick="throw new Error('UNCAUGHT_JS_BUTTON_CRASH')">Trigger JS Crash</button>
      </body>
    </html>
    """

@mock_app.get("/contact", response_class=HTMLResponse)
async def contact_page():
    return """
    <!DOCTYPE html>
    <html>
      <head><title>Contact Support</title></head>
      <body>
        <h1>Contact Us</h1>
        <form action="/submit-contact" method="post">
          <input type="text" id="name" name="name" placeholder="Your Name" required />
          <input type="email" id="email" name="email" placeholder="Your Email" />
          <button type="submit" id="submit-btn">Send Message</button>
        </form>
      </body>
    </html>
    """

@mock_app.post("/submit-contact")
async def submit_contact(data: dict = None):
    # Intentional server error on boundary payload overflow
    raise HTTPException(status_code=500, detail="HTTP 500 Unhandled Server Error on Form Submission")
