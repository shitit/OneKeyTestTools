import SocketServer
import struct
from ConfigParser import ConfigParser
import wmi, win32api, win32con, win32com.client
import pythoncom
import subprocess, threading, time, os, sys
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, MetaData, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

# define communication struct
'''
typedef struct
{
	char	acVer[64];		
	char	acType[64];		
	char	acMachine[64];	
	char	acName[64];		
	char	acPassword[64];	
	char	acBuild[512];	
	char	acDate[64];		
	char	acProName[64];	
	char	acWosa[64];		
	char	acReserve[128];	
} tMsgInfo;
'''
recv_header_name = (
	'acVer',
	'acType',
	'acMachine',
	'acName',
	'acPassword',
	'acBuild',
	'acDate',
	'acProName',
	'acWosa',
	'acReserve'
)
g_construct = struct.Struct('64s64s64s64s64s512s64s64s64s128s')

C_NORMAL  = 0
C_BUSY    = 1
E_CONFIG  = 4
E_UNKNOWN = 9
 
g_confile = 'config.ini'
g_timewait = 1

def queryProcess(list_name):
	ret = False
	pythoncom.CoInitialize()
	try:
		WMI = win32com.client.GetObject('winmgmts:')
		wql = 'select * from Win32_Process where '
		for item in list_name:
			wql = wql + 'Name like "' + item + '%" or '
		wql = wql[0:wql.rfind('or')]
		p = WMI.ExecQuery(wql)
		if len(p) != 0:
			ret = True
		else:
			ret = False
	except Exception,ex:
		ret = False
	pythoncom.CoUninitialize()
	return ret

def killProcess(list_name):
	pythoncom.CoInitialize()
	try:
		WMI = win32com.client.GetObject('winmgmts:')
		wql = 'select * from Win32_Process where '
		for item in list_name:
			wql = wql + 'Name like "' + item + '%" or '
		wql = wql[0:wql.rfind('or')]
		p = WMI.ExecQuery(wql)
		if len(p) != 0:
			for _p in p:
				pid = _p.Properties_('ProcessId').Value
				handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid)
				if handle:
					win32api.TerminateProcess(handle,0)
					win32api.CloseHandle(handle)
	except Exception,ex:
		print ex
	pythoncom.CoUninitialize()

class TestQueue(Base):
	__tablename__ = 'test_queue'

	id = Column('id', Integer, primary_key=True)
	exec_info = Column('exec_info', String)
	exec_time = Column('exec_time', DateTime)
	exec_ornot = Column('exec_ornot', Integer)

	def __init__(self, exec_info, exec_time, exec_ornot):
		self.exec_info = exec_info
		self.exec_time = exec_time
		self.exec_ornot = exec_ornot

	def __repr__(self):
		return "%s:%d" % (self.exec_info, self.exec_ornot)

class TCPHandler(SocketServer.StreamRequestHandler):

	def bExecuting(self, pname):
		return queryProcess(pname)

	def checkConfig(self):
		try:
			config = ConfigParser()
			config.read(g_confile)
			self.mod_cfg = config.get('autotest', 'config').strip()
			self.mod_testware = tuple(config.get('autotest', 'testware').strip().split(','))
			self.mod_runfile = tuple(config.get('autotest', 'runfile').strip().split(','))
			self.runtest = config.get('autotest', 'runtest').strip()
			self.checktest = config.get('autotest', 'checktest').strip().split(',')
			if self.runtest=='' or self.mod_cfg=='':
				return False
		except:
			return False
		return True

	def in_queue(self, acBuild):
		ts = TestQueue(acBuild, datetime.now(), 0)
		session.add(ts)
		session.commit()

	def send_status(self, _status):
		self.request.sendall(str(_status))

	def handle(self):
		self.data = self.request.recv(4096).strip('')
		receive_data = dict(zip(recv_header_name, g_construct.unpack(self.data)))
		acBuild = receive_data['acBuild'].replace('\x00','')
		# check configure setting
		try:
			if self.checkConfig():
				# go into queue
				self.in_queue(acBuild)
				# query whether to execute or not
				if not self.bExecuting(self.checktest):
					self.send_status(C_NORMAL)
				else:
					self.send_status(C_BUSY)
			else:
				self.send_status(E_CONFIG)
		except Exception, ex:
			print ex
			self.send_status(E_CONFIG)

class TestExec:

	def checkConfig(self):
		try:
			config = ConfigParser()
			config.read(g_confile)
			self.mod_cfg = config.get('autotest', 'config').strip()
			self.mod_testware = tuple(config.get('autotest', 'testware').strip().split(','))
			self.mod_runfile = tuple(config.get('autotest', 'runfile').strip().split(','))
			self.runtest = config.get('autotest', 'runtest').strip()
			self.checktest = config.get('autotest', 'checktest').strip().split(',')
			if self.runtest=='' or self.mod_cfg=='':
				return False
		except:
			return False
		return True
	
	def set_config(self, acBuild):		
		# write to ini
		r_config = ConfigParser()
		r_config.read(self.mod_cfg)
		r_config.set(self.mod_testware[0], self.mod_testware[1], acBuild)
		r_config.set(self.mod_runfile[0], self.mod_runfile[1], self.runtest)
		r_config.write(open(self.mod_cfg, 'w'))

	def bExecuting(self, pname):
		return queryProcess(pname)

	def execute_autotest(self):
		killProcess(self.checktest)
		command_line = self.runtest
		p = subprocess.Popen(command_line.split(), shell=False)

	def out_queue(self):
		ts = session.query(TestQueue).filter(TestQueue.exec_ornot==0).order_by(TestQueue.exec_time).first()
		if ts!=None:
			ts.exec_ornot = 1
			session.commit()
			return ts.exec_info
		else:
			return None

	def comsume_handle(self):
		while 1:
			# check configure setting
			try:
				if self.checkConfig():
					# query whether to execute or not
					if not self.bExecuting(self.checktest):
						# pop queue
						r_acBuild = self.out_queue()
						if r_acBuild != None:
							self.set_config(r_acBuild)
							self.execute_autotest()
			except Exception, ex:
				print ex
			time.sleep(g_timewait)

def startServer():
	config = ConfigParser()
	config.read(g_confile)
	HOST = config.get('server_info', 'ip').strip()
	PORT = config.getint('server_info', 'port')
	# thread for comsume
	tx = TestExec()
	testexec_thread = threading.Thread(target=tx.comsume_handle)
	testexec_thread.daemon = True
	testexec_thread.start()
	server = SocketServer.ThreadingTCPServer((HOST, PORT), TCPHandler)
	server.serve_forever()

if __name__ == "__main__":
	db_file = sys.argv
	print db_file
	sys.exit(0)
	#engine = create_engine('sqlite:///' + db_file + '?check_same_thread=False', echo=False)
	#Base = declarative_base()
	#Session = scoped_session(sessionmaker(bind=engine))
	#session = Session()
	#startServer()
