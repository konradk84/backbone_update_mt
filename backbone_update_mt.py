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

def file_len(ip_list):
    with open(ip_list) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

file = ip_list.strip('.txt')
file_debug = file + '_' + cfg[config]['DEBUG_FILE']
file_error = file + '_' + cfg[config]['ERROR_FILE']
log = Log(file_debug, file_error)

print(ip_list)
ip_count = file_len(ip_list) #todo: check len, if 0 then exit
file_in = open(ip_list, 'r')
for i, line in enumerate(file_in):
    try:
        quit_loop = False
        prompt = False
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
                    log.debug('We found prompt')
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
                        log.debug('Checking version')
                        channel.send("system resource print\r\n")
                        send_get_version = True
                    if get_version == True:
                        log.debug('Got version, updating')
                        if float(version) < 5.26:
                            log.debug('less 5.26')
                            #channel.send(upload_526)
                        elif float(version) >= 5.26 and float(version) < 6.38:
                            log.debug('greater or equal 5.26 and less then 6.38')
                            #channel.send(upload_6381)
                        elif float(version) >= 6.38 and float(version) < 6.43:
                            log.debug('greater or equal 6.38 and less then 6.43')
                            #channel.send(scheduler+'\r\n')
                            #time.sleep(2)
                            #channel.send(script+'\r\n')
                            #time.sleep(2)
                            #channel.send(upload_643)                   
                        else:
                            log.debug('case not handled')
                            log.error_log(ip, buf+'\r\ncase not handled\r\n')
                        #status: finished
                        time.sleep(3)
                        channel_data = bytes()
                        '''
                        while channel.recv_ready():
                            channel_data += channel.recv(9999)
                            #print('channel_data: ', channel_data)
                            time.sleep(3)
                        #porownujemy wartosci od konca total oraz downloaded by upewnic sie ze pobralismy wszystko
                        buf = channel_data.decode('utf-8')
                        log.debug(buf)
                        total_pos = buf.rfind('total: ')
                        total = buf[total_pos:total_pos+15]
                        total = total.strip('\r\n')
                        #print('total: ', total)
                        downloaded_pos = buf.rfind('downloaded: ')
                        downloaded = buf[downloaded_pos:downloaded_pos+20]
                        downloaded = downloaded.strip('\r\n')
                        downloaded = downloaded.replace('downloaded: ', 'total: ')
                        #print('downloaded: ', downloaded)
                        log.debug('total i downloaded:')
                        log.debug(total)
                        log.debug(downloaded)
                        if total == '':
                            log.debug('@@@ total jest pusty @@@')
                        if downloaded == total and total != '':
                            log.debug(buf)
                            log.debug('paczka pobrana\n')
                        '''
                        #find 750 in model
                        channel.send("/system routerboard print\r\n")
                        channel_data = bytes()
                        time.sleep(2)
                        while channel.recv_ready(): #bug
                            channel_data += channel.recv(9999)
                            log.debug(str(channel_data))
                            time.sleep(4)
                        buf = channel_data.decode('utf-8')    
                        print('tu?')
                        log.debug(buf)
                        if buf.find('750UP') != -1:
                            log.debug('jest 750UP')
                            time.sleep(120)
                            #channel.send('system reboot\r\n')
                            time.sleep(120)
                            log.debug('wyspany')
                        else:
                            log.debug('nie jest 750UP')
                            #channel.send('system reboot\r\n')
                        
                        channel_data = bytes()
                        channel.send('quit\r\n')
                        quit_loop = True
                        get_version = False
                        break

                    if buf.find('bad command name') != -1:
                        log.debug('bad command name')
                        log.error_log(ip, buf+'\r\nbad command name\r\n')
                        quit_loop = True
                        get_version = False
                        send_get_version = False
                        break   
            log.debug("t/o")
            if(int(time.time()) > now + 60):
                log.debug('timeout 60 s')
                log.error_log(ip, 'timeout 60 s')
                quit_loop = True
                get_version = False
                send_get_version = False
                break   
        percent = i / ip_count * 100
        print("---------------- done:  ", int(percent), "% -----------------")
    except paramiko.ssh_exception.AuthenticationException as ssherr:
        debug(str(ssherr))
        print (ssherr)
        client.close()
    except paramiko.ssh_exception.SSHException as ssherr:
        debug(str(ssherr))
        print (ssherr)
        client.close()
    except paramiko.ssh_exception.socket.error as ssherr:
        debug(str(ssherr))
        print (ssherr)
        client.close()
    except paramiko.ssh_exception.BadHostKeyException as ssherr:
        debug(str(ssherr))
        print (ssherr)
        client.close()
    finally:
        client.close()
log.debug("done")
	
	
'''	
if float(version) < 5.26:
    print(adr, 'ma wersje softu mniejsza niz 5.26\n')
    ver_content = adr + ' ma wersje softu mniejsza niz 5.26\n'
    debug(ver_content)
    #pobierz 5.26
    channel.send(upload_526)
elif float(version) < 6.0 and float(version) > 5.25:
    print(adr, 'ma wersje softu mniejsza niz 6.0, wieksza niz 5.25\n')
    ver_content = adr + ' ma wersje softu mniejsza niz 6.0, wieksza niz 5.25\n'
    debug(ver_content)
    #pobierz 6.0
    channel.send(upload_6381)
elif float(version) > 6.0 and float(version) < 6.422: #aktualziacja wersji dziesietnej, brzydkie rozwiazanie
    print(adr, 'ma wersje softu wieksza niz 6.0\n')
    ver_content = adr + ' ma wersje softu wieksza niz 6.0\n'
    debug(ver_content)
    #pobierz 6.42.3
    channel.send(upload_6423)
else:
    print('wersja wieksza niz 6.42?\n')
    debug('wersja wieksza niz 6.42?\n')
    current_version = False
    client.close()
    prompt = False #wychodzimy z petli while
    break
'''