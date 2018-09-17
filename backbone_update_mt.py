import sys, paramiko, re, time, datetime, os, select, configparser
from log_class import *
from version_mt_class import *

channel_data = bytes()
buf = ''

upload_526 = "/tool fetch url=http://172.16.11.23/routeros-mipsbe-5.26.npk\r\n"
upload_6381 = "/tool fetch url=http://172.16.11.23/routeros-mipsbe-6.38.1.npk\r\n"
upload_643 = "/tool fetch url=http://172.16.11.23/routeros-mipsbe-6.43.npk\r\n"

cfg = configparser.ConfigParser()
cfg.read('config.ini')
#check arguments
if len(sys.argv) < 3:
    print('''\nToo few arguments. Usage: backbone_update_mt.py <config_section> <ip_list> ''')
    exit()

config = sys.argv[1]
ip_list = sys.argv[2]
user = cfg[config]['LOGIN']
password = cfg[config]['PASSWORD']
port = cfg[config]['PORT']
scheduler = cfg[config]['SCHEDULER']
script = cfg[config]['SCRIPT']
script = script[1:]
script = script.replace('=/', '="/')
timeout = 5

#based on actual version, we act diffrent way
def update(channel, log):
    if float(version) < 5.26:
        log.debug('less 5.26')
        channel.send(upload_526)
    elif float(version) >= 5.26 and float(version) < 6.38:
        log.debug('greater or equal 5.26 and less then 6.38')
        channel.send(upload_6381)
    elif float(version) >= 6.38 and float(version) < 6.43:
        log.debug('greater or equal 6.38 and less then 6.43')
        #we need to regenerate ssh key, after update to higher then 6.42.1, in case to keep asccess via ssh
        channel.send(scheduler+'\r\n')
        #too fast sending commands, cause error. 
        time.sleep(2)
        channel.send(script+'\r\n')
        time.sleep(2)
        channel.send(upload_643)                   
    else:
        log.debug('case not handled')
        log.error_log(ip, buf+'\r\ncase not handled\r\n')
        return False
    return True

#status: finished
#some version send "finished" at end of download. Some not, whats why we compare total, and downloaded bytes
def downloaded(channel, log):
    channel_data = bytes()
    now = int(time.time())
    while True:
        timeout = 5
        r,w,e = select.select([channel], [], [], timeout)
        if channel in r:
            channel_data += channel.recv(9999)
            buf = channel_data.decode('utf-8')
            #log.debug(buf) mocno smieci output
            total_pos = buf.rfind('total: ')
            total = buf[total_pos:total_pos+15]
            total = total.strip('\r\n')
            downloaded_pos = buf.rfind('downloaded: ')
            downloaded = buf[downloaded_pos:downloaded_pos+20]
            downloaded = downloaded.strip('\r\n')
            downloaded = downloaded.replace('downloaded: ', 'total: ')
            #older version sends finished, but dont show last package data. Compare is not possible.
            if buf.find('status: finished') != -1 and buf.endswith('] > ') == True:
                log.debug('finished')
                log.debug(buf)
                return True
            #check package download is complete
            if downloaded == total and total != '':
                log.debug(buf)
                log.debug('package downloaded\n')
                return True
        else:
            #in case of broken connection
            if is_timeout(now):
                clean_flags()
                return False

#have to set delay reboot in case of 750up
def get_model(channel, log):
    now = int(time.time())
    channel_data = bytes()
    log.debug('checking is 750up model')
    channel.send("/system routerboard print\r\n")
    while True:
        timeout = 5
        r,w,e = select.select([channel], [], [], timeout)
        if channel in r:
            channel_data += channel.recv(9999)
            buf = channel_data.decode('utf-8')
            if buf.find('model: ') != -1:
                log.debug('got model in buf')
                log.debug(buf)
                if buf.find('750UP') != -1:
                    #going sleep beffore reboot
                    log.debug('got 750up, going sleep for 90s')
                    time.sleep(90)
                    return 0
                else:
                    log.debug('is not 750up')
                    return 1
            else:
                log.debug('no model found')
        else:
            #in case of broken connection
            if is_timeout(now):
                return -1

def reboot(channel, log):
    now = int(time.time())
    channel_data = bytes()
    is750 = get_model(channel, log)
    channel.send('/system reboot\r\n')
    while True:
        timeout = 5
        r,w,e = select.select([channel], [], [], timeout)
        if channel in r:
            channel_data += channel.recv(9999)
            buf = channel_data.decode('utf-8')
            if buf.find('Reboot, yes? [y/N]:') != -1:
                log.debug('got reboot question')
                log.debug(buf)
                channel.send('n\r\n')
                log.debug('sended reboot confirmaton')
                if is750 == 0:
                    log.debug('going sleep for another 90s')
                    time.sleep(90)
                #we only what do it once, cleaning data
                channel_data = bytes()
                '''if we send n as confirmation for debug purposes, uncomment below line to exit reboot function. Otherwise comment it, so we can pass to next if condition'''
                return True
            if buf.find('system will reboot shortly') != -1:
                log.debug('got reboot confirmation')
                log.debug(buf)
                #we only what do it once, cleaning data
                channel_data = bytes()
                return True
        else:
            if is_timeout(now):
                clean_flags()
                return False

def is_timeout(now):
    if(int(time.time()) > now + 60):
        log.debug(str(now))
        log.debug('timeout 60 s')
        log.error_log(ip, 'timeout 60 s')
        return True

def clean_flags():
    quit_loop = True
    get_version = False
    send_get_version = False    


def file_len(ip_list):
    with open(ip_list) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

file = ip_list.replace('.txt', '')
#if file name last char beffore dot is t, then its cutted. Dont know why.
file_debug = file + '-' + cfg[config]['DEBUG_FILE']
file_error = file + '-' + cfg[config]['ERROR_FILE']
log = Log(file_debug, file_error)

print(ip_list)
ip_count = file_len(ip_list) #todo: check len, if 0 then exit
file_in = open(ip_list, 'r')
for i, line in enumerate(file_in):
    try:
        quit_loop = False
        get_version = False
        send_get_version = False
        buf_ip = line
        ip = buf_ip.strip( '\n' )

        log.debug('############################################\n')
        log.debug(ip)
        print('ip_address: ', ip)
        
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, port=port, username=user, password=password, timeout=10)
        
        log.debug("logged in\n")
        now = int(time.time())
        channel = client.invoke_shell()
        channel_data = bytes()
        while quit_loop == False: #todo: fix that unecessery loop condition
            timeout = 5
            r,w,e = select.select([channel], [], [], timeout)
            if channel in r:
                channel_data += channel.recv(9999)
                buf = channel_data.decode('utf-8')
                if buf.endswith('] > ') == True:
                    log.debug(buf)
                    log.debug('we found prompt')
                    if buf.find('version: ') != -1 and get_version == False:
                        try:
                            version = Version()
                            version = version.find_version(buf)
                        except:
                            log.log_error(ip, " exception occured: \r\n" + "-------------- buf start -------------\r\n" + buf + '\r\n-------------- buf end -------------')
                            quit_loop = True
                            get_version = False
                            send_get_version = False
                            client.close()
                        
                        get_version = True
                        log.debug(version)
                    if get_version == False and send_get_version == False:
                        log.debug('checking version')
                        channel.send("system resource print\r\n")
                        send_get_version = True
                    if get_version == True:
                        log.debug('got version, updating')
                        if update(channel, log):
                            if downloaded(channel, log):
                                if reboot(channel, log):
                                    log.debug('everything should go fine ;)')
                                    clean_flags()
                                    break
                        else:
                            channel_data = bytes()
                            channel.send('quit\r\n')
                            clean_flags()
                            break
                        
                    if buf.find('bad command name') != -1:
                        log.debug('bad command name')
                        log.error_log(ip, buf+'\r\nbad command name\r\n')
                        clean_flags()
                        break   
            log.debug("t/o")
            if is_timeout(now):
                clean_flags()
                break
               
        percent = i / ip_count * 100
        print("---------------- done:  ", int(percent), "% -----------------")
    except paramiko.ssh_exception.AuthenticationException as ssherr:
        log.debug(str(ssherr))
        #print (ssherr)
        client.close()
    except paramiko.ssh_exception.SSHException as ssherr:
        log.debug(str(ssherr))
        #print (ssherr)
        client.close()
    except paramiko.ssh_exception.socket.error as ssherr:
        log.debug(str(ssherr))
        #print (ssherr)
        client.close()
    except paramiko.ssh_exception.BadHostKeyException as ssherr:
        log.debug(str(ssherr))
        #print (ssherr)
        client.close()
    finally:
        client.close()
log.debug("done")
	
