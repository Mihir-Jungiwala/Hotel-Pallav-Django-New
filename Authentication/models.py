from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



class Authentication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    # Ties this row to the actual Django session that created it, so
    # AutoLogoutMiddleware checks *this* session's idle time instead of
    # "whichever row for this user happens to have the most recent
    # activity_time" — which previously meant one active session's
    # activity could silently keep another idle session of the same user
    # alive, or vice versa. Nullable/blank so existing rows (created
    # before this field existed) don't break; the middleware falls back
    # to the pre-existing lookup for those.
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    forgot_password_token = models.CharField(max_length=100, null=True)  
    token_used = models.BooleanField(default=False)  
    email_sent_time = models.DateTimeField(null=True, blank=True)
    activity_type = models.CharField(max_length=10, choices=[('Login', 'Login'), ('Logout', 'Logout')])
    activity_time = models.DateTimeField(auto_now_add=True)
    login_date = models.DateField(null=True, blank=True)
    logout_date = models.DateField(null=True, blank=True)
    login_time = models.TimeField(null=True, blank=True)
    logout_time = models.TimeField(null=True, blank=True)
    minutes_logged_in = models.CharField(max_length=5, null=True, blank=True)  # Changed to MM:HH format
    password_change_time = models.DateTimeField(null=True, blank=True)
    password_change_duration = models.PositiveIntegerField(null=True, blank=True)
   


    def calculate_minutes_logged_in(self):
        """Calculate and update the minutes logged in."""
        if self.login_time and self.logout_time:
            login_datetime = timezone.make_aware(timezone.datetime.combine(timezone.datetime.today(), self.login_time))
            logout_datetime = timezone.make_aware(timezone.datetime.combine(timezone.datetime.today(), self.logout_time))

            td = logout_datetime - login_datetime
            total_minutes = int(td.total_seconds() // 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            self.minutes_logged_in = f"{hours:02d}:{minutes:02d}"  # Format as MM:HH
        else:
            self.minutes_logged_in = None

    def save(self, *args, **kwargs):
        """Override save method to calculate minutes logged in and update password change fields before saving."""
        self.calculate_minutes_logged_in()

        # Check if password was changed and update password_change fields
        if self.pk:  # If the object already exists (not a new instance)
            original = Authentication.objects.get(pk=self.pk)
            if not original.password_change_time and self.password_change_time:
                if self.email_sent_time:  # Check if email_sent_time is available
                    self.password_change_duration = (self.password_change_time - self.email_sent_time).total_seconds() // 60
                

        super().save(*args, **kwargs)


