import io, sys

class Version():
    
    def __init__(self):
        self.version = ''
        self.ver_pos = 0
    
    def __len__(self):
        return len(self.version)

    def find_version(self, buf_str):
        rl = io.StringIO(buf_str)
        while True:
            line = rl.readline()
            if line.find('version: ' ) != -1:
                ver_pos = line.find('version: ')
                version = line[ver_pos:]
                version = version.strip('\r\n')
                version = version.replace('(stable)', '')
                version = version.replace('(bugfix)', '')
                version = version.replace('(testing)', '')
                version = version.replace('rc1', '')
                version = version.replace('rc2', '')
                version = version.replace('rc3', '')
                version = version.replace('rc4', '')
                version = version.replace('rc5', '')
                version = version.replace('rc6', '')
                version = version.replace('rc7', '')
                version = version.replace('rc8', '')
                version = version.replace('rc9', '')
                version = version.replace('rc', '')
                version = version.strip( ' ' )
                version = version.strip( 'version: ')
                #print('mamy ver5: ', version, ', o dlugosci: ', len(version))
                #input()
                if version.count('.') > 1:
                    ver_pos = version.rfind('.')
                    version = version[:ver_pos] + version[ver_pos+1:]
                if len(version) == 3:
                    version = version[:2] + '0' + version[2:]
                return version

