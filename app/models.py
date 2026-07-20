from datetime import date
from pydantic import BaseModel, field_validator


class OTPRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        v = v.strip().lower()
        if not v or "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        if len(v) > 254:
            raise ValueError("Email too long")
        return v


class OTPVerify(BaseModel):
    email: str
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        v = v.strip()
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Code must be exactly 6 digits")
        return v


class ProfileSetup(BaseModel):
    name: str
    date_of_birth: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 1 or len(v) > 100:
            raise ValueError("Name must be between 1 and 100 characters")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        v = v.strip()
        try:
            parsed = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Date of birth must be in YYYY-MM-DD format")
        if parsed > date.today():
            raise ValueError("Date of birth cannot be in the future")
        if parsed < date(1900, 1, 1):
            raise ValueError("Invalid date of birth")
        return v


class ProfileUpdate(BaseModel):
    name: str
    date_of_birth: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 1 or len(v) > 100:
            raise ValueError("Name must be between 1 and 100 characters")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        if v is None:
            return v
        v = v.strip()
        try:
            parsed = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Date of birth must be YYYY-MM-DD")
        if parsed > date.today():
            raise ValueError("Date of birth cannot be in the future")
        if parsed < date(1900, 1, 1):
            raise ValueError("Invalid date of birth")
        return v
