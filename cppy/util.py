# coding: utf-8
from cppy.CpUtil import CpCodeMgr
from cppy.CpUtil import CpCybos

import queue

def getCommonStockCods():
    '''
    일반적인 종목코드를 리스트로 반환합니다.
    (거래소+코스닥, 우선주제외, 스팩제외, 경고위험제외, 관리종목제외, 거래정지중단제외, 리츠워런트ETFETN제외)
    :return: code list
    '''
    ret = []
    codmgr = CpCodeMgr()

    kospi_cods = codmgr.GetStockListByMarket(CpCodeMgr.CPC_MARKET_KOSPI)
    kosdq_cods = codmgr.GetStockListByMarket(CpCodeMgr.CPC_MARKET_KOSDAQ)

    # 리스트를 합침
    cods_list = kospi_cods + kosdq_cods

    for cod in cods_list:
        # 감리구분: 정상 + 주의 종목 까지
        cont_kind = codmgr.GetStockControlKind(cod)
        if cont_kind != CpCodeMgr.CPC_CONTROL_NONE:
            if cont_kind != CpCodeMgr.CPC_CONTROL_ATTENTION:
                continue

        # 관리구분: 관리종목 제외
        super_kind = codmgr.GetStockSupervisionKind(cod)
        if super_kind != CpCodeMgr.CPC_SUPERVISION_NONE:
            continue

        # 상태구분: 정상 (정지,중단 제외)
        stat_kind = codmgr.GetStockStatusKind(cod)
        if stat_kind != CpCodeMgr.CPC_STOCK_STATUS_NORMAL:
            continue

        # 부구분 : 주권만 선택 (ETF, 리츠, 워런트 등등 제외)
        sec_kind = codmgr.GetStockSectionKind(cod)
        if sec_kind != CpCodeMgr.CPC_KSE_SECTION_KIND_ST:
            continue

        # 우선주제외
        if codmgr.isCommonStock(cod) == False:
            continue

        # 스팩제외
        if codmgr.isSpacStock(cod) == True:
            continue

        # 통과종목 append
        ret.append(cod)

    ret.sort()
    return ret


def generatorIntervalRequest(q, waitTick=250, limitType=CpCybos.LT_NONTRADE_REQUEST):
    '''
    Rq/Rp 균등시간 요청하기 위한 제네레이터
    :param q: Request 메서드가 있는 객체
    :param waitTick:  next 호출 횟수 간격
    :param limitType: 제한타입 Default: nontrade
    :return: Request호출시 True, 그외 False
    '''
    if q.__class__.__name__ != 'Queue':
        raise 'param queu error'

    cpcybos = CpCybos()
    desc_cnt = 0

    while True:
        ret = False
        # tick count 수가 없으면 (request 가능)
        if desc_cnt <= 0:
            # 가능 개수를 센다.
            rcnt = cpcybos.GetLimitRemainCount(limitType)
            if rcnt > 0:
                try:
                    # queue에서 가져옴
                    itm = q.get_nowait()
                    itm.Request()
                    ret = True
                    desc_cnt = waitTick
                except queue.Empty:
                    pass
            else:
                # wait more
                pass
        else:
            desc_cnt -= 1

        # generator
        yield ret






import re

def parseHelpPage(txt):
    '''
    코드생성해주는 유틸리티 펑션
    Help 파일의 페이지의 설명을 읽어 샘플클래스로 생성,
    정확하지 않으니 제대로 생성이 안될 경우 직접 작성하세요
    '''
    #start parse
    lines = txt.strip().split('\n')
    cls_nm = lines[0].strip()
    #print('클래스명: ', cls_nm)

    desc_cls = '' # 클래스 설명
    comu_typ = 'Request/Reply' # 통신종류
    module_nm = '' # 모듈위치

    # cut idx
    setinput_line = 0
    getheader_line = 0
    getdata_line = 0
    getsub_line = 0
    lines = lines[1:]

    # 메서드 위치 찾기
    for i, line in enumerate(lines):
        if line.find('설명') != -1:
            desc_cls = lines[i+1]
        if line.find('통신종류') != -1:
            comu_typ = lines[i+1]
        if line.find('모듈 위치') != -1:
            module_nm = lines[i+1]
        if line.find('object.SetInputValue') != -1:
            setinput_line = i
        if line.find('object.GetHeaderValue') != -1:
            getheader_line = i
        if line.find('object.GetDataValue') != -1:
            getdata_line = i
        if line.find('object.Subscribe') != -1:
            getsub_line = i

    #print(desc_cls, comu_typ, module_nm,setinput_line, getheader_line, getdata_line)

    # setinputvalue extract
    setinput_list = []
    is_exist_prev = False
    prev_field_no = 0
    prev_field_type = ''
    prev_field_nm = ''
    prev_field_desc = ''
    for i , line in enumerate(lines[setinput_line: getheader_line]):
        #print(i, line)
        m = re.search(r'^(\d+)\s*-\s*\(\s*(\w+)\s*\)(.*)', line)
        if m:
            if is_exist_prev == False:
                is_exist_prev = True
            else:
                #print(prev_field_no, prev_field_type, prev_field_nm, prev_field_desc)
                setinput_list.append((prev_field_no, prev_field_type, prev_field_nm, prev_field_desc))
            prev_field_no = m.group(1)
            prev_field_type = m.group(2)
            prev_field_nm = m.group(3)
            prev_field_desc = ''

        else:
            if is_exist_prev == False:
                prev_field_desc = ''
            else:
                prev_field_desc += line.strip()
                if line.strip() != '':
                    prev_field_desc += '\n'

    # last
    if is_exist_prev == True:
        setinput_list.append((prev_field_no, prev_field_type, prev_field_nm, prev_field_desc))

    #setheadervalue extract
    getheader_list = []
    is_exist_prev = False
    prev_field_no = 0
    prev_field_type = ''
    prev_field_nm = ''
    prev_field_desc = ''
    for i , line in enumerate(lines[getheader_line: getdata_line]):
        #print(i, line)
        m = re.search(r'^(\d+)\s*-\s*\(\s*(\w+)\s*\)(.*)', line)
        if m:
            if is_exist_prev == False:
                is_exist_prev = True
            else:
                #print(prev_field_no, prev_field_type, prev_field_nm, prev_field_desc)
                getheader_list.append((prev_field_no, prev_field_type, prev_field_nm, prev_field_desc))

            prev_field_no = m.group(1)
            prev_field_type = m.group(2)
            prev_field_nm = m.group(3)
            prev_field_desc = ''

        else:
            if is_exist_prev == False:
                prev_field_desc = ''
            else:
                prev_field_desc += line.strip()
                if line.strip() != '':
                    prev_field_desc += '\n'

    # last
    #print(prev_field_no, prev_field_type, prev_field_nm, prev_field_desc)
    if is_exist_prev == True:
        getheader_list.append((prev_field_no, prev_field_type, prev_field_nm, prev_field_desc))

    # getdatavalue extract
    getdata_list = []
    is_exist_prev = False
    prev_field_no = 0
    prev_field_type = ''
    prev_field_nm = ''
    prev_field_desc = ''
    for i , line in enumerate(lines[getdata_line: getsub_line]):
        #print(i, line)
        m = re.search(r'^(\d+)\s*-\s*\(\s*(\w+)\s*\)(.*)', line)
        if m:
            if is_exist_prev == False:
                is_exist_prev = True
            else:
                #print(prev_field_no, prev_field_type, prev_field_nm, prev_field_desc)
                getdata_list.append((prev_field_no, prev_field_type, prev_field_nm, prev_field_desc))

            prev_field_no = m.group(1)
            prev_field_type = m.group(2)
            prev_field_nm = m.group(3)
            prev_field_desc = ''

        else:
            if is_exist_prev == False:
                prev_field_desc = ''
            else:
                prev_field_desc += line.strip()
                if line.strip() != '':
                    prev_field_desc += '\n'

    # last
    #print(prev_field_no, prev_field_type, prev_field_nm, prev_field_desc)
    if is_exist_prev == True:
        getdata_list.append((prev_field_no, prev_field_type, prev_field_nm, prev_field_desc))


    # module rename
    if module_nm.find('cpdib') != -1:
        module_nm = 'CpDib'
    if module_nm.find('cpsysdib') != -1:
        module_nm = 'CpSysDib'
    if module_nm.find('cptrade') != -1:
        module_nm = 'CpTrade'
    if module_nm.find('cputil') != -1:
        module_nm = 'CpUtil'

    # 요청 통신 종류
    send_nm = ''
    send_nm_u = ''
    recv_nm = ''
    if comu_typ.strip() == 'Request/Reply':
        send_nm = 'request'
        send_nm_u = 'Request'
        recv_nm = 'response'
    else:
        send_nm = 'subscribe'
        send_nm_u = 'Subscribe'
        recv_nm = 'publish'


    basic_format = """
from cppy.%s import %s

class Sample%s(object):
    '''%s'''
    def __init__(self):
        self.com = %s(self.%s)
    def %s(self):
        %s
        self.com.%s()
    def %s(self):
        %s

        %s
    """

    input_format = '\n\t\t'.join(["self.com.SetInputValue(%s, s%s) # %s %s"%(itm[0],itm[0], itm[1], itm[2]) for itm in setinput_list])
    header_format = '\n\t\t'.join(
        ["h%s = self.com.GetHeaderValue(%s) # %s %s " % (itm[0], itm[0], itm[1], itm[2]) for itm in getheader_list])

    data_format = ''
    if len(getdata_list) > 0:
        data_format = 'for i in range(cnt): # 조회할 건수를 세팅하세요\n\t\t\t'
        data_format += '\n\t\t\t'.join(["d%s = self.com.GetDataValue(%s, i) # %s %s"%(itm[0],itm[0], itm[1], itm[2]) for itm in getdata_list])

    return (basic_format%(
        module_nm, cls_nm,
        cls_nm,
        desc_cls,
        cls_nm, recv_nm,
        send_nm,
        input_format,
        send_nm_u,
        recv_nm,
        header_format,
        data_format
        ))