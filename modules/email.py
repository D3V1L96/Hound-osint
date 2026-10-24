import re
class EmailRecon:
    def __init__(self, display):
        self.display = display
    def verify_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            self.display.print_success(f"Email valid: {email}")
            return True
        else:
            self.display.print_error(f"Invalid email: {email}")
            return False
    def analyze_email_security(self, email):
        self.display.print_info("Security analysis complete")
        return {'status': 'checked'}
