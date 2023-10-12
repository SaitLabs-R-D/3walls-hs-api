from io import BytesIO
from helpers.env import EnvVars
from typing import Union
import jinja2, base64
from .types import FileAttachment
import sendgrid
from sendgrid.helpers.mail import (
    Mail,
    From,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
    Bcc,
    To,
)
from helpers.env import EnvVars
from typing import Union


class EmailManager:
    def __init__(self):
        self.jinja_loader = jinja2.Environment(
            loader=jinja2.FileSystemLoader("services/sms_email/templates")
        )
        self.sg = sendgrid.SendGridAPIClient(EnvVars.SEND_GRID_KEY)
        self.sender_name = "3walls"
        if EnvVars.is_development:
            self.sender_name = f"{self.sender_name}-dev"

    def render_jinja_html(self, file_name, **context):

        return self.jinja_loader.get_template(file_name).render(context)

    def send(
        self,
        to: Union[str, list[str]],
        subject: str,
        body: str,
        bcc: Union[str, list[str], None] = None,
        attachments: Union[list[FileAttachment], FileAttachment, None] = None,
        send_to_3wall: bool = False,
    ):

        send_to = to if isinstance(to, list) else [to]

        send_bcc = bcc if isinstance(bcc, list) else [bcc] if bcc else []

        if send_to_3wall:
            send_bcc.append(EnvVars.THREE_WALL_EMAIL)

        recivers = [Bcc(email) for email in send_bcc] + [To(email) for email in send_to]

        if attachments:
            attachments = (
                attachments if isinstance(attachments, list) else [attachments]
            )

            attachments = [
                Attachment(
                    FileContent(self.encode_file(attachment.content)),
                    FileName(attachment.filename),
                    FileType(attachment.mimetype),
                    Disposition("attachment"),
                )
                for attachment in attachments
            ]

        message = Mail(
            from_email=From(EnvVars.SEND_GRID_SENDER, self.sender_name),
            to_emails=recivers,
            subject=subject,
            html_content=body,
        )

        if attachments:
            message.attachment = attachments

        response = self.sg.send(message)

        return response

    @staticmethod
    def encode_file(file: BytesIO) -> str:
        """
        Description:
        ------------
        - Encode file to base64 string

        Parameters:
        -----------
        - `file`: BytesIO, or any object that has `read` method

        Returns:
        --------
        - `str`: base64 string
        """
        return base64.b64encode(file.read()).decode()

    def send_email_verification_mail(
        self,
        to: Union[str, list[str]],
        email: str,
        full_name: str,
        token: str,
        send_to_3wall: bool = True,
    ):
        subject = "Thank you for joining 3-Walls Immersive Room"
        content = f"""
        <h1>Hi {full_name}</h1>
        <p>Thank you for joining 3-Walls Immersive Room</p>
        <p>Click <a href="{EnvVars.SITE_URL}/login/verify-email?token={token}">here</a> to login</p>
        <p>Or copy this link to your browser: {EnvVars.SITE_URL}/login/verify-email?token={token}</p>
        <p>the email you used to register is: {email}</p>
        """

        self.send(to, subject, content, send_to_3wall=send_to_3wall)

    def send_reset_password(
        self, to: Union[str, list[str]], full_name: str, token: str
    ):
        subject = "Reset your password"
        content = f"""
            <h1>Hey {full_name}</h1>
            <p>Click <a href="{EnvVars.SITE_URL}/login/reset-password?token={token}">here</a> to reset your password</p>
            <p>Or copy this link to your browser: {EnvVars.SITE_URL}/login/reset-password?token={token}</p>
        """

        self.send(to, subject, content)

    def send_regstration_email(
        self,
        to: Union[str, list[str]],
        email: str,
        full_name: str,
        token: str,
        send_to_3wall: bool = True,
    ):
        subject = "Welcome to 3-Wall"
        content = f"""
        <h1>Hi {full_name}</h1>
        <p>Thank you for joining 3-Wall</p>
        <p>Click <a href="{EnvVars.SITE_URL}/login/first?token={token}">here</a> to login</p>
        <p>Or copy this link to your browser: {EnvVars.SITE_URL}/login/first?token={token}</p>
        <p>the email you used to register is: {email}</p>
        """

        self.send(to, subject, content, send_to_3wall=send_to_3wall)


EMAIL_SERVICE = EmailManager()
