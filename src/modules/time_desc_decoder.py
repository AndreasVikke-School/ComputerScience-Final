""" Time Description INput decoder """
import re

def decode_time_desc(time_desc: str, description: bool) -> str:
    '''
        Decodes Time and Description input
    '''
    regex = r'^([0-2]?\d)(([:,\.])(\d+))?((\s+)([^\d].*))?'
    match = re.match(regex, time_desc)
    try:
        time_formatet = match.groups()[0]
        if match.groups()[2] in [',', '.']:
            time_formatet = '{0}{1}'.format(match.groups()[0], match.groups()[1].replace(',', '.'))
        elif match.groups()[2] == ':':
            if int(match.groups()[3]) < 35 and int(match.groups()[3]) > 4:
                time_formatet = '{0}{1}'.format(match.groups()[0], '.5')
            elif int(match.groups()[3]) > 35:
                time_formatet = '{0}'.format(int(match.groups()[0]) + 1)
            else:
                time_formatet = '{0}'.format(match.groups()[0])

        value = {
            'input': time_desc,
            'time': float(time_formatet)
        }
        if len(match.group()) == 6 and match.group()[6] is not None:
            value['description'] = match.groups()[6]
        elif description:
            return "Decode Error"
        return value
    except: # pylint: disable=bare-except
        print('Decode Error')
        return "Decode Error"
