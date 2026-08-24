# Import necessary modules from Django
import os  # Importing os for operating system-related functionalities
from django.db import models  # Importing Django's model module to define database models
from django.contrib.auth.models import User  # Importing the built-in User model for user authentication and management

class User_Profile(models.Model):
    # Basic personal details
    User_Full_Name = models.CharField(max_length=100, null=True)  # Full name of the user
    User_Mobile_Number = models.CharField(max_length=15, null=True)  # Mobile number with a max length of 15 characters
    User_Email_ID = models.EmailField(null=True)  # Email address (unique format enforced)
    User_Date_Of_Birth = models.DateField(null=True)  # Date of birth of the user
    User_Gender = models.CharField(max_length=10, null=True)  # Gender of the user (up to 10 characters)
    User_Address = models.CharField(max_length=100, null=True)  # User's address
    User_Nationality = models.CharField(max_length=100, null=True)  # Nationality of the user
    User_Country_And_Pin_Code = models.CharField(max_length=100, null=True)  # Country and pin code of residence

    # Employment and qualification details
    User_Job_Title = models.CharField(max_length=100, null=True)  # Job title of the user
    User_Department = models.CharField(max_length=100, null=True)  # Department in which the user works
    User_Qualification = models.CharField(max_length=100, null=True)  # Highest educational qualification of the user
    User_Qualification_Institution = models.CharField(max_length=100, null=True)  # Institution from which the user graduated
    User_Skills = models.TextField(null=True)  # Skills of the user (long text field to accommodate multiple skills)
    User_Salary = models.IntegerField(null=True)  # Salary of the user

    # File fields for storing images and documents
    User_Image = models.ImageField(upload_to='user_images/', null=True)  # Profile picture of the user
    User_Document_Frontside_Image = models.ImageField(upload_to='user_documents/', null=True)  # Front side of a document (e.g., ID)
    User_Document_Backside_Image = models.ImageField(upload_to='user_documents/', null=True)  # Back side of a document
    User_Resume_PDF = models.FileField(upload_to='user_resumes/', null=True)  # Resume in PDF format

    # Status and activity fields
    is_active = models.BooleanField(default=True)  # Indicates if the user profile is active or not

    # Audit fields for tracking who created or modified the profile and when
    created_by = models.ForeignKey(User, related_name='created_user_profiles', on_delete=models.SET_NULL, null=True, editable=False)  # User who created this profile
    created_at = models.DateTimeField(auto_now_add=True, editable=False)  # Timestamp when the profile was created (auto-generated)
    modified_by = models.ForeignKey(User, related_name='modified_user_profiles', on_delete=models.SET_NULL, null=True, editable=False)  # User who last modified this profile
    modified_at = models.DateTimeField(null=True, editable=False)  # Timestamp of the last modification

    def __str__(self):
        # String representation of the object (returns the user's full name)
        return self.User_Full_Name

    def delete(self, *args, **kwargs):
        """
        Custom delete method to remove associated files (images, documents, resume) from the filesystem
        before deleting the database record.
        """
        # Check if the user image exists, and delete it from the filesystem
        if self.User_Image:
            if os.path.isfile(self.User_Image.path):
                os.remove(self.User_Image.path)

        # Check if the document front-side image exists, and delete it
        if self.User_Document_Frontside_Image:
            if os.path.isfile(self.User_Document_Frontside_Image.path):
                os.remove(self.User_Document_Frontside_Image.path)

        # Check if the document back-side image exists, and delete it
        if self.User_Document_Backside_Image:
            if os.path.isfile(self.User_Document_Backside_Image.path):
                os.remove(self.User_Document_Backside_Image.path)

        # Check if the resume file exists, and delete it
        if self.User_Resume_PDF:
            if os.path.isfile(self.User_Resume_PDF.path):
                os.remove(self.User_Resume_PDF.path)

        # Call the superclass delete method to delete the database entry
        super(User_Profile, self).delete(*args, **kwargs)
