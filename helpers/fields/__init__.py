from helpers import validators
from bson import ObjectId
from datetime import datetime
from helpers.files import decode_base64_image, decode_base64_pdf
import phonenumbers


class ObjectIdField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid id")

        return ObjectId(value)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class EmailField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):

        if not isinstance(value, str):
            raise ValueError("Invalid Email")

        value = value.lower().strip()

        if not validators.valid_email(value):
            raise ValueError("Invalid Email")

        return value


class StrNumberField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not isinstance(value, str):
            raise ValueError("Invalid Number")
        elif not value.isdigit():
            raise ValueError("Invalid Number")

        return value


class PasswordField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not validators.valid_password(value):
            raise ValueError("Invalid Password")

        return value


class PhoneField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):

        if not isinstance(value, str):
            raise ValueError("Invalid Phone Number")
        try:
            phone = phonenumbers.parse(value, region="IL")

            value = phonenumbers.format_number(
                phone, phonenumbers.PhoneNumberFormat.E164
            )
        except:
            raise ValueError("Invalid Phone Number")

        return value


class Base64ImageField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if isinstance(value, tuple):
            return value

        file, content_type = decode_base64_image(value)

        if not file or not content_type:
            raise ValueError("Invalid Image")

        return file, content_type


class URLField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not validators.valid_url(value):
            raise ValueError("Invalid Link")

        return value


class IsraelPhoneField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):

        if not isinstance(value, str):
            raise ValueError("Invalid Phone Number")

        value = value.strip()

        if value.startswith("0"):
            value = value.replace("0", "+972", 1)

        try:
            phone = phonenumbers.parse(value)

            value = phonenumbers.format_number(
                phone, phonenumbers.PhoneNumberFormat.E164
            )
        except:
            raise ValueError("Invalid Phone Number")

        return value


class DateTimeField(int):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: int):

        if isinstance(value, datetime):
            return value

        value = int(value)

        # aka value == 0
        if not value:
            return datetime.fromtimestamp(0)

        return datetime.fromtimestamp(value / 1000)


class Base64PdfField(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if isinstance(value, tuple):
            return value

        file, content_type = decode_base64_pdf(value)

        if not file or not content_type:
            raise ValueError("Invalid PDF")

        return file, content_type
