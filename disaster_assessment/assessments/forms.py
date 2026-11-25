from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import DisasterImage, Profile

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    organization = forms.CharField(max_length=200, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = user.profile
            profile.phone = self.cleaned_data.get('phone', '')
            profile.organization = self.cleaned_data.get('organization', '')
            profile.save()
        return user


class DisasterImageForm(forms.ModelForm):
    class Meta:
        model = DisasterImage
        fields = ['image', 'disaster_type', 'location', 'date_of_incident', 'description']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/jpg',
                'id': 'id_image'
            }),
            'disaster_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Chennai, Tamil Nadu'
            }),
            'date_of_incident': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about the location or situation'
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Image size must be under 10 MB.")
            valid_types = ['image/jpeg', 'image/png', 'image/jpg']
            if hasattr(image, 'content_type') and image.content_type not in valid_types:
                raise forms.ValidationError("Only JPG, JPEG and PNG images are allowed.")
        return image
