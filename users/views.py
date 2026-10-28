from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import UserProfileForm


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès !")
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'users/profile.html', {'form': form})
