from django.http import JsonResponse
from django.shortcuts import render
from .models import RouterData
from django.contrib.auth.decorators import login_required
from pysnmp.entity.rfc3413.oneliner import cmdgen
import time
from pysnmp import hlapi


@login_required(login_url='/login/')
def home(request):
    if request.method == 'POST':
        ip = request.POST.get("ip", "")
        interface = request.POST.get("interface", "")
        return render(request, 'graph.html', context={'ip': ip, 'interface': interface})
    if request.method == 'GET':
        return render(request, 'home.html')


@login_required(login_url='/login/')
def getDataGraph(request):
    if request.method == 'POST':
        device_iP = request.POST.get("ip", "")
        interface = request.POST.get("interface", "")
        old = RouterData.objects.filter(ip=ip, interface=interface).latest()
        print (device_iP, interface)
        # ///////////////////////////////////

        # device_iP = '217.139.253.32'  # by user
        # device_uptime_oid = '1.3.6.1.2.1.1.3.0'
        ifInOctets = "1.3.6.1.2.1.2.2.1.10." + interface  # in by user;
        ifOutOctets = "1.3.6.1.2.1.2.2.1.16." + interface  # out
        ifSpeed = "1.3.6.1.2.1.2.2.1.5." + interface
        # hlapi.CommunityData('know!where')
        # time_data = get(device_iP, ['1.3.6.1.2.1.1.3.0'], hlapi.CommunityData('know!where'))
        in_data = get(device_iP, [ifInOctets], hlapi.CommunityData('know!where'))
        out_data = get(device_iP, [ifOutOctets], hlapi.CommunityData('know!where'))
        speed_data = get(device_iP, [ifSpeed], hlapi.CommunityData('know!where'))
        time.sleep(8)
        in_data1 = get(device_iP, [ifInOctets], hlapi.CommunityData('know!where'))
        out_data1 = get(device_iP, [ifOutOctets], hlapi.CommunityData('know!where'))
        # speed_data1 = get(device_iP, [ifSpeed], hlapi.CommunityData('know!where'))

        # Delta(in) * 8*100 /(delta_time ) * speed
        print(in_data1[ifInOctets], in_data[ifInOctets])
        print(in_data1[ifInOctets] - in_data[ifInOctets])
        print(speed_data[ifSpeed])

        bandWidthin = (in_data1[ifInOctets] - in_data[ifInOctets]) * 8 * 100 / (8 * speed_data[ifSpeed])
        bandWidthout = (out_data1[ifOutOctets] - out_data[ifOutOctets]) * 8 * 100 / (8 * speed_data[ifSpeed])
        print(bandWidthin, bandWidthout)
        # /////////////////////////////////
        return JsonResponse({'input': bandWidthin, 'output': bandWidthout})


def get(target, oids, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.getCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_object_types(oids)
    )
    return fetch(handler, 1)[0]


def construct_object_types(list_of_oids):
    object_types = []
    for oid in list_of_oids:
        object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))
    return object_types


def fetch(handler, count):
    result = []
    for i in range(count):
        try:
            error_indication, error_status, error_index, var_binds = next(handler)
            if not error_indication and not error_status:
                items = {}
                for var_bind in var_binds:
                    items[str(var_bind[0])] = cast(var_bind[1])
                result.append(items)
            else:
                raise RuntimeError('Got SNMP error: {0}'.format(error_indication))
        except StopIteration:
            break
    return result


def cast(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value)
            except (ValueError, TypeError):
                pass
    return value


def get_bulk(target, oids, credentials, count, start_from=0, port=161,
             engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.bulkCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        start_from, count,
        *construct_object_types(oids)
    )
    return fetch(handler, count)


def get_bulk_auto(target, oids, credentials, count_oid, start_from=0, port=161,
                  engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    count = get(target, [count_oid], credentials, port, engine, context)[count_oid]
    return get_bulk(target, oids, credentials, count, start_from, port, engine, context)
