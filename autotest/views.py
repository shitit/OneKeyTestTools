from django.shortcuts import render_to_response
from django.http import HttpResponse
from models import TestQueue, PidRecord
from simplejson import dumps
from datetime import datetime
import OnekeyTest.settings
from os import sep as os_sep

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
			q = None
			if exec_status != '2':
				q = TestQueue.objects.filter(exec_ornot=exec_status)
			else:
				q = TestQueue.objects.all()
			if start_time != '':
				try:
					q = q.filter(exec_time__gte=datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
				except:
					pass
			if end_time != '':
				try:
					q = q.filter(exec_time__lte=datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S'))
				except:
					pass
			info_dict['total'] = q.count()
			info_dict['rows'] = [ {'cid':item.id, 'exec_info':item.exec_info, 'exec_time':item.exec_time.strftime('%Y-%m-%d %H:%M:%S'), 'exec_ornot':item.exec_ornot} for item in q[(page-1)*rows:page*rows] ]
			out = dumps(info_dict)
			return HttpResponse(out)

		# delete
		elif i_type == '2':
			cid = request.POST.get('cid', '')
			try:
				if TestQueue.objects.filter(id=cid)[0].exec_ornot==1:
					out = dumps({'ret':'1'})
				else:
					TestQueue.objects.filter(id=cid).delete()
					out = dumps({'ret':'0'})
			except:
				out = dumps({'ret':'2'})
			return HttpResponse(out)

		# start and stop
		elif i_type == '3':
			start_flag = request.POST.get('start', '')
			if start_flag == '1':
				server_name = OnekeyTest.settings.BASE_DIR + os_sep + 'TestServer' + os_sep + 'TestServer.py '
				base_dir = OnekeyTest.settings.BASE_DIR + os_sep + 'TestServer '
				db_name = OnekeyTest.settings.DATABASES['default']['NAME']
				import subprocess
				szCmd = 'python ' + server_name + base_dir + db_name
				PidRecord.objects.all().delete()
				p = subprocess.Popen(szCmd.split(), shell=True)
				PidRecord(p.pid, '').save()
			elif start_flag == '0':
				try:
					server_p.terminate()
				except Exception,ex:
					print ex
			return HttpResponse('')

		# return total and pager
		otest = TestQueue.objects
		info_dict['total'] = otest.count()
		info_dict['rows'] = [ {'cid':item.id, 'exec_info':item.exec_info, 'exec_time':item.exec_time.strftime('%Y-%m-%d %H:%M:%S'), 'exec_ornot':item.exec_ornot} for item in otest.all()[(page-1)*rows:page*rows] ]
		out = dumps(info_dict)
		return HttpResponse(out)
	return render_to_response('autotest/index.html')