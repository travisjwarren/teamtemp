from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.core.urlresolvers import reverse
from responses.forms import CreateSurveyForm, SurveyResponseForm, ResultsPasswordForm
from responses.models import User, TeamTemperature, TemperatureResponse
from datetime import datetime
import utils
import responses

def home(request):
    if request.method == 'POST':
        form = CreateSurveyForm(request.POST)
        if form.is_valid():
            csf = form.cleaned_data
            form_id = utils.random_string(8)
            userid = responses.get_or_create_userid(request)
            user, created = User.objects.get_or_create(id=userid)
            # TODO check that id is unique!
            survey = TeamTemperature(creation_date = datetime.now(),
                                     duration = csf['duration'],
                                     password = csf['password'],
                                     creator = user,
                                     id = form_id)
            survey.save()
            return HttpResponseRedirect('/admin/%s' % form_id)
    else:
        form = CreateSurveyForm()
    return render(request, 'index.html', {'form': form})

def submit(request, survey_id):
    userid = responses.get_or_create_userid(request)
    user, created = User.objects.get_or_create(id=userid)
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    if request.method == 'POST':
        form = SurveyResponseForm(request.POST)
        if form.is_valid():
            srf = form.cleaned_data
            # TODO check that id is unique!
            response_id = request.POST.get('id', None)
            response = TemperatureResponse(id = response_id,
                                           request_id = survey,
                                           score = srf['score'],
                                           word = srf['word'],
                                           responder_id = user)
            response.save()
            form = SurveyResponseForm(instance=response)
    else:
        try: 
            previous = TemperatureResponse.objects.get(request = survey_id, 
                                                       responder = user) 
            response_id = previous.id
        except TemperatureResponse.DoesNotExist:
            previous = None
            response_id = None

         
        form = SurveyResponseForm(instance=previous)
    return render(request, 'form.html', {'form': form, 'response_id': response_id})

def admin(request, survey_id):
    survey = get_object_or_404(TeamTemperature, pk=survey_id)
    # if valid session token or valid password render results page
    password = None
    user = None
    if request.method == 'POST':
        form = ResultsPasswordForm(request.POST)
        if form.is_valid():
            rpf = form.cleaned_data
            password = rpf['password']
    else: 
        try: 
            userid = request.session.get('userid', '__nothing__')
            user = User.objects.get(id=userid)
        except User.DoesNotExist:
            return render(request, 'password.html', {'form': ResultsPasswordForm()})
    if user and survey.creator.id == user.id or survey.password == password:
        request.session['userid'] = survey.creator.id
        return render(request, 'results.html', 
                { 'id': survey_id, 'stats': survey.stats()})
    else:
        return render(request, 'password.html', {'form': ResultsPasswordForm()})
