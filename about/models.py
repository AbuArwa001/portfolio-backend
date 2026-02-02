from django.db import models

class About(models.Model):
    profile = models.OneToOneField('users.UserProfile', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    bio = models.TextField()
    profile_image = models.ImageField(upload_to="about/", blank=True, null=True)
    skills = models.TextField(help_text="Comma separated skills")
    

    def skills_list(self):
        return [s.strip() for s in self.skills.split(",")]

    def __str__(self):
        return self.name
