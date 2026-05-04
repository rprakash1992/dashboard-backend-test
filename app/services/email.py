import resend

# import core
from app.core.config import get_settings, ROOT_USER_EMAIL

settings = get_settings()


resend.api_key = settings.RESEND_API_KEY


class EmailService:
    def __init__(self):
        self.app_name = settings.APP_NAME
        self.app_domain = settings.APP_DOMAIN
        self.app_email = settings.APP_EMAIL
        self.root_user_email = ROOT_USER_EMAIL

    async def send_profile_activation_email(self, email: str, name: str):
        try:
            htmlText = f"""<div><p><b>Dear {name},</b></p>
    <br />
    <p>We are excited to inform you that your registration request on {self.app_name} has been successfully approved by the admin.</p>
    <p>You may access the application now.</p>
    <p>Welcome aboard, and enjoy your journey with us!</p>
    <br />
    <p>Best regards,</p>
    <p>{self.app_name} Team</p>
    <div>"""

            params: resend.Emails.SendParams = {
                "from": self.app_email,
                "to": [email],
                "subject": f"{self.app_name}: Account Approved!",
                "html": htmlText,
            }

            response: resend.Email = resend.Emails.send(params)

            if response["id"]:
                return True
            else:
                return False

        except Exception as e:
            print(e)
            return {"error": f"Internal Server Error: {str(e)}", "data": []}

    async def send_new_user_registration_email(self, new_user_email: str, new_user_name: str):
        try:
            htmlText = f"""<div><p><b>Dear Admin,</b></p>
    <br />
    <p>A new user has registered on <b>{self.app_name}</b> and is waiting for account activation.</p>
    <br />
    <table style="border-collapse:collapse;">
      <tr><td style="padding:4px 12px 4px 0;color:#888;">Name</td><td style="padding:4px 0;"><b>{new_user_name}</b></td></tr>
      <tr><td style="padding:4px 12px 4px 0;color:#888;">Email</td><td style="padding:4px 0;"><b>{new_user_email}</b></td></tr>
    </table>
    <br />
    <p>Please review and activate their account.</p>
    <br />
    <p>Best regards,</p>
    <p>{self.app_name} Team</p>
    </div>"""

            params: resend.Emails.SendParams = {
                "from": self.app_email,
                "to": self.root_user_email,
                "subject": f"{self.app_name}: New User Registration — {new_user_name}",
                "html": htmlText,
            }

            response: resend.Email = resend.Emails.send(params)

            if response["id"]:
                return True
            else:
                return False

        except Exception as e:
            print(e)
            return {"error": f"Internal Server Error: {str(e)}", "data": []}

    async def send_profile_deactivation_email(self, email, name):
        try:
            htmlText = f"""<div><p><b>Dear {name},</b></p>
    <br />
    <p>We regret to inform you that your account has been deactivated by the admin.</p> 
    <p>Please contact admin for further queries.</p>
    <br />
    <p>Best regards,</p>
    <p>{self.app_name} Team</p>
    <div>"""

            params: resend.Emails.SendParams = {
                "from": self.app_email,
                "to": [email],
                "subject": f"{self.app_name}: Account Deactivated!",
                "html": htmlText,
            }

            response: resend.Email = resend.Emails.send(params)

            if response["id"]:
                return True
            else:
                return False

        except Exception as e:
            print(e)
            return {"error": f"Internal Server Error: {str(e)}", "data": []}
