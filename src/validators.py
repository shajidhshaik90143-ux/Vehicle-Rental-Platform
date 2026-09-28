from datetime import date

def validate_registration(name, email, password, confirm, phone):
    errors = []
    if len(name.strip()) < 2:
        errors.append("Name must contain at least 2 characters.")
    if "@" not in email or "." not in email:
        errors.append("Enter a valid email address.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if password != confirm:
        errors.append("Passwords do not match.")
    digits = "".join(c for c in phone if c.isdigit())
    if phone and len(digits) < 10:
        errors.append("Phone number should contain at least 10 digits.")
    return errors

def validate_dates(pickup, return_date):
    if pickup < date.today():
        return "Pickup date cannot be in the past."
    if return_date <= pickup:
        return "Return date must be after pickup date."
    return None
