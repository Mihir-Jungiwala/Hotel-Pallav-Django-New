import logging

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


def Send_Reset_Password_Mail(email, first_name, last_name, token, request=None):
    """
    Sends a password reset email to the user.

    Args:
        email (str): The email address of the user.
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.
        token (str): The unique token for password reset.
        request: The current HttpRequest, used to build an absolute
            reset link against the actual host the app is served from.
            Falls back to DJANGO_SITE_BASE_URL (or localhost, for local
            dev) if no request is available.

    Returns:
        bool: True if the email was sent successfully, raises an exception otherwise.
    """

    # Previously hardcoded to http://127.0.0.1:8000 — every reset email
    # sent from a real deployment would have linked back to localhost,
    # making the "reset password" flow completely non-functional in
    # production. Building from the actual request host fixes it; the
    # env var fallback covers callers (or future management commands)
    # that don't have a request to hand in.
    if request is not None:
        reset_path = reverse('changepassword', args=[token])
        reset_link = request.build_absolute_uri(reset_path)
    else:
        import os
        base_url = os.environ.get('DJANGO_SITE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
        reset_link = f"{base_url}/Change-Password/{token}/"
    
    # Set the subject for the email
    subject = 'Password Reset Request - Action Required'
    
    # Prepare the HTML message with personalized content
    message = f"""
    <html>
        <head>
            <style>
                /* Styles for the email layout */
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f9f9f9;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-sizing: border-box;
                }}
                h2 {{
                    color: #4CAF50;
                }}
                a.button {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    width: auto;
                    max-width: 100%;
                    box-sizing: border-box;
                    word-wrap: break-word;
                    text-align: center;
                    margin-top: 10px; /* Space above the button */
                }}
                p {{
                    margin: 0 0 15px;
                }}
                .green-text {{
                    color: green; /* Green text for the email */
                    text-decoration: none; /* Remove underline */
                }}
                .black-text {{
                    color: black; /* Text color for company name */
                }}
                .button-spacing {{
                    margin: 15px 0; /* Space below the button */
                }}
                @media (max-width: 600px) {{
                    .container {{
                        padding: 15px;
                    }}
                    .button-container {{
                        text-align: center; /* Center the button container on mobile */
                    }}
                    a.button {{
                        width: 100%; /* Button will take full width on mobile */
                        padding: 15px;
                    }}
                }}
                @media (min-width: 601px) {{
                    .button-container {{
                        text-align: left; /* Align button to the left on desktop */
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Dear {first_name} {last_name},</h2>
                <p>
                    We regret to inform you that your password needs to be reset. 
                </p>
                <p>
                    To reset your password, please click on the button below:
                </p>
                <div class="button-container">
                    <a href="{reset_link}" class="button">
                        Reset Password
                    </a>
                </div>
                <p class="button-spacing"></p> <!-- Space below the button -->
                <p>
                    This link is valid for 10 minutes. After that, you will need to request another password reset.
                </p>
                <p>
                    If you did not request this, please disregard this email. Your account remains secure.
                </p>
                <p>
                    If you have any issues or questions, we’re here to help. Please contact our support team at 
                    <span class="green-text">noreply.hotelpallav@gmail.com</span>.
                </p>
                <p>
                    Thank you,<br>
                    <span class="black-text">Easy Hotel Solutions</span>
                </p>
            </div>
        </body>
    </html>
    """

    # Set the sender's email address from the settings
    email_from = settings.EMAIL_HOST_USER
    
    # Create a list of recipients containing the user's email
    recipient_list = [email]

    try:
        # Send the reset password email using the send_mail function with HTML content
        send_mail(subject, '', email_from, recipient_list, html_message=message)
        
        # Log the successful email sending
        logger.info(f'Password reset email sent to {email}.')
    except Exception as e:
        # Log any errors encountered while sending the email
        logger.error(f'Error sending password reset email to {email}: {str(e)}')
        
        # Rethrow the exception for handling in the calling function
        raise  

    return True  # Indicate that the email was sent successfully

