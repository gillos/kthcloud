from requests import *
from requests.auth import HTTPBasicAuth
import json
import sys
from xml.dom.minidom import parseString
import os
from getpass import getpass
def getorgurl(token):
	xml=get('https://www.cloud.kth.se/api/org/',headers={'Accept':'application/*+xml;version=5.1','x-vcloud-authorization':token},verify=False).text
	return parseString(xml).getElementsByTagName('Org')[0].attributes['href'].value

def getvcdurl(u,token):
	xml=get(orgurl,headers={'Accept':'application/*+xml;version=5.1','x-vcloud-authorization':token},verify=False).text
	#print xml
	for e in parseString(xml).getElementsByTagName('Link'):
		if e.attributes['type'].value=='application/vnd.vmware.vcloud.vdc+xml':
			return e.attributes['href'].value
	return ''

def getvms(u,token):
	xml=get(u,headers={'x-vcloud-authorization':token,'Accept':'application/*+xml;version=5.1'},verify=False).text
	return {e.attributes['name'].value:e.attributes['href'].value for e in parseString(xml).getElementsByTagName('Vm')}

def getvapps(u,token):
	xml=get(u,headers={'Accept':'application/*+xml;version=5.1','x-vcloud-authorization':token},verify=False).text
	return {e.attributes['name'].value:e.attributes['href'].value for e in parseString(xml).getElementsByTagName('ResourceEntity') if e.attributes['type'].value=='application/vnd.vmware.vcloud.vApp+xml'}

def poweractionvm(u,token,action='reset'):
	xml=get(u,headers={'Accept':'application/*+xml;version=5.1','x-vcloud-authorization':token},verify=False).text
	#print xml
	actionurl=[e.attributes['href'].value for e in parseString(xml).getElementsByTagName('Link') if e.attributes['rel'].value=='power:'+ action]
	if len(actionurl)==1:
		#print actionurl[0]
		res=post(actionurl[0],headers={'Accept':'application/*+xml;version=5.1','x-vcloud-authorization':token},verify=False)
		if res.status_code==202:
			return True
	return False

def getcred():
	p=os.path.expanduser('~/')
	try:
		f=open(p+'.vcloud')
		c=json.loads(f.read())
		f.close()
	except:
		user=raw_input('vCloud username:')
		pw=getpass('vCloud password:')
		f=open(p+'.vcloud','w')
		c={'username':user,'password':pw}
		f.write(json.dumps(c))
		f.close()
	return c

if __name__ == '__main__':
	v=get('https://www.cloud.kth.se/api/versions',verify=False).text
	for e in parseString(v).getElementsByTagName('VersionInfo'):
		ver=e.getElementsByTagName('Version')[0].childNodes[0].data
		if ver=='5.1':
			u=e.getElementsByTagName('LoginUrl')[0].childNodes[0].data
	cred=getcred()
	x=post(u,auth=HTTPBasicAuth(cred['username'], cred['password']),headers={'Accept':'application/*+xml;version=5.1'},verify=False)
	if x.status_code==200:
		vca=x.headers['x-vcloud-authorization']
	else:
		sys.exit(1)
	orgurl=getorgurl(vca)
	vdcurl=getvcdurl(orgurl,vca)
	print vdcurl
	vapps=getvapps(vdcurl,vca)
	print vapps
	vms=dict(sum([getvms(vapps[k],vca).items() for k in vapps.keys()],[]))
	for k in vms.keys():
			print poweractionvm(vms[k],vca,'reset')