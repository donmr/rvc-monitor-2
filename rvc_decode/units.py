def tempC2F(degc):
    return round( ( degc * 9 / 5 ) + 32, 1 )

def convert_unit(myvalue,myunit,mytype):
    new_value = myvalue
    mu = myunit.lower()

    if mu == 'pct':
        if myvalue != 255:
            new_value = str(myvalue / 2) + '%'

    elif mu == 'deg c':
        new_value = 'n/a'
        if mytype == 'uint8' and myvalue != ( 1 << 8 ) - 1:
            new_value = myvalue - 40
        elif mytype == 'uint16' and myvalue != ( 1 << 16 ) - 1:
            new_value = round( ( myvalue * 0.03125 ) - 273, 2 )

    elif mu == 'v':
        new_value = 'n/a'
        if mytype == 'uint8' and myvalue != ( 1 << 8 ) - 1:
            new_value = myvalue
        elif mytype == 'uint16' and myvalue != ( 1 << 16 ) - 1:
            new_value = round( myvalue * 0.05, 2 )

    elif mu == 'a':
        new_value = 'n/a'
        if mytype == 'uint8':
            new_value = myvalue
        elif mytype == 'uint16' and myvalue != ( 1 << 16 ) - 1:
            new_value = round( ( myvalue * 0.05 ) - 1600 , 2)
        elif mytype == 'uint32' and myvalue != ( 1 << 32 ) - 1:
            new_value = round( ( myvalue * 0.001 ) - 2000000 , 3)

    elif mu == 'w':
        new_value = 'n/a'
        if mytype == 'uint16' and myvalue != ( 1 << 16 ) - 1:
            new_value = myvalue

    elif mu == 'ah':
        new_value = 'n/a'
        if mytype == 'uint16' and myvalue != ( 1 << 16 ) - 1:
            new_value = myvalue

    elif mu == 'ohm':
        new_value = 'n/a'
        if mytype == 'uint16' and myvalue != ( 1 << 16 ) - 1:
            new_value = myvalue

    elif mu == 'hz':
        if mytype == 'uint16' and myvalue != ( 1 << 16 ) - 1:
            new_value = round( myvalue / 128 , 2)

    elif mu == 'sec':
        if mytype == 'uint8' and myvalue > 240 and myvalue < 251:
            new_value = ( ( myvalue - 240 ) + 4 ) * 60
        elif mytype == 'uint16':
            new_value = myvalue * 2

    elif mu == 'bitmap':
        new_value = "{0:08b}".format(myvalue)

    #### J1939

    elif mu == 'rpm':
        if mytype == 'uint16' and myvalue != ( 1 << 16 ) - 1:
            new_value = round( myvalue / 8, 2)

    return new_value
