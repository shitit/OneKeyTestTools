from django.shortcuts import render_to_response
from django.http import HttpResponse
from models import TestQueue, PidRecord
from simplejson import dumps
from datetime import datetime
import OnekeyTest.settings
from os import sep as os_sep
import win32api
from django.core.paginator import Paginator
from django.core.paginator import PageNotAnInteger
from django.core.paginator import EmptyPage

# Create your views here.
def main(request):
	if request.method == 'POST':
		info_dict = {}
		rows = request.POST.get('rows', '')
		try:
			rows = int(rows)
		except:
			rows = 10

		page = request.POST.get('page', '')
		try:
			page = int(page)
		except:
			page = 1

		i_type = request.POST.get('type', '0')

		# query
		if i_type == '1':
			start_time = request.POST.get('start_time', '')
			end_time = request.POST.get('end_time', '')
			exec_status = request.POST.get('exec_status', '')
			_q = None
			if exec_status != '3':
				_q = TestQueue.objects.order_by('-exec_time').filter(exec_ornot=exec_status)
			else:
				_q = TestQueue.objects.order_by('-exec_time').all()
			if start_time != '':
				try:
					_q = _q.filter(exec_time__gte=datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
				except:
					pass
			if end_time != '':
				try:
					_q = _q.filter(exec_time__lte=datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S'))
				except:
					pass

			info_dict['total'] = _q.count()
			paginator = Paginator(_q, rows)
			try:
				_q = paginator.page(page)
			except PageNotAnInteger:
				_q = paginator.page(1)
			except EmptyPage:
				_q = paginator.page(paginator.num_pages)
			info_dict['rows'] = [ {'cid':item.id, 'exec_info':item.exec_info, 'exec_time':item.exec_time.strftime('%Y-%m-%d %H:%M:%S'), 'exec_ornot':item.exec_ornot} for item in _q ]
			out = dumps(info_dict)
			return HttpResponse(out)

		# delete
		elif i_type == '2':
			cid = request.POST.get('cid', '')
			try:
				ret = TestQueue.objects.filter(id=cid)[0].exec_ornot
				if ret==1:
					out = dumps({'ret':'1'})
				elif ret==2:
					out = dumps({'ret':'3'})
				else:
					TestQueue.objects.filter(id=cid).delete()
					out = dumps({'ret':'0'})
			except:
				out = dumps({'ret':'2'})
			return HttpResponse(out)

		# start and stop
		elif i_type == '3':
			start_flag = request.POST.get('start', '')
			if start_flag == '1':	# start
				server_name = OnekeyTest.settings.BASE_DIR + os_sep + 'TestServer' + os_sep + 'TestServer.py '
				base_dir = OnekeyTest.settings.BASE_DIR + os_sep + 'TestServer '
				db_name = OnekeyTest.settings.DATABASES['default']['NAME']
				import subprocess
				szCmd = 'python ' + server_name + base_dir + db_name
				PidRecord.objects.all().delete()
				p = subprocess.Popen(szCmd.split(), shell=False)
				PidRecord(p.pid, 1).save()
				out = dumps({'ret':'0'})
			elif start_flag == '0':	# stop
				try:
					pr = PidRecord.objects.first()
					pid = pr.pid
					handle = win32api.OpenProcess(1, False, pid)
					win32api.TerminateProcess(handle, 0) 
					pr.run_ornot = 0
					pr.save()
					out = dumps({'ret':'0'})
				except Exception,ex:
					out = dumps({'ret':'1'})
					print ex
			elif start_flag == '2':	# status
				ret = 0
				if_run = PidRecord.objects.first().run_ornot
				if if_run == 1:
					ret = 1
				out = dumps({'ret':str(ret)})
			return HttpResponse(out)

		# return total and pager
		otest = TestQueue.objects
		info_dict['total'] = otest.count()
		q = otest.order_by('-exec_time').all()
		paginator = Paginator(q, rows)
		try:
			q = paginator.page(page)
		except PageNotAnInteger:
			q = paginator.page(1)
		except EmptyPage:
			q = paginator.page(paginator.num_pages)
		info_dict['rows'] = [ {'cid':item.id, 'exec_info':item.exec_info, 'exec_time':item.exec_time.strftime('%Y-%m-%d %H:%M:%S'), 'exec_ornot':item.exec_ornot} for item in q ]
		out = dumps(info_dict)
		return HttpResponse(out)
	return render_to_response('index.html')
