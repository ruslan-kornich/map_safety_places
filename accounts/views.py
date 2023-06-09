from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.views import LoginView as DefaultLoginView
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.shortcuts import redirect


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


from django.http import HttpResponseServerError


class LoginView(DefaultLoginView):
    def get_success_url(self):
        return reverse_lazy("map")

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")

        # В случае ошибки, возвращаем HTTP-ответ с кодом 500 и сообщением об ошибке
        return HttpResponseServerError(
            "Внутрішня помилка сервера. Будь ласка, спробуйте пізніше. Або введіть коректний пароль або логін "
        )


def logout_view(request):
    logout(request)
    return redirect("home")
