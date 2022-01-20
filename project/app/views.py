import re
from django.shortcuts import render, redirect
from django.http import request
from django.views.decorators.csrf import csrf_exempt
import speech_recognition as sr
from django.views.generic import TemplateView, ListView
from .models import InputText
from django.contrib.auth import login
from .form import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


def index(request):
    return render(request, 'app/index.html')


def home(request):
    latest_data = ''
    if InputText.objects.filter(
            user=request.user).count() > 0:
        latest_data = InputText.objects.filter(
            user=request.user).latest('pub_date')
    return render(request, 'app/home.html', {'data': "【文字起こし結果】:"+str(latest_data)})


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user_instance = form.save()
            login(request, user_instance)
            return redirect("app:home")
    else:
        form = UserCreationForm()

    context = {
        "form": form
    }
    return render(request, 'app/signup.html', context)


class LogView(LoginRequiredMixin, ListView):
    template_name = "app/log.html"

    def get(self, request):
        if InputText.objects.filter(user=request.user).count() > 0:
            model = InputText.objects.filter(user=request.user)
            return render(request, self.template_name, {'model': model})

    def post(self, request):
        delete_pk = request.POST.get('delete')
        InputText.objects.filter(pk=delete_pk).delete()
        return redirect('app:log')


class RecordTrialView(TemplateView):
    template_name = 'index.html'

    def post(self, request):
        audio_wav = request.body

        with open('audio/audio.wav', 'wb') as f:
            f.write(audio_wav)
            r = sr.Recognizer()
            with sr.AudioFile('audio/audio.wav') as source:
                audio_data = r.record(source)

        output = r.recognize_google(audio_data, language='ja-JP')
        print(output)

        return JsonResponse({'data': output})


class RecordView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["data"] = InputText.objects.latest('pub_date')
        return context

    def get(self, request):
        return render(request, 'app/index.html', {'data': "output"})

    def post(self, request):
        audio_wav = request.body

        with open('audio/audio.wav', 'wb') as f:
            f.write(audio_wav)
            r = sr.Recognizer()
            with sr.AudioFile('audio/audio.wav') as source:
                audio_data = r.record(source)

        output = r.recognize_google(audio_data, language='ja-JP')
        sentences = output.split(' ')
        print(output)

        for sentence in sentences:
            input_text = InputText(text=sentence, user=request.user)
            input_text.save()
        return JsonResponse({'data': output})
