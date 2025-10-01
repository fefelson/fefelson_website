from django import forms
from django.contrib.auth.forms import UserCreationForm
from sport_matchups.models import User, Preferences


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Enter a valid email address.")

    EDGE_CHOICES = [
        ("5", "5%"),
        ("7.5", "7.5%"),
        ("10", "10%"),
        ("15", "15%"),
    ]
    BANKROLL_CHOICES = [
        ("100", "$100"),
        ("200", "$200"),
        ("500", "$500"),
        ("1000", "$1000"),
        ("2000", "$2000"),
        ("5000", "$5000"),
        ("10000", "$10000"),
    ]

    edge = forms.ChoiceField(choices=EDGE_CHOICES, required=False, help_text="Select your betting edge.")
    bankroll = forms.ChoiceField(choices=BANKROLL_CHOICES, required=False, help_text="Select your bankroll amount.")
    send_email = forms.BooleanField(required=False, initial=True, help_text="Receive email notifications.")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'edge', 'bankroll', 'send_email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.send_email = self.cleaned_data['send_email']

        if commit:
            user.save()
            # Create Preferences if edge or bankroll provided
            if self.cleaned_data.get('edge') or self.cleaned_data.get('bankroll'):
                preferences = Preferences.objects.create(
                    edge=float(self.cleaned_data['edge'] or 0.0),
                    bankroll=int(self.cleaned_data['bankroll'] or 0)
                )
                user.preferences = preferences
                user.save()

        return user
