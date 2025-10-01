from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from .forms import SignUpForm

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('game_list')
    else:
        form = SignUpForm()
        print(form.fields.keys())  # Debug: Print form field names
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def user_preferences(request):
    user = request.user
    prefs = getattr(user, 'preferences', None)

    # Set default values if no preferences exist
    initial_edge = prefs.edge if prefs else 7.5
    initial_bankroll = prefs.bankroll if prefs else 1000

    if request.method == "POST":
        edge = float(request.POST.get("edge", initial_edge))
        bankroll = int(request.POST.get("bankroll", initial_bankroll))
        send_email = request.POST.get("send_email") == "on"

        user.send_email = send_email
        user.save()

        if prefs:
            prefs.edge = edge
            prefs.bankroll = bankroll
            prefs.save()
        else:
            from sport_matchups.models import Preferences
            prefs = Preferences.objects.create(user=user, edge=edge, bankroll=bankroll)
            prefs.user = user
            prefs.save()

        from django.contrib import messages
        messages.success(request, "Preferences updated successfully!")
        return redirect("user_preferences")

    context = {
        "preferences": {"edge": initial_edge, "bankroll": initial_bankroll},
        "user": user,
    }
    return render(request, "sport_matchups/user_preferences.html", context)
