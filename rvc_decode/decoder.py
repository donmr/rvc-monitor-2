from .units import convert_unit, tempC2F


def rvc_decode(mydgn, mydata, spec):
    result = {'data':mydata, 'name':"UNKNOWN-"+mydgn }
    if mydgn not in spec:
        return result

    decoder = spec[mydgn]
    result['name'] = decoder['name']
    params = []
    try:
        params.extend(spec[decoder['alias']]['parameters'])
    except:
        pass

    try:
        params.extend(decoder['parameters'])
    except:
        pass

    param_count = 0
    for param in params:
        try:
            mybytes = get_bytes(mydata,param['byte'])
            myvalue = int(mybytes,16) # Get the decimal value of the hex bytes
        except:
            # If you get here, it's because the params had more bytes than the data packet.
            # Thus, skip the rest of the processing
            continue

        try:
            myvalue = get_bits(myvalue,param['bit'])
            if param['type'][:4] == 'uint':
                myvalue = int(myvalue,2)
        except:
            pass

        try:
            myvalue = convert_unit(myvalue,param['unit'],param['type'])
        except:
            pass

        result[param['name']] = myvalue

        try:
            if param['unit'].lower() == 'deg c':
                result[param['name'] + ' F'] = tempC2F(myvalue)
        except:
            pass

        try:
            mydef = 'undefined'
            mydef = param['values'][int(myvalue)]
            # int(myvalue) is a hack because the spec yaml interprets binary bits
            # as integers instead of binary strings.
            result[param['name'] + " definition"] = mydef
        except:
            pass

        param_count += 1

    if param_count == 0:
        result['DECODER PENDING'] = 1

    return result

def get_bytes(mybytes,byterange):
    try:
        bset=byterange.split('-')
        sub_bytes = "".join(mybytes[i:i+2] for i in range(int(bset[1])*2, (int(bset[0])-1)*2, -2))
    except:
        sub_bytes = mybytes[ byterange * 2 : ( byterange + 1 ) * 2 ]

    return sub_bytes

def get_bits(mydata,bitrange):
    mybits="{0:08b}".format(mydata)
    try:
        bset=bitrange.split('-')
        sub_bits = mybits[ 7 - int(bset[1]) : 8 - int(bset[0]) ]
    except:
        sub_bits = mybits[ 7 - bitrange : 8 - bitrange ]

    return sub_bits

# Convert a string to something easier to use as a JSON parameter by
# converting spaces and slashes to underscores, and removing parentheses.
# e.g.: "Manufacturer Code (LSB) in/out" => "manufacturer_code_lsb_in_out"
def parameterize_string(string):
    return string.translate(string.maketrans(' /', '__', '()')).lower()
