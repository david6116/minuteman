from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
import requests
import json

from minuteman.forms import LogForm
from minuteman.forms import ProjectForm
from minuteman.models import Log, Project, Client

@login_required()
def dashboard(request):

    form = LogForm(contractor=request.user.contractor)
    lastfive = Log.objects.filter(contractor__user=request.user)
    lastfive = lastfive.reverse()[:5]
    projects = Project.objects.all().select_related()

    try:
        current_log = Log.objects.get(contractor=request.user.contractor, end_time=None)
    except Log.DoesNotExist:
        current_log = None

    context = {
        'form': form,
        'projects': projects,
        'lastfive': lastfive,
        'current_log': current_log,
    }

    return render_to_response('minuteman/dashboard.html', context,
                                context_instance=RequestContext(request))

@login_required()
def project_summary(request):

    logs = Log.objects.filter(contractor=request.user.contractor)

    projects = {}
    project_costs = {}
    rate = request.user.contractor.rate / 60.00 / 60.00

    for each_log in logs:
        if each_log.project in projects:
            projects[each_log.project]['duration'] += each_log.duration.total_seconds()
            projects[each_log.project]['cost'] += each_log.duration.total_seconds() * rate

        else:
            projects[each_log.project] = {
                'duration': each_log.duration.total_seconds(),
                'cost' : each_log.duration.total_seconds() * rate,
                'client' : each_log.project.client
            }

    context = {
        'projects' : projects,
    }

    return render_to_response('minuteman/project_summary.html', context,
                                context_instance=RequestContext(request))


@login_required()
def project_total(request):



    return render_to_response('minuteman/project_total.html',
        context_instance=RequestContext(request))

@login_required()
def create_project(request):
     if request.method == 'POST':
         form = ProjectForm(request.POST)
         if form.is_valid():
            try:
                assignuser = request.user.contractor
                clientobject = Client.objects.get(id=request.POST['clientid'])
                newproject = Project.objects.create(client=clientobject, name=request.POST['name'])
                assignuser.projects.add(newproject)
            except Exception:
                print("FAIL")
         else:
            print('fail')
     else:
         print('fail')

@csrf_exempt
@login_required
def start(request):

    if request.method == 'POST':
        form = LogForm(request.user.contractor, request.POST)
        if form.is_valid():
            project = form.cleaned_data['project']
            comments = form.cleaned_data['comments']

            try:
                current_log = Log.objects.get(contractor=request.user.contractor, end_time=None)
            except Log.DoesNotExist:
                pass
            else:
                current_log.stop()

            Log.start(project=project, contractor=request.user.contractor, comments=comments)
            return HttpResponseRedirect('/dashboard/')
        else:
            return HttpResponseBadRequest("You're shit ain't valid")
    else:
        return HttpResponseNotAllowed(['POST'])

@csrf_exempt
@login_required
def stop(request):

    if request.method == 'POST':
        form = LogForm(request.user.contractor, request.POST)
        if form.is_valid():
            current_log = Log.objects.get(contractor=request.user.contractor, end_time=None)
            current_log.stop()
            return HttpResponseRedirect('/dashboard/')
        else:
            return HttpResponseBadRequest()
    else:
        return HttpResponseNotAllowed(['POST'])

@csrf_exempt
def send_invoice(request):
    message_info = {"key": "d7cd67d0-3671-4412-9e82-8cbaf394f5b2",
        "message": {
            "html": "example html",
            "text": "example text",
            "subject": "Mandrill and I",
            "from_email": "david6116@yahoo.com",
            "from_name": "Tstr Dave",
            "to": [
                {
                    "email": "clay@daemons.net",
                    "name": "david"
                }
            ],
            "tags": [
                "exampletest"
            ],
        }
    }

    message_info_json = json.dumps(message_info)

    print(message_info_json)

    r = requests.post("https://mandrillapp.com/api/1.0/messages/send.json", data=message_info_json)

    print r

    return HttpResponseBadRequest("You're shit an't valid")
