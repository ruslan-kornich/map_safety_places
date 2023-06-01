from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect
from django.views import View


class SignupView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, "accounts/signup.html", {"form": form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("accounts:login")
        return render(request, "accounts/signup.html", {"form": form})


class LoginView(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, "accounts/login.html", {"form": form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(
                    "home"
                )  # Замените 'home' на имя вашего представления главной страницы
        return render(request, "accounts/login.html", {"form": form})


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("accounts:login")
