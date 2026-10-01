import re
import os
import io
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI

st.set_page_config(
    page_title="B-SIGHT | 사외블록 통합 의사결정 플랫폼",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# OpenAI 클라이언트 초기화 (환경 변수 및 Streamlit Secrets 동시 지원)
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
if not openai_api_key:
    try:
        openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
    except FileNotFoundError:
        openai_api_key = ""

client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# ============================================================
# 0. ORIGINAL DASHBOARD DATA — preserved & expanded for 2027/2028
# ============================================================

SUPPLIER_MASTER = [{'name': '힘스2', 'cnt': 1150, 'weight': 139380, 'avgLeadTime': 24.4, 'ontimePct': 98.2, 'capaMonth': 6000, 'spec': '대불 2공장 150T OHC / E/ROOM(26년 5.9만T → 27년 7.9만T 급증)', 'topItem': 'E/ROOM, S/SHELL', 'totalManpower': 280, 'foreignPct': 42, 'skilledPct': 68, 'mgmtPoints': ['물량 급증(7.9만T) 대비 용접 자동화 장비 추가 도입 및 야간 교대조 정착 필요', '외국인 작업자(42%) 비율 증가에 따른 다국어 작업 표준서 비치 및 안전 교육 강화', 'E/ROOM 정밀 배관 치수 검사 프로세스 조기 확정으로 재작업률 0% 유지']}, {'name': '알파', 'cnt': 1492, 'weight': 72783, 'avgLeadTime': 26.4, 'ontimePct': 96.8, 'capaMonth': 3500, 'spec': '선수 3D 곡블록 특화 / 3공장 200T G/C (26년 3.7만T, 27년 3.5만T)', 'topItem': '선수BLOCK, BTM_BENCH', 'totalManpower': 190, 'foreignPct': 35, 'skilledPct': 75, 'mgmtPoints': ['선수 3D 곡부 성형 과정에서 숙련공(75%) 중심의 1대1 멘토링 체계 운영', '대형 200T 골리앗 크레인 양중 시 안전 규정 준수 여부 실시간 모니터링', '곡가공 오차 사전 시뮬레이션 도입으로 피팅 공정 Lead Time 단축']}, {'name': '메이드', 'cnt': 587, 'weight': 68542, 'avgLeadTime': 24.2, 'ontimePct': 99.5, 'capaMonth': 3000, 'spec': '플로팅도크(242×48m) / 120T 초과 Hopper 해상직송 (26년 3.4만T, 27년 3.5만T)', 'topItem': 'HOPPER', 'totalManpower': 160, 'foreignPct': 25, 'skilledPct': 82, 'mgmtPoints': ['플로팅도크 해상 직송 작업 특성상 기상 악화 대비 사전 출항 스케줄 조율 체계 구축', '초대형 Hopper 블록 적재 안전성 확보를 위한 결박(Lashing) 검수 프로세스 강화', '핵심 크레인 운전원 이탈 방지를 위한 장기 근속 인센티브 및 복지 지원']}, {'name': '태진', 'cnt': 590, 'weight': 56235, 'avgLeadTime': 28.0, 'ontimePct': 97.9, 'capaMonth': 2500, 'spec': '직영 55% 기술 인력 / E/ROOM, Hopper 조립 (26년 2.7만T, 27년 2.9만T)', 'topItem': 'E/ROOM, S/SHELL', 'totalManpower': 140, 'foreignPct': 30, 'skilledPct': 78, 'mgmtPoints': ['직영 비중이 높아(55%) 기술 숙련도가 안정적이나, 현장 고령화 대비 신규 인력 육성 필요', 'E/ROOM 및 S/SHELL 복합 모듈 조립 시 간섭 검사 사전 수행', '원부자재 입고 지연 시 공정 병목을 막기 위한 버퍼 재고 관리 표준화']}, {'name': '보원엠피1공장', 'cnt': 386, 'weight': 49579, 'avgLeadTime': 37.8, 'ontimePct': 94.5, 'capaMonth': 2500, 'spec': '300T/200T 골리앗 크레인 / 대형 UPP DECK 전담 (26년 2.7만T, 27년 2.2만T)', 'topItem': 'UPP DECK, 메가블록', 'totalManpower': 130, 'foreignPct': 38, 'skilledPct': 65, 'mgmtPoints': ['대형 메가블록 및 UPP DECK 취급 중량물 작업으로 크레인 신호수 교육 강화', '외국인 용접공(38%) 품질 편차 줄이기 위한 자동 용접기 활용 비중 확대', 'Lead Time이 다소 길어(37.8일) 공정 지연 방지를 위한 킥오프 미팅 주 1회 정례화']}, {'name': '힘스3', 'cnt': 374, 'weight': 46797, 'avgLeadTime': 25.1, 'ontimePct': 98.4, 'capaMonth': 2500, 'spec': '대불 3공장 가공/대조립 연계 S/SHELL, E/ROOM (26년 2.7만T, 27년 1.9만T)', 'topItem': 'S/SHELL_BENCH', 'totalManpower': 125, 'foreignPct': 40, 'skilledPct': 70, 'mgmtPoints': ['대불 3공장 가공 센터와 연계한 철판 소요량 실시간 싱크 관리', '외국인 인력 이탈률 모니터링 및 기숙사 환경 개선 등 복지 케어 실시', 'S/SHELL 벤치 조립 치수 정밀도 관리 철저']}, {'name': '동남', 'cnt': 512, 'weight': 29840, 'avgLeadTime': 22.0, 'ontimePct': 97.6, 'capaMonth': 2200, 'spec': '60m PIN JIG / OHC 100+50T 2대 [CNTR T-BHD 3순위 전담 & 초과분 수용]', 'topItem': 'CNTR T-BLK, T-BHD', 'totalManpower': 110, 'foreignPct': 32, 'skilledPct': 76, 'mgmtPoints': ['유일 초과 물량 유입 시 신속하게 투입될 수 있는 다기능공(Multi-skilled) 풀 운영', '60m PIN JIG 설비 유지보수 스케줄을 야간 및 주말로 분산하여 가동 중단 최소화', 'T-BHD 용접 변형 방지를 위한 대각선 대칭 용접 순서 준수 관리']}, {'name': '유일', 'cnt': 380, 'weight': 21000, 'avgLeadTime': 32.5, 'ontimePct': 97.3, 'capaMonth': 1750, 'spec': '컨테이너선 [CNTR T-BHD 1순위 전담] (타조선소 수주로 최대 21,000T Cap 한도 준수)', 'topItem': 'CNTR T-BHD, T-BLK', 'totalManpower': 95, 'foreignPct': 28, 'skilledPct': 80, 'mgmtPoints': ['타 조선소 물량 병행으로 인한 생산 캐파 포화(연간 21,000T 한도) 관리 철저', 'CNTR 격벽(T-BHD) 전문 숙련공(80%) 배치로 품질 신뢰도 최상위 유지', '물량 초과 즉시 대아 및 동남으로 자동 리밸런싱되는 실시간 경보 체계 연동']}, {'name': '대아', 'cnt': 295, 'weight': 17850, 'avgLeadTime': 36.7, 'ontimePct': 95.8, 'capaMonth': 1800, 'spec': '선미 Stern Boss 및 [CNTR T-BHD 2순위 전담 & 유일 초과분 흡수]', 'topItem': 'CNTR T-BHD, 선미BLOCK', 'totalManpower': 90, 'foreignPct': 35, 'skilledPct': 72, 'mgmtPoints': ['유일 물량 초과 유입 시 즉각 대응할 수 있는 여유 작업 스페이스 상시 확보', '선미 Stern Boss 등 고난도 주조품 결합 부위 비파괴 검사(NDT) 사전 예약', '공정 Lead Time(36.7일) 단축을 위한 사전 조립 가점 공정 도입 검토']}, {'name': '장성테크', 'cnt': 277, 'weight': 8103, 'avgLeadTime': 14.5, 'ontimePct': 99.6, 'capaMonth': 500, 'spec': '소형 Bench 및 HATCH COAMING 초단기 생산 (26년 4.0k T, 27년 4.1k T)', 'topItem': 'HATCH COAMING, Bench', 'totalManpower': 45, 'foreignPct': 20, 'skilledPct': 85, 'mgmtPoints': ['소형 벤치 고속 조립 라인으로 회전율이 매우 높아(14.5일) 원부자재 적기 공급 필수', 'Hatch Coaming 평탄도 및 치수 정밀도 관리로 현장 탑재 용이성 증대', '소수 정예 베테랑 중심(숙련공 85%)으로 이탈 리스크 관리 집중']}, {'name': 'DHMC', 'cnt': 21, 'weight': 587, 'avgLeadTime': 90.0, 'ontimePct': 100.0, 'capaMonth': 100, 'spec': '대형 Rudder 블록 전문 정밀 제작', 'topItem': 'Rudder 블록', 'totalManpower': 20, 'foreignPct': 10, 'skilledPct': 95, 'mgmtPoints': ['고도의 정밀 가공이 요구되는 Rudder 블록 전담으로 장기 제작 기간(90일) 엄수', '핵심 장인 기술자에 대한 의존도가 높아 건강 및 근속 관리 최우선', '출하 전 최종 삼차원 치수 검사 성적서 엄격 검증']}, {'name': '트레스', 'cnt': 19, 'weight': 447, 'avgLeadTime': 108.6, 'ontimePct': 100.0, 'capaMonth': 100, 'spec': '특수 구조물 블록 소량 전담', 'topItem': '특수BLOCK', 'totalManpower': 15, 'foreignPct': 10, 'skilledPct': 90, 'mgmtPoints': ['비정형 특수 구조물 설계 변경 발생 시 조선소 설계 부서와 즉시 핫라인 가동', '소량 다품종 생산 체제에 맞는 유연한 공정 스케줄링 운영', '철저한 품질 검증으로 무결점 납품 유지']}, {'name': '칸플랜트', 'cnt': 6, 'weight': 364, 'avgLeadTime': 18.7, 'ontimePct': 100.0, 'capaMonth': 100, 'spec': '단순 T-BHD 격벽 블록 제작', 'topItem': 'T-BHD', 'totalManpower': 12, 'foreignPct': 15, 'skilledPct': 80, 'mgmtPoints': ['단순 격벽 블록 위주로 신속한 턴어라운드(18.7일) 관리', '기본 안전 수칙 준수 및 작업장 정리정돈 상태 상시 점검', '납기 준수율 100% 지속 유지를 위한 주간 진도 관리']}]

MONTHLY_PIVOT = {'2026': [21207, 19420, 25310, 24605, 24317, 22969, 25881, 18572, 24168, 23254, 27545, 26244], '2027': [25724, 23910, 25529, 27064, 27174, 32791, 26954, 16846, 23332, 21446, 28485, 25709]}

WEIGHT_2027 = {'힘스2': 80584, '알파': 35382, '메이드': 35181, '태진': 28069, '보원엠피1공장': 21835, '힘스3': 20572, '동남': 31198, '유일': 21587, '대아': 25487, '장성테크': 4085, 'DHMC': 238, '트레스': 159, '칸플랜트': 0}

HISTORICAL_TOTALS = {'2023': {'weight': 224734, 'blocks': 2350}, '2024': {'weight': 229822, 'blocks': 2400}, '2025': {'weight': 260201, 'blocks': 2650}, '2026': {'weight': 283492, 'blocks': 3168}, '2027': {'weight': 304964, 'blocks': 3488}}

SHIP_MODELS = {
    '16000 CNTR': {'bom': [{'item': 'CNTR T-BHD (격벽)', 'ratio': 0.38, 'avgUnitWeight': 110.0, 'supplier1': '유일', 'supplier2': '대아', 'supplier3': '동남'}, {'item': 'S/SHELL_BENCH', 'ratio': 0.16, 'avgUnitWeight': 125.0, 'supplier1': '힘스3', 'supplier2': '태진'}, {'item': 'E/ROOM', 'ratio': 0.16, 'avgUnitWeight': 95.0, 'supplier1': '힘스2', 'supplier2': '태진'}, {'item': 'BTM_BENCH', 'ratio': 0.1, 'avgUnitWeight': 65.0, 'supplier1': '알파', 'supplier2': '장성테크'}, {'item': '선미BLOCK', 'ratio': 0.08, 'avgUnitWeight': 65.0, 'supplier1': '대아', 'supplier2': '알파'}, {'item': '선수BLOCK', 'ratio': 0.07, 'avgUnitWeight': 60.0, 'supplier1': '알파', 'supplier2': '대아'}, {'item': 'D/BTM', 'ratio': 0.05, 'avgUnitWeight': 130.0, 'supplier1': '태진', 'supplier2': '힘스2'}]}, 
    '15500 CNTR(LNG DF)': {'bom': [{'item': 'CNTR T-BHD (격벽)', 'ratio': 0.38, 'avgUnitWeight': 108.0, 'supplier1': '유일', 'supplier2': '대아', 'supplier3': '동남'}, {'item': 'S/SHELL_BENCH', 'ratio': 0.16, 'avgUnitWeight': 125.0, 'supplier1': '힘스3', 'supplier2': '태진'}, {'item': 'E/ROOM', 'ratio': 0.16, 'avgUnitWeight': 92.0, 'supplier1': '힘스2', 'supplier2': '태진'}, {'item': 'BTM_BENCH', 'ratio': 0.1, 'avgUnitWeight': 62.0, 'supplier1': '알파', 'supplier2': '장성테크'}, {'item': '선미BLOCK', 'ratio': 0.08, 'avgUnitWeight': 64.0, 'supplier1': '대아', 'supplier2': '알파'}, {'item': '선수BLOCK', 'ratio': 0.07, 'avgUnitWeight': 58.0, 'supplier1': '알파', 'supplier2': '대아'}, {'item': 'D/BTM', 'ratio': 0.05, 'avgUnitWeight': 128.0, 'supplier1': '태진', 'supplier2': '힘스2'}]}, 
    '174K LNG': {'bom': [{'item': 'HOPPER', 'ratio': 0.284, 'avgUnitWeight': 138.0, 'supplier1': '메이드', 'supplier2': '보원엠피1공장'}, {'item': 'UPP DECK', 'ratio': 0.211, 'avgUnitWeight': 112.5, 'supplier1': '보원엠피1공장', 'supplier2': '동남'}, {'item': 'E/ROOM', 'ratio': 0.194, 'avgUnitWeight': 92.3, 'supplier1': '힘스2', 'supplier2': '태진'}, {'item': '선수BLOCK', 'ratio': 0.132, 'avgUnitWeight': 81.9, 'supplier1': '알파', 'supplier2': '대아'}, {'item': 'S/SHELL', 'ratio': 0.059, 'avgUnitWeight': 124.5, 'supplier1': '태진', 'supplier2': '힘스2'}, {'item': '선미BLOCK', 'ratio': 0.058, 'avgUnitWeight': 126.9, 'supplier1': '대아', 'supplier2': '알파'}, {'item': 'T-BHD', 'ratio': 0.045, 'avgUnitWeight': 46.8, 'supplier1': '유일', 'supplier2': '동남'}, {'item': 'D/BTM', 'ratio': 0.016, 'avgUnitWeight': 153.7, 'supplier1': '태진', 'supplier2': '힘스2'}]}
}

ITEM_GROUPS = {
    "E/ROOM": ["힘스2", "태진"], "S/SHELL": ["힘스2", "힘스3", "태진"],
    "S/SHELL_BENCH": ["힘스3", "태진"], "선수BLOCK": ["알파", "대아"],
    "BTM_BENCH": ["알파", "장성테크"], "HOPPER": ["메이드", "보원엠피1공장", "태진"],
    "UPP DECK": ["보원엠피1공장", "동남"], "T-BHD": ["유일", "대아", "동남", "칸플랜트"],
    "CNTR T-BHD": ["유일", "대아", "동남"], "T-BLK": ["동남", "유일"],
    "선미BLOCK": ["대아", "알파"], "HATCH COAMING": ["장성테크"],
    "Rudder": ["DHMC"], "특수BLOCK": ["트레스"], "D/BTM": ["태진", "힘스2"],
}

VESSEL_DATASET = [
    {'hno': '8282', 'dock': '1', 'sunpyoNo': '26M01', 'shipType': '174K LNG', 'owner': 'NYK', 'klDate': '2026-01-15', 'lcDate': '2026-05-20', 'dlDate': '2026-09-30', 'year': '2026', 'blockCount': 72, 'totalWeight': 7420, 'topSupplier': '힘스2'}, 
    {'hno': '8222', 'dock': '1', 'sunpyoNo': '26M02', 'shipType': '174K LNG', 'owner': 'NYK', 'klDate': '2026-02-10', 'lcDate': '2026-06-25', 'dlDate': '2026-10-31', 'year': '2026', 'blockCount': 70, 'totalWeight': 7255, 'topSupplier': '메이드'}, 
    {'hno': '8323', 'dock': '1', 'sunpyoNo': '26M03', 'shipType': '174K LNG', 'owner': 'MOL', 'klDate': '2026-03-15', 'lcDate': '2026-07-20', 'dlDate': '2026-11-30', 'year': '2026', 'blockCount': 71, 'totalWeight': 7350, 'topSupplier': '보원엠피1공장'}, 
    {'hno': '8209', 'dock': '1', 'sunpyoNo': '26M04', 'shipType': '174K LNG', 'owner': 'MOL', 'klDate': '2026-04-10', 'lcDate': '2026-08-25', 'dlDate': '2026-12-31', 'year': '2026', 'blockCount': 70, 'totalWeight': 7255, 'topSupplier': '힘스2'}, 
    {'hno': '8318', 'dock': '2', 'sunpyoNo': '26M05', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2026-02-28', 'lcDate': '2026-07-15', 'dlDate': '2026-11-20', 'year': '2026', 'blockCount': 104, 'totalWeight': 7850, 'topSupplier': '유일'}, 
    {'hno': '8247', 'dock': '2', 'sunpyoNo': '26M06', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2026-04-20', 'lcDate': '2026-09-10', 'dlDate': '2027-01-15', 'year': '2026', 'blockCount': 102, 'totalWeight': 7650, 'topSupplier': '대아'}, 
    {'hno': '8294', 'dock': '2', 'sunpyoNo': '26M07', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2026-06-15', 'lcDate': '2026-11-05', 'dlDate': '2027-03-20', 'year': '2026', 'blockCount': 102, 'totalWeight': 7638, 'topSupplier': '동남'}, 
    {'hno': '8313', 'dock': '1', 'sunpyoNo': '26M08', 'shipType': '174K LNG', 'owner': 'KNOT', 'klDate': '2026-05-10', 'lcDate': '2026-09-25', 'dlDate': '2027-01-30', 'year': '2026', 'blockCount': 71, 'totalWeight': 7300, 'topSupplier': '힘스2'}, 
    {'hno': '8287', 'dock': '1', 'sunpyoNo': '26M09', 'shipType': '174K LNG', 'owner': 'KNOT', 'klDate': '2026-06-20', 'lcDate': '2026-11-10', 'dlDate': '2027-03-15', 'year': '2026', 'blockCount': 70, 'totalWeight': 7255, 'topSupplier': '메이드'}, 
    {'hno': '8278', 'dock': '2', 'sunpyoNo': '26M10', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'CMA CGM', 'klDate': '2026-03-05', 'lcDate': '2026-07-30', 'dlDate': '2026-11-30', 'year': '2026', 'blockCount': 84, 'totalWeight': 6050, 'topSupplier': '유일'}, 
    {'hno': '8277', 'dock': '2', 'sunpyoNo': '26M11', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'CMA CGM', 'klDate': '2026-05-15', 'lcDate': '2026-10-10', 'dlDate': '2027-02-28', 'year': '2026', 'blockCount': 82, 'totalWeight': 5900, 'topSupplier': '대아'}, 
    {'hno': '8276', 'dock': '2', 'sunpyoNo': '26M12', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'CMA CGM', 'klDate': '2026-07-20', 'lcDate': '2026-12-15', 'dlDate': '2027-04-30', 'year': '2026', 'blockCount': 82, 'totalWeight': 5895, 'topSupplier': '동남'}, 
    {'hno': '8254', 'dock': '1', 'sunpyoNo': '26M13', 'shipType': '157K COT', 'owner': 'DHT', 'klDate': '2026-02-15', 'lcDate': '2026-06-30', 'dlDate': '2026-10-31', 'year': '2026', 'blockCount': 34, 'totalWeight': 3650, 'topSupplier': '힘스2'}, 
    {'hno': '8255', 'dock': '1', 'sunpyoNo': '26M14', 'shipType': '157K COT', 'owner': 'DHT', 'klDate': '2026-04-10', 'lcDate': '2026-08-20', 'dlDate': '2026-12-15', 'year': '2026', 'blockCount': 33, 'totalWeight': 3550, 'topSupplier': '메이드'}, 
    {'hno': '8311', 'dock': '2', 'sunpyoNo': '26M38', 'shipType': '13000 CNTR(METH. DF)', 'owner': 'MAERSK', 'klDate': '2026-08-01', 'lcDate': '2026-12-20', 'dlDate': '2027-04-30', 'year': '2026', 'blockCount': 94, 'totalWeight': 6267, 'topSupplier': '유일'},

    {'hno': '8366', 'dock': '1', 'sunpyoNo': '27M01', 'shipType': '174K LNG', 'owner': 'QATAR ENERGY', 'klDate': '2027-01-10', 'lcDate': '2027-05-20', 'dlDate': '2027-09-30', 'year': '2027', 'blockCount': 73, 'totalWeight': 7450, 'topSupplier': '힘스2'}, 
    {'hno': '8334', 'dock': '1', 'sunpyoNo': '27M02', 'shipType': '174K LNG', 'owner': 'QATAR ENERGY', 'klDate': '2027-02-15', 'lcDate': '2027-06-30', 'dlDate': '2027-10-31', 'year': '2027', 'blockCount': 72, 'totalWeight': 7380, 'topSupplier': '메이드'}, 
    {'hno': '8335', 'dock': '1', 'sunpyoNo': '27M03', 'shipType': '174K LNG', 'owner': 'QATAR ENERGY', 'klDate': '2027-03-01', 'lcDate': '2027-07-10', 'dlDate': '2027-11-15', 'year': '2027', 'blockCount': 72, 'totalWeight': 7400, 'topSupplier': '힘스2'},
    {'hno': '8336', 'dock': '1', 'sunpyoNo': '27M04', 'shipType': '174K LNG', 'owner': 'QATAR ENERGY', 'klDate': '2027-04-01', 'lcDate': '2027-08-10', 'dlDate': '2027-12-15', 'year': '2027', 'blockCount': 72, 'totalWeight': 7400, 'topSupplier': '보원엠피1공장'},
    {'hno': '8337', 'dock': '1', 'sunpyoNo': '27M05', 'shipType': '174K LNG', 'owner': 'EXXONMOBIL', 'klDate': '2027-05-01', 'lcDate': '2027-09-10', 'dlDate': '2028-01-15', 'year': '2027', 'blockCount': 72, 'totalWeight': 7350, 'topSupplier': '힘스3'},
    {'hno': '8338', 'dock': '2', 'sunpyoNo': '27M11', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2027-01-15', 'lcDate': '2027-06-10', 'dlDate': '2027-10-20', 'year': '2027', 'blockCount': 104, 'totalWeight': 7850, 'topSupplier': '유일'}, 
    {'hno': '8339', 'dock': '2', 'sunpyoNo': '27M12', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2027-03-10', 'lcDate': '2027-07-25', 'dlDate': '2027-11-30', 'year': '2027', 'blockCount': 104, 'totalWeight': 7850, 'topSupplier': '대아'}, 
    {'hno': '8340', 'dock': '2', 'sunpyoNo': '27M13', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2027-04-15', 'lcDate': '2027-08-20', 'dlDate': '2027-12-28', 'year': '2027', 'blockCount': 104, 'totalWeight': 7850, 'topSupplier': '동남'},
    {'hno': '8341', 'dock': '2', 'sunpyoNo': '27M14', 'shipType': '16000 CNTR', 'owner': 'EVERGREEN', 'klDate': '2027-05-10', 'lcDate': '2027-09-15', 'dlDate': '2028-02-10', 'year': '2027', 'blockCount': 102, 'totalWeight': 7700, 'topSupplier': '알파'},
    {'hno': '8347', 'dock': '2', 'sunpyoNo': '27M15', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'CMA CGM', 'klDate': '2027-02-20', 'lcDate': '2027-07-15', 'dlDate': '2027-11-25', 'year': '2027', 'blockCount': 102, 'totalWeight': 7425, 'topSupplier': '유일'}, 
    {'hno': '8348', 'dock': '2', 'sunpyoNo': '27M16', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'CMA CGM', 'klDate': '2027-04-10', 'lcDate': '2027-09-01', 'dlDate': '2028-01-20', 'year': '2027', 'blockCount': 102, 'totalWeight': 7400, 'topSupplier': '대아'},
    {'hno': '8349', 'dock': '1', 'sunpyoNo': '27M17', 'shipType': '174K LNG', 'owner': 'SHELL', 'klDate': '2027-06-01', 'lcDate': '2027-10-15', 'dlDate': '2028-03-10', 'year': '2027', 'blockCount': 71, 'totalWeight': 7300, 'topSupplier': '메이드'},
    {'hno': '8350', 'dock': '1', 'sunpyoNo': '27M18', 'shipType': '174K LNG', 'owner': 'SHELL', 'klDate': '2027-07-01', 'lcDate': '2027-11-10', 'dlDate': '2028-04-15', 'year': '2027', 'blockCount': 71, 'totalWeight': 7300, 'topSupplier': '힘스2'},
    {'hno': '8351', 'dock': '2', 'sunpyoNo': '27M19', 'shipType': '16000 CNTR', 'owner': 'ONE', 'klDate': '2027-06-15', 'lcDate': '2027-10-20', 'dlDate': '2028-03-30', 'year': '2027', 'blockCount': 104, 'totalWeight': 7800, 'topSupplier': '유일'},
    {'hno': '8352', 'dock': '2', 'sunpyoNo': '27M20', 'shipType': '16000 CNTR', 'owner': 'ONE', 'klDate': '2027-07-15', 'lcDate': '2027-11-25', 'dlDate': '2028-05-10', 'year': '2027', 'blockCount': 104, 'totalWeight': 7800, 'topSupplier': '동남'},
    {'hno': '8371', 'dock': '2', 'sunpyoNo': '27M28', 'shipType': '13000 CNTR', 'owner': 'MAERSK', 'klDate': '2027-04-10', 'lcDate': '2027-08-30', 'dlDate': '2027-12-31', 'year': '2027', 'blockCount': 87, 'totalWeight': 6062, 'topSupplier': '유일'},
    {'hno': '8372', 'dock': '2', 'sunpyoNo': '27M29', 'shipType': '13000 CNTR', 'owner': 'MAERSK', 'klDate': '2027-05-20', 'lcDate': '2027-10-05', 'dlDate': '2028-02-25', 'year': '2027', 'blockCount': 87, 'totalWeight': 6050, 'topSupplier': '대아'},
    {'hno': '8373', 'dock': '1', 'sunpyoNo': '27M30', 'shipType': '174K LNG', 'owner': 'BP', 'klDate': '2027-08-10', 'lcDate': '2027-12-15', 'dlDate': '2028-06-10', 'year': '2027', 'blockCount': 71, 'totalWeight': 7300, 'topSupplier': '보원엠피1공장'},
    {'hno': '8374', 'dock': '1', 'sunpyoNo': '27M31', 'shipType': '174K LNG', 'owner': 'BP', 'klDate': '2027-09-01', 'lcDate': '2028-01-10', 'dlDate': '2028-07-05', 'year': '2027', 'blockCount': 71, 'totalWeight': 7300, 'topSupplier': '힘스3'},
    {'hno': '8375', 'dock': '2', 'sunpyoNo': '27M32', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'EPS', 'klDate': '2027-08-15', 'lcDate': '2028-01-05', 'dlDate': '2028-06-20', 'year': '2027', 'blockCount': 102, 'totalWeight': 7400, 'topSupplier': '알파'}
]

# ============================================================
# 1. APP STYLE (다크모드 대응 CSS)
# ============================================================
st.markdown("""
<style>
    .main .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    .app-title {font-size: 1.75rem; font-weight: 800; margin-bottom: 0.15rem;}
    .app-subtitle {color:#64748b; font-size:0.86rem; margin-bottom:1rem;}
    .kpi-card {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 16px; padding: 16px;
        background-color: var(--background-color, #ffffff);
        color: var(--text-color, #0f172a);
        min-height: 125px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .kpi-label {font-size: 0.76rem; color: #94a3b8; font-weight: 700;}
    .kpi-value {font-size: 1.55rem; font-weight: 800; margin-top: 8px;}
    .kpi-sub {font-size: 0.72rem; color: #94a3b8; margin-top: 7px;}
    .chat-panel {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 18px; 
        background-color: var(--secondary-background-color, #f8fbff);
        padding: 14px;
    }
    div[data-testid="stChatMessage"] {padding: 0.45rem 0;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. DATAFRAME + DERIVED RISK
# ============================================================
df_sup = pd.DataFrame(SUPPLIER_MASTER)
df_vessel = pd.DataFrame(VESSEL_DATASET)

def risk_score(row):
    ontime_penalty = max(0, 100 - float(row["ontimePct"])) * 2.0
    lead_penalty = max(0, float(row["avgLeadTime"]) - 20) * 0.65
    foreign_penalty = max(0, float(row["foreignPct"]) - 30) * 0.35
    skill_penalty = max(0, 75 - float(row["skilledPct"])) * 0.45
    return round(min(100, ontime_penalty + lead_penalty + foreign_penalty + skill_penalty), 1)

df_sup["risk_score"] = df_sup.apply(risk_score, axis=1)

# Source: 사외블록2026-2027(1).xlsx, 완료(계획)일 기준; missing supplier loads kept in annual totals.
ANNUAL_SUPPLIER_WEIGHT = {'2026': {'힘스2': 59308, '알파': 37456, '메이드': 33912, '태진': 27503, '보원엠피1공장': 27136, '힘스3': 27467, '동남': 28179, '유일': 14380, '대아': 23156, '장성테크': 3994, 'DHMC': 349, '트레스': 288, '칸플랜트': 364}, '2027': {'힘스2': 80584, '알파': 35382, '메이드': 35181, '태진': 28069, '보원엠피1공장': 21835, '힘스3': 20572, '동남': 31198, '유일': 21587, '대아': 25487, '장성테크': 4085, 'DHMC': 238, '트레스': 159, '칸플랜트': 0}}
UNASSIGNED_PLAN = {'2026': {'weight': 0, 'blocks': 0}, '2027': {'weight': 587, 'blocks': 32}}

def get_supplier_weight(row, year_filter):
    name = row["name"]
    year_filter = str(year_filter)
    if year_filter in ANNUAL_SUPPLIER_WEIGHT:
        return ANNUAL_SUPPLIER_WEIGHT[year_filter].get(name, 0)
    factor = 0.52 if year_filter == "2027" else 0.48 if year_filter == "2026" else 0.4
    return round(float(row["weight"]) * factor)

def find_supplier(text):
    for name in sorted(df_sup["name"].tolist(), key=len, reverse=True):
        if name.lower() in text.lower():
            return name
    return None

def parse_weight(text, default=10000):
    nums = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", text)
    if not nums: return float(default)
    return float(nums[-1].replace(",", ""))

def item_fit_score(supplier_name, item):
    if not item: return 0
    return 100 if supplier_name in ITEM_GROUPS.get(item, list(df_sup["name"])) else 0

def annualized_capacity(row, months=12):
    return float(row["capaMonth"]) * months

def supplier_plan_for_year(year):
    """Use complete uploaded annual load, never a filtered dashboard subset."""
    year = str(year)
    if year in ("2026", "2027"):
        return {r["name"]: float(get_supplier_weight(r, year)) for _, r in df_sup.iterrows()}
    if year != "2028":
        raise ValueError(f"{year}년 업체별 배정 자료가 없습니다.")
    data = globals().get("custom_2028_df")
    if data is None or data.empty:
        raise ValueError("2028년 업체별 물량 엑셀을 먼저 업로드하세요.")
    name_col = "업체명" if "업체명" in data.columns else "topSupplier"
    weight_col = "중량" if "중량" in data.columns else "totalWeight"
    if name_col not in data or weight_col not in data:
        raise ValueError("업로드 자료에 업체명/중량 또는 topSupplier/totalWeight 열이 필요합니다.")
    data = data.copy()
    if "완료(계획)" in data:
        dates = pd.to_datetime(data["완료(계획)"], errors="coerce")
        if dates.isna().any():
            raise ValueError("완료(계획) 일정에 빈 값 또는 잘못된 날짜가 있습니다.")
        data = data.loc[dates.dt.year.eq(2028)].copy()
    elif "year" in data:
        data = data.loc[data["year"].astype(str).str.replace(r"\.0$", "", regex=True).eq("2028")].copy()
    else:
        raise ValueError("2028년 여부를 확인할 완료(계획) 또는 year 열이 필요합니다.")
    if data.empty:
        raise ValueError("업로드 자료에 2028년 완료 물량이 없습니다.")
    data[name_col] = data[name_col].astype("string").str.strip()
    weights = pd.to_numeric(data[weight_col], errors="coerce")
    if weights.isna().any() or (~np.isfinite(weights)).any() or weights.lt(0).any():
        raise ValueError("중량에 빈 값, 숫자가 아닌 값 또는 음수가 있습니다.")
    unknown = data.loc[~data[name_col].isin(df_sup["name"]), name_col].fillna("업체명 누락").unique()
    if len(unknown):
        raise ValueError("업체 마스터에 없는 이름을 확인하세요: " + ", ".join(map(str, unknown)))
    data[weight_col] = weights
    totals = data.groupby(name_col)[weight_col].sum().to_dict()
    return {name: float(totals.get(name, 0)) for name in df_sup["name"]}


def allocate_transfer(src, requested, item, year):
    if not item or item not in ITEM_GROUPS:
        raise ValueError("재배정할 품목을 선택하세요. 품목 미지정 상태에서는 적합 업체를 확정할 수 없습니다.")
    if not np.isfinite(requested) or requested <= 0:
        raise ValueError("재배정 물량은 0보다 큰 숫자여야 합니다.")
    plans = supplier_plan_for_year(year)
    if requested > plans.get(src, 0) + 1e-8:
        raise ValueError(f"{src}의 {year}년 기존 배정량 {plans.get(src, 0):,.0f}T를 초과합니다.")
    pool = df_sup[(df_sup["name"] != src) & df_sup["name"].isin(ITEM_GROUPS[item])].copy()
    pool = pool.sort_values(["ontimePct", "skilledPct", "risk_score", "name"], ascending=[False, False, True, True])
    rows = []; remaining = float(requested)
    for _, r in pool.iterrows():
        name = r["name"]
        cap = min(float(r["capaMonth"])*12, 21000 if name == "유일" else float("inf"))
        room = max(0.0, cap - plans[name])
        alloc = min(remaining, room)
        if alloc <= 1e-8:
            continue
        rows.append({"원업체": src, "품목": item, "대체업체": name,
                     "기존배정(T)": plans[name], "연간Capa(T)": cap, "잔여Capa(T)": room,
                     "재배정물량(T)": alloc, "배정후물량(T)": plans[name]+alloc,
                     "배정비율(%)": round(alloc/requested*100, 1),
                     "납기준수율(%)": r["ontimePct"], "숙련공비중(%)": r["skilledPct"],
                     "Risk Score": r["risk_score"]})
        remaining -= alloc
        if remaining <= 1e-8:
            break
    return pd.DataFrame(rows), max(0.0, remaining)

# ============================================================
# 3. SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🎛️ 통합 분석 조건")
    
    year_filter = st.selectbox(
        "분석 대상 연도",
        ["2028", "2027", "2026", "2025", "2024", "2023"],
        index=1,
        format_func=lambda x: {
            "2028": "2028년 (업로드 데이터 분석)",
            "2027": "2027년 (304,964T / 완료계획 기준)",
            "2026": "2026년 (283,492T / 완료계획 기준)",
            "2025": "2025년 실적 (26.02만T)",
            "2024": "2024년 실적 (22.98만T)",
            "2023": "2023년 실적 (22.47만T)",
        }.get(x, x),
    )

    ship_types = ["ALL"] + sorted(df_vessel["shipType"].unique().tolist())
    ship_type = st.selectbox("선종", ship_types, format_func=lambda x: "전체 선종" if x == "ALL" else x)

    vessel_candidates = df_vessel[df_vessel["year"] == year_filter] if year_filter in HISTORICAL_TOTALS else df_vessel
    vessel_options = ["ALL"] + vessel_candidates["hno"].astype(str).tolist() if not vessel_candidates.empty else ["ALL"]
    vessel_no = st.selectbox("호선", vessel_options, format_func=lambda x: "전체 호선" if x == "ALL" else x)

    supplier_options = ["ALL"] + df_sup["name"].tolist()
    supplier_filter = st.selectbox("협력사", supplier_options, format_func=lambda x: "전체 13개 협력사" if x == "ALL" else x)

    st.divider()
    st.markdown("### 📂 2028년 물량 엑셀 업로드")
    uploaded_2028 = st.file_uploader("2028년 사외업체 물량/선표 파일 (xlsx, csv)", type=["xlsx", "csv"])
    
    custom_2028_df = None
    if uploaded_2028 is not None:
        try:
            if uploaded_2028.name.endswith('.csv'):
                custom_2028_df = pd.read_csv(uploaded_2028)
            else:
                custom_2028_df = pd.read_excel(uploaded_2028)
            st.success(f"📊 2028년 데이터 로드 성공: {len(custom_2028_df)}행")
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")

# 데이터 필터링
if year_filter == "2028" and custom_2028_df is not None:
    fv = custom_2028_df.copy()
    total_weight = int(fv["totalWeight"].sum()) if "totalWeight" in fv.columns else 320000
    total_blocks = int(fv["blockCount"].sum()) if "blockCount" in fv.columns else 3100
    vessel_count = len(fv)
else:
    fv = df_vessel.copy()
    if year_filter in HISTORICAL_TOTALS:
        fv = fv[fv["year"] == year_filter]
    if ship_type != "ALL": fv = fv[fv["shipType"] == ship_type]
    if vessel_no != "ALL": fv = fv[fv["hno"] == vessel_no]
    if supplier_filter != "ALL": fv = fv[fv["topSupplier"] == supplier_filter]

    if ship_type == "ALL" and vessel_no == "ALL" and supplier_filter == "ALL" and year_filter in HISTORICAL_TOTALS:
        base = HISTORICAL_TOTALS[year_filter]
        total_weight = base["weight"]
        total_blocks = base["blocks"]
    else:
        total_weight = int(fv["totalWeight"].sum()) if not fv.empty else 0
        total_blocks = int(fv["blockCount"].sum()) if not fv.empty else 0
    vessel_count = len(fv)

monthly_weight = round(total_weight / 12)
avg_block = round(total_weight / total_blocks, 1) if total_blocks else 0

st.markdown('<div class="app-title">🚢 B-SIGHT | 사외블록 통합 예측 · 생산 · 인력 · 업체배정 의사결정 플랫폼</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">AI 시뮬레이터 및 자동 재배정 엔진 복원 · 질문 의도 분석 챗봇 통합 버전</div>', unsafe_allow_html=True)

# KPI cards: the vessel dataset is only a sample, so omit its count.
k1, k2 = st.columns(2)
with k1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">선택 조건 총 물량</div><div class="kpi-value">{total_weight:,.0f} T</div><div class="kpi-sub">월평균 {monthly_weight:,.0f} T</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">총 사외블록</div><div class="kpi-value">{total_blocks:,.0f} EA</div><div class="kpi-sub">개당 평균 {avg_block:,.1f} T</div></div>', unsafe_allow_html=True)

# ============================================================
# 4. MAIN / CHAT SPLIT
# ============================================================
dash_col, chat_col = st.columns([7.2, 2.8], gap="large")

with dash_col:
    tabs = st.tabs([
        "📊 종합 물량", "👥 인력 & 관리", "📅 선표 & 공정", 
        "🚢 선종 & 척수", "🏭 Capa & 배정규칙", "⚡ AI 시뮬레이터", "🔄 물량 자동 재배정"
    ])

    with tabs[0]:
        c1, c2 = st.columns([1.55, 1])
        with c1:
            trend_df = pd.DataFrame({
                "연도": ["2023", "2024", "2025", "2026", "2027", "2028(예상)"],
                "사외블록 중량(T)": [224734, 229822, 260201, HISTORICAL_TOTALS["2026"]["weight"], HISTORICAL_TOTALS["2027"]["weight"], 320000],
                "블록수(EA)": [2350, 2400, 2650, HISTORICAL_TOTALS["2026"]["blocks"], HISTORICAL_TOTALS["2027"]["blocks"], 3100],
            })
            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend_df["연도"], y=trend_df["사외블록 중량(T)"], name="중량(T)"))
            fig.add_trace(go.Scatter(x=trend_df["연도"], y=trend_df["블록수(EA)"], name="블록수(EA)", yaxis="y2", mode="lines+markers"))
            fig.update_layout(title="연도별 사외블록 중량 및 블록수 추이", yaxis=dict(title="T"), yaxis2=dict(title="EA", overlaying="y", side="right"), height=360, margin=dict(l=10,r=10,t=55,b=10), legend=dict(orientation="h"))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            if not fv.empty and "shipType" in fv.columns:
                ship_stats = fv.groupby("shipType", as_index=False)["totalWeight"].sum()
                fig2 = px.pie(ship_stats, names="shipType", values="totalWeight", hole=.62, title="선종별 사외블록 중량 점유율")
                fig2.update_layout(height=360, margin=dict(l=10,r=10,t=55,b=10))
                st.plotly_chart(fig2, use_container_width=True)

        # Monthly plan, displayed in the marked area beneath annual charts.
        if year_filter in MONTHLY_PIVOT:
            month_plan = MONTHLY_PIVOT[year_filter]
            monthly_df = pd.DataFrame({"월": [f"{m}월" for m in range(1, 13)], "물량(T)": month_plan})
            fig_month = px.bar(monthly_df, x="월", y="물량(T)", text="물량(T)",
                               title=f"{year_filter}년 월별 사외제작 물량")
            fig_month.update_traces(marker_color="#0875d1", texttemplate="%{text:,.0f}", textposition="outside")
            fig_month.update_layout(height=360, margin=dict(l=10, r=10, t=55, b=10),
                                    xaxis_title="월", yaxis_title="물량(T)")
            st.plotly_chart(fig_month, use_container_width=True)
            if ship_type != "ALL" or vessel_no != "ALL" or supplier_filter != "ALL":
                st.caption("월별 그래프는 전체 사외제작 계획입니다. 선택한 선종·호선·협력사 필터의 월별 배분 자료는 없습니다.")
        else:
            st.info(f"{year_filter}년 월별 사외제작 계획 데이터가 없어 월별 그래프를 표시하지 않습니다.")

        dyn = df_sup.copy()
        dyn["배정중량(T)"] = dyn.apply(lambda r: get_supplier_weight(r, year_filter), axis=1)
        view = dyn[["name","배정중량(T)","avgLeadTime","ontimePct","topItem"]].copy()
        view.columns = ["협력사","배정중량(T)","Lead Time(일)","납기준수율(%)","주요품목"]
        st.dataframe(view.sort_values("배정중량(T)", ascending=False), use_container_width=True, hide_index=True)
        if year_filter in UNASSIGNED_PLAN and UNASSIGNED_PLAN[year_filter]["blocks"]:
            missing = UNASSIGNED_PLAN[year_filter]
            st.info(f"업체명 미입력 {missing['blocks']:,}개 / {missing['weight']:,.0f}T는 연간·월별 총량에 포함되지만 업체별 배정량에는 포함되지 않습니다.")


    with tabs[1]:
        st.dataframe(df_sup[["name","totalManpower","foreignPct","skilledPct","risk_score","topItem"]], use_container_width=True, hide_index=True)
    with tabs[2]:
        if custom_2028_df is not None and year_filter == "2028":
            st.dataframe(custom_2028_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(fv[["dock","sunpyoNo","hno","shipType","owner","klDate","dlDate","totalWeight"]], use_container_width=True, hide_index=True)
    with tabs[3]:
        st.dataframe(fv, use_container_width=True, hide_index=True)
    with tabs[4]:
        cap = df_sup.copy()
        cap["1년 Capa"] = cap["capaMonth"] * 12
        cap["기존배정(1년)"] = cap.apply(lambda r: get_supplier_weight(r, year_filter), axis=1)
        cap["환산부하율(%)"] = (cap["기존배정(1년)"] / cap["1년 Capa"] * 100).round(1)
        st.dataframe(cap[["name","capaMonth","기존배정(1년)","1년 Capa","환산부하율(%)","topItem"]].sort_values("환산부하율(%)", ascending=False), use_container_width=True, hide_index=True)
    
    # ---------------- AI Simulator (문법 오류 수정 완료) ----------------
    with tabs[5]:
        st.markdown("#### 선종 · 척수별 BOM & 자동 배정 시뮬레이터")
        sim_ship = st.selectbox("선종 선택", list(SHIP_MODELS.keys()), key="sim_ship")
        sc1, sc2 = st.columns(2)
        with sc1:
            sim_count = st.number_input("투입 척수", 1, 20, 2, key="sim_count")
        with sc2:
            sim_wpv = st.number_input("척당 사외블록 중량(T)", 1000, 30000, 7800, 100, key="sim_wpv")

        total_sim = sim_count * sim_wpv
        bom_rows = []
        for b in SHIP_MODELS[sim_ship]["bom"]:
            w = total_sim * b["ratio"]
            ea = round(w / b["avgUnitWeight"])
            suppliers = [b.get("supplier1"), b.get("supplier2"), b.get("supplier3")]
            suppliers = [x for x in suppliers if x]
            bom_rows.append({
                "품목": b["item"], "비중(%)": b["ratio"]*100,
                "산출중량(T)": round(w), "수량(EA)": ea,
                "1순위 협력사": suppliers[0] if suppliers else "-"
            })
        bom_df = pd.DataFrame(bom_rows)
        st.dataframe(bom_df, use_container_width=True, hide_index=True)

        sim_load = []
        for _, r in df_sup.iterrows():
            existing_monthly = get_supplier_weight(r, year_filter) / 12
            add = 0
            for b in SHIP_MODELS[sim_ship]["bom"]:
                if r["name"] in [b.get("supplier1"), b.get("supplier2"), b.get("supplier3")]:
                    add += total_sim * b["ratio"] / 12
                    break
            new_load = existing_monthly + add
            sim_load.append({
                "협력사": r["name"], "기존 월평균(T)": round(existing_monthly),
                "신규 월평균(T)": round(new_load),
                "월 Capa(T)": r["capaMonth"],
                "예상부하율(%)": round(new_load / r["capaMonth"] * 100, 1)
            })
        sim_load_df = pd.DataFrame(sim_load).sort_values("예상부하율(%)", ascending=False)
        st.dataframe(sim_load_df, use_container_width=True, hide_index=True)

    # ---------------- Auto Reallocation ----------------
    with tabs[6]:
        st.markdown("#### 🔄 업체 간 물량 자동 재배정")
        st.caption("품목 적합 업체에 연간 잔여 Capa 범위 내에서만 재배정합니다. 수용하지 못하는 물량은 배정 불가로 표시합니다.")
        r1, r2, r3 = st.columns(3)
        with r1:
            src = st.selectbox("원업체", df_sup["name"].tolist(), key="re_src")
        with r2:
            re_weight = st.number_input("재배정 물량(T)", 100, 100000, 10000, 100, key="re_weight")
        with r3:
            re_item = st.selectbox("품목", ["품목 선택 필요"] + list(ITEM_GROUPS.keys()), key="re_item")
        st.caption("2028년은 업로드 자료의 업체별 전체 배정량을 사용합니다. 연간 Capa=월 Capa×12, 유일은 최대 21,000T입니다. 월별 일정과 품목별 원업체 보유량은 별도 확인이 필요합니다.")
        if st.button("자동 재배정 계산", type="primary", use_container_width=True):
            try:
                result, remaining = allocate_transfer(src, float(re_weight), re_item if re_item in ITEM_GROUPS else None, year_filter)
                assigned = float(re_weight) - remaining
                if remaining > 1e-8:
                    st.warning(f"요청 {re_weight:,.0f}T 중 배정 가능 {assigned:,.0f}T / 배정 불가 {remaining:,.0f}T: 품목 적합 업체의 연간 잔여 Capa 부족")
                else:
                    st.success(f"{assigned:,.0f}T 전량 배정 가능: 연간 Capa 이내 잠정 시나리오")
                if not result.empty:
                    st.dataframe(result, use_container_width=True, hide_index=True)
                else:
                    st.info("배정 가능한 품목 적합 업체의 연간 여유가 없습니다.")
                st.caption("계산 결과는 시나리오이며 기존 배정 데이터를 변경하지 않습니다. 초과 업체를 포함한 전체 기존 부하는 아래 표에서 확인하세요.")
                plans = supplier_plan_for_year(year_filter)
                loads = []
                for _, row in df_sup.iterrows():
                    name = row["name"]
                    cap = min(float(row["capaMonth"])*12, 21000 if name == "유일" else float("inf"))
                    loads.append({"업체": name, "기존배정(T)": plans[name], "연간Capa(T)": cap, "잔여Capa(T)": max(0,cap-plans[name]), "기존초과(T)": max(0,plans[name]-cap)})
                st.dataframe(pd.DataFrame(loads), use_container_width=True, hide_index=True)
            except ValueError as exc:
                st.error(str(exc))

# ============================================================
# 5. CHATBOT PANEL (질문 분석 및 응답 강화)
# ============================================================
with chat_col:
    st.markdown('<div class="chat-panel">', unsafe_allow_html=True)
    st.markdown("### 🤖 B-SIGHT 지능형 음성 챗봇")
    st.caption("질문 의도 분석, 음성 인식 및 자동 재배정 연동")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [{
            "role":"assistant",
            "content":"안녕하세요! 현장 데이터 분석이나 물량 재배정에 대해 질문해 주세요. (예: '힘스2 물량 1만 톤 납기 우선으로 재배정해줘')"
        }]

    # Browser speech recognition: no OpenAI audio API or extra pip package.
    import tempfile
    from pathlib import Path
    import streamlit.components.v1 as components

    @st.cache_resource
    def _browser_voice_component():
        component_dir = Path(tempfile.mkdtemp(prefix="bsight_voice_"))
        (component_dir / "index.html").write_text(_VOICE_HTML, encoding="utf-8")
        return components.declare_component("bsight_browser_voice_v1", path=str(component_dir))

    _VOICE_HTML = r"""<!doctype html><html lang="ko"><meta charset="utf-8">
    <style>body{font:14px sans-serif;margin:4px;color:#475569}button{padding:9px 12px;border:1px solid #cbd5e1;border-radius:8px;cursor:pointer;margin-right:6px}textarea{box-sizing:border-box;width:100%;margin-top:8px;padding:8px;border:1px solid #cbd5e1;border-radius:6px}#status{margin:8px 0;min-height:20px}</style>
    <button id="start">🎙️ 음성 인식 시작</button><button id="stop" disabled>중지</button>
    <div id="status" role="status">시작 버튼을 누르고 마이크 사용을 허용하세요.</div>
    <textarea id="text" rows="2" placeholder="인식 결과를 확인하고 수정할 수 있습니다."></textarea>
    <button id="apply">질문 입력란에 반영</button>
    <script>
    const send=(type,extra={})=>window.parent.postMessage({isStreamlitMessage:true,type,...extra},"*");
    send("streamlit:componentReady",{apiVersion:1});send("streamlit:setFrameHeight",{height:210});
    const start=document.getElementById('start'), stop=document.getElementById('stop'),
    status=document.getElementById('status'), field=document.getElementById('text');
    const API=window.SpeechRecognition||window.webkitSpeechRecognition;
    let recognition, finalText='', active=false;
    if(!API){start.disabled=true;status.textContent='이 브라우저는 음성 인식을 지원하지 않습니다. Chrome에서 열거나 직접 질문을 입력하세요.';}
    else {
      recognition=new API();recognition.lang='ko-KR';recognition.continuous=false;recognition.interimResults=true;
      recognition.onstart=()=>{active=true;start.disabled=true;stop.disabled=false;status.textContent='듣고 있습니다. 말씀하신 뒤 중지를 누르세요.';};
      recognition.onresult=e=>{let interim='';for(let i=e.resultIndex;i<e.results.length;i++){if(e.results[i].isFinal)finalText+=e.results[i][0].transcript+' ';else interim+=e.results[i][0].transcript;}field.value=(finalText+interim).trim();};
      recognition.onerror=e=>{const messages={'not-allowed':'마이크 권한이 차단되었습니다. 주소창의 사이트 권한에서 마이크를 허용하고 다시 시도하세요.','service-not-allowed':'브라우저 또는 회사 보안 정책이 음성 인식 서비스를 차단했습니다.','audio-capture':'마이크를 찾지 못했습니다. 연결 및 다른 앱의 마이크 사용을 확인하세요.','network':'음성 인식 서비스 연결에 실패했습니다. 네트워크를 확인하세요.','no-speech':'음성을 감지하지 못했습니다. 다시 시도하세요.','aborted':'음성 인식을 중지했습니다.'};status.textContent=messages[e.error]||('음성 인식 오류: '+e.error);};
      recognition.onend=()=>{active=false;start.disabled=false;stop.disabled=true;if(field.value.trim())status.textContent='인식 결과를 확인한 뒤 질문 입력란에 반영하세요.';};
      start.onclick=()=>{if(active)return;finalText='';field.value='';try{recognition.start();}catch(e){status.textContent='시작하지 못했습니다. 잠시 후 다시 시도하세요.';}};
      stop.onclick=()=>recognition.stop();
    }
    document.getElementById('apply').onclick=()=>{const text=field.value.trim();if(!text){status.textContent='먼저 음성을 인식하거나 내용을 입력하세요.';return;}send('streamlit:setComponentValue',{value:{text,event_id:Date.now()+':'+Math.random()},dataType:'json'});status.textContent='질문 입력란에 반영했습니다.';};
    </script></html>"""

    st.markdown("#### 🎙️ 음성 질문 (브라우저 음성 인식)")
    st.caption("OpenAI 키 없이 사용합니다. Chrome 권장 · 마이크 권한 필요 · 인식 후 질문 전송을 눌러주세요.")
    voice_event = _browser_voice_component()(key="browser_voice", default=None)
    if isinstance(voice_event, dict) and voice_event.get("event_id") != st.session_state.get("last_voice_event"):
        st.session_state.last_voice_event = voice_event.get("event_id")
        st.session_state.voice_question_text = voice_event.get("text", "")

    # A form prevents accidental resubmission on unrelated dashboard reruns.
    with st.form("voice_question_form", clear_on_submit=True):
        user_input_text = st.text_input(
            "음성 인식 결과 / 질문 입력",
            key="voice_question_text",
            placeholder="예: 힘스2 물량 1만 톤 빼서 가장 적합한 업체에 나눠줘",
        )
        voice_question_submitted = st.form_submit_button("질문 전송")

    examples = [
        "협력사 비교해줘",
        "보원엠피 납기 위험이 얼마나 돼?",
        "2027년 피크 대응 전략은?",
        "힘스2 물량 10,000T를 납기 우선으로 재배정해줘",
    ]
    st.markdown("**빠른 질문**")
    for q in examples:
        if st.button(q, key="q_"+q, use_container_width=True):
            st.session_state.pending_prompt = q

    for m in st.session_state.chat_messages[-8:]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("예: 힘스2 물량 10,000T를 납기 우선으로 재배정해줘")
    if "pending_prompt" in st.session_state:
        prompt = st.session_state.pop("pending_prompt")
    if voice_question_submitted and user_input_text.strip():
        prompt = user_input_text.strip()

    def generate_response(prompt_text):
        """Route natural Korean questions to evidence-backed dashboard answers."""
        p = prompt_text.strip()
        q = re.sub(r"\s+", "", p.lower())
        if not p:
            return "질문을 입력해 주세요."

        # The question's explicit year takes precedence over the sidebar.
        year = next((y for y in ("2028", "2027", "2026", "2025", "2024", "2023") if y in p), year_filter)
        names = [n for n in sorted(df_sup["name"], key=len, reverse=True) if n.lower() in q]
        aliases = {"보원엠피": "보원엠피1공장", "보원": "보원엠피1공장", "힘스 2": "힘스2", "힘스 3": "힘스3"}
        if not names:
            names = [v for k, v in aliases.items() if re.sub(r"\s+", "", k.lower()) in q]
        names = list(dict.fromkeys(names))
        src = names[0] if names else None
        item = next((x for x in sorted(ITEM_GROUPS, key=len, reverse=True)
                     if re.sub(r"\s+", "", x.lower()) in q), None)
        if item == "T-BHD" and any(x in q for x in ("cntr", "컨테이너", "container")):
            item = "CNTR T-BHD"
        transfer = any(x in q for x in ("재배정", "옮겨", "옮기", "나눠", "빼서", "이관", "물량전환"))
        risk = any(x in q for x in ("위험", "리스크", "risk", "지연", "차질", "취약"))
        delivery = any(x in q for x in ("납기", "리드타임", "leadtime"))
        people = any(x in q for x in ("인력", "외국인", "숙련", "이탈", "작업자"))
        compare = any(x in q for x in ("비교", "순위", "top", "어느업체", "가장", "업체별"))
        peak = any(x in q for x in ("피크", "peak", "성수기", "최고월", "최대월"))
        amount = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*(만)?\s*(?:t|톤)", p, re.I)
        wt = float(amount.group(1).replace(",", "")) * (10000 if amount and amount.group(2) else 1) if amount else None
        vessel = next((v for v in df_vessel["hno"].astype(str).unique() if re.search(rf"(?<!\d){re.escape(v)}(?:호선)?(?!\d)", p)), None)

        # New volume has no origin supplier. Identify item family and allocate
        # only within qualified suppliers and annual remaining capacity.
        new_volume = wt is not None and any(x in q for x in ("추가", "신규", "증가", "늘어", "더배정", "더필요"))
        if new_volume and not transfer:
            if year not in ("2026", "2027"):
                return f"{year}년 협력사별 확정 배정 계획이 없어 추가 물량의 잔여 Capa를 계산할 수 없습니다."
            # CNTR describes a vessel family, not a particular block item.
            cntr = any(x in q for x in ("cntr", "컨테이너", "container"))
            if cntr and not item:
                models = [m for m in SHIP_MODELS if "CNTR" in m]
                selected = next((m for m in models if re.sub(r"\s+", "", m.lower()) in q), None)
                if not selected:
                    selected = "16000 CNTR"  # labeled example when the vessel class is unspecified
                bom = SHIP_MODELS[selected]["bom"]
                requests = [(b["item"].split(" (")[0], wt*b["ratio"]) for b in bom]
            elif item:
                requests = [(item, wt)]
            else:
                return "추가 배정할 **선종 또는 블록 품목**을 알려주세요. 예: ‘2027년 CNTR T-BHD 10,000T 추가’."
            remaining_by_name = {}
            for _, r in df_sup.iterrows():
                planned = get_supplier_weight(r, year)
                capacity = min(float(r["capaMonth"])*12, 21000 if r["name"] == "유일" else float("inf"))
                remaining_by_name[r["name"]] = max(0, capacity-planned)
            lines = [f"### 🧭 {year}년 추가 물량 {wt:,.0f}T 배정 검토",
                     f"- 대상: **{selected if cntr and not item else item}** · 연간 잔여 Capa 기준 잠정안", ""]
            if cntr and not item and not any(re.sub(r"\s+", "", m.lower()) in q for m in SHIP_MODELS if "CNTR" in m):
                lines.append("- 선형 미지정: **16000 CNTR의 BOM 비중을 예시로 가정**했습니다. 다른 선형이면 품목별 물량이 달라집니다.\n")
            for req_item, req_wt in requests:
                compatible = ITEM_GROUPS.get(req_item, [])
                if req_item.startswith("CNTR T-BHD"):
                    compatible = ["유일", "대아", "동남"]
                candidates = sorted((df_sup[df_sup["name"] == n].iloc[0] for n in compatible),
                                    key=lambda r: (({"유일": 0, "대아": 1, "동남": 2}.get(r["name"], 3))
                                                   if req_item.startswith("CNTR T-BHD") else 0,
                                                   -r["ontimePct"], r["risk_score"]))
                pending = req_wt
                assignments = []
                if req_item.startswith("CNTR T-BHD"):
                    # Yuil first; overflow to Daea/Dongnam at the 55/45 target,
                    # with any unfilled target redistributed if spare capacity exists.
                    yuil_take = min(pending, remaining_by_name["유일"])
                    if yuil_take > 0:
                        assignments.append(f"유일 {yuil_take:,.0f}T")
                        remaining_by_name["유일"] -= yuil_take
                        pending -= yuil_take
                    overflow = pending
                    for name, share in (("대아", .55), ("동남", .45)):
                        allocated = min(overflow * share, remaining_by_name[name])
                        if allocated > 0:
                            assignments.append(f"{name} {allocated:,.0f}T")
                            remaining_by_name[name] -= allocated
                            pending -= allocated
                    for name in ("대아", "동남"):
                        allocated = min(pending, remaining_by_name[name])
                        if allocated > 0:
                            assignments.append(f"{name} 추가 {allocated:,.0f}T")
                            remaining_by_name[name] -= allocated
                            pending -= allocated
                    candidates = []
                for r in candidates:
                    room = remaining_by_name[r["name"]]
                    allocated = min(pending, room)
                    if allocated > 0:
                        assignments.append(f"{r['name']} {allocated:,.0f}T")
                        remaining_by_name[r["name"]] -= allocated
                        pending -= allocated
                    if pending <= 0.01:
                        break
                lines.append(f"- **{req_item} {req_wt:,.0f}T:** " + (" → ".join(assignments) if assignments else "배정 가능한 연간 여유 없음")
                             + (f" · **미배분 {pending:,.0f}T**" if pending > 0.01 else ""))
            lines.append("\n> 품목 적합성과 기존 연간 배정·Capa로 계산했습니다. 선종별 BOM 비중은 예시 모델이며 실제 호선의 도면 물량, 월별 가용 Capa, 설비·품질·계약 조건을 확인한 뒤 확정하세요.")
            return "\n".join(lines)

        # Intent order matters: an explicit action or year-specific plan wins
        # over a broad keyword such as an individual supplier or "위험".
        if transfer:
            if not src or wt is None:
                missing = "원업체와 이동 물량" if not src and wt is None else "원업체" if not src else "이동 물량(T)"
                return f"재배정 계산에 필요한 **{missing}**을 알려주세요. 예: ‘힘스2 E/ROOM 5,000T를 납기 우선으로 재배정해줘’. 임의의 업체나 물량을 가정하지 않습니다."
            origin = df_sup[df_sup["name"] == src].iloc[0]
            origin_weight = get_supplier_weight(origin, year)
            if year not in ("2026", "2027"):
                return f"{year}년의 협력사별 확정 배정량이 없어 재배정 여유량을 계산할 수 없습니다. 2026년 또는 2027년으로 질문해 주세요."
            if wt > origin_weight:
                return f"**{src}**의 {year}년 배정량은 {origin_weight:,.0f}T입니다. 요청한 {wt:,.0f}T가 이를 초과하므로 이동 물량을 다시 지정해 주세요."
            if not item:
                return (f"**{src}**의 어떤 품목을 재배정할지 알려주세요. 주력 품목은 **{origin['topItem']}**입니다. "
                        "품목별 적합 업체가 달라서 전체 물량을 임의의 업체에 배분할 수 없습니다.")
            allowed = ITEM_GROUPS.get(item, list(df_sup["name"]))
            if item == "CNTR T-BHD" or (item == "T-BHD" and ("cntr" in q or "컨테이너" in q)):
                allowed = ["유일", "대아", "동남"]
            pool = []
            for _, r in df_sup.iterrows():
                if r["name"] == src or r["name"] not in allowed:
                    continue
                current = get_supplier_weight(r, year)
                cap = min(float(r["capaMonth"]) * 12, 21000 if r["name"] == "유일" else float("inf"))
                remaining = max(0, cap - current)
                if remaining > 0:
                    pool.append((r, remaining))
            pool.sort(key=lambda pair: (pair[0]["ontimePct"], -pair[0]["risk_score"]), reverse=True)
            rest = wt
            lines = [f"### 🔄 {year}년 {src} 물량 재배정 검토", f"- 이동 요청: **{wt:,.0f}T** / 원업체 배정: **{origin_weight:,.0f}T**", f"- 품목: **{item or '미지정'}** · 후보: {'품목 적합 업체' if item else '전 업체(품목 적합성 미검증)'}", "", "**후보별 Capa 범위 내 잠정 배분**"]
            for r, room in pool:
                if rest <= 0:
                    break
                assigned = min(room, rest)
                lines.append(f"- **{r['name']}** {assigned:,.0f}T · 잔여 Capa {room:,.0f}T · 납기 {r['ontimePct']:.1f}% · 관리 위험 {r['risk_score']:.1f}")
                rest -= assigned
            if rest > 0:
                lines.append(f"- **미배분 {rest:,.0f}T**: 적합 업체의 연간 Capa가 부족합니다.")
            if not pool:
                lines.append("- 적합 후보의 연간 잔여 Capa가 없습니다.")
            lines.append("\n> 연간 Capa와 기존 배정량을 사용한 잠정안입니다. 월별 여유, 설비·품질·계약, 실제 공정 일정은 별도 확인해야 합니다.")
            return "\n".join(lines)

        if peak or (year == "2027" and any(x in q for x in ("대응", "전략", "생산계획"))):
            if year != "2027":
                return f"{year}년의 월별 생산계획은 이 코드에 없어 피크 월을 특정할 수 없습니다. 연간 총량은 {HISTORICAL_TOTALS[year]['weight']:,}T입니다." if year in HISTORICAL_TOTALS else "2028년 업로드 자료에 월별 생산 일정 열이 없으면 피크 월을 계산할 수 없습니다."
            top = df_sup.copy()
            top["plan"] = top.apply(lambda r: get_supplier_weight(r, "2027"), axis=1)
            top["util"] = top["plan"] / (top["capaMonth"] * 12) * 100
            critical = top.sort_values("util", ascending=False).head(3)
            lines = ["### 📈 2027년 피크 대응 전략", f"- 연간 계획 **{HISTORICAL_TOTALS['2027']['weight']:,}T**, 월평균 **{HISTORICAL_TOTALS['2027']['weight']/12:,.0f}T**", "- 기존 사업계획상 6월 피크 **32,791T**: 월평균 대비 **약 29.0%** 상회", "", "**우선 실행**", "1. 6월 투입분의 자재·설계 확정과 제작 착수를 1~2개월 앞당겨 주간 부하를 평준화합니다.", "2. 유일의 연간 21,000T 한도를 확인하고 CNTR T-BHD 초과분의 대아·동남 수용 능력을 예약합니다.", "3. 납기 위험 업체는 주간 공정률·인력 변동·자재 입고를 함께 점검합니다.", "", "**연간 Capa 활용률 상위 업체(참고)**"]
            lines += [f"- {r['name']}: {r['plan']:,.0f}T / {r['capaMonth']*12:,.0f}T = {r['util']:.1f}%" for _, r in critical.iterrows()]
            lines.append("\n> 6월 수치는 사업계획 기준입니다. 현재 코드에는 업체별 월별 배정·공정 데이터가 없어 6월 개별 업체의 초과 여부는 판정할 수 없습니다.")
            return "\n".join(lines)

        if vessel:
            rows = df_vessel[df_vessel["hno"].astype(str) == vessel]
            if not rows.empty:
                v = rows.iloc[0]
                return (f"### 🚢 {vessel}호선 선표\n- 선종 **{v['shipType']}** · {v['year']}년 · {v['dock']}도크\n"
                        f"- 사외블록 **{v['blockCount']:,}EA / {v['totalWeight']:,}T** · 1순위 협력사 **{v['topSupplier']}**\n"
                        f"- 착공 **{v['klDate']}** · 인도 **{v['dlDate']}**\n\n> 1순위 협력사는 전체 블록의 확정 배정처를 뜻하지 않습니다.")

        if src and not compare:
            r = df_sup[df_sup["name"] == src].iloc[0]
            weight = get_supplier_weight(r, year) if year in ("2026", "2027") else None
            lines = [f"### 🏭 {src} 협력사 분석", f"- 평균 Lead Time **{r['avgLeadTime']:.1f}일** · 납기준수율 **{r['ontimePct']:.1f}%**", f"- 관리 위험 점수 **{r['risk_score']:.1f}/100** · 월 Capa **{r['capaMonth']:,.0f}T**", f"- 인력 **{r['totalManpower']}명** · 외국인 **{r['foreignPct']}%** · 숙련공 **{r['skilledPct']}%**", f"- 주요 품목 **{r['topItem']}**"]
            if weight is not None:
                lines.append(f"- {year}년 배정 **{weight:,.0f}T** · 연간 Capa 활용률 **{weight/(r['capaMonth']*12)*100:.1f}%**")
            if risk or delivery:
                lines += ["", "**납기 위험 판단**", f"- 과거 납기 미준수 비율 **{100-r['ontimePct']:.1f}%**, 평균 제작기간 **{r['avgLeadTime']:.1f}일**."]
                if r["ontimePct"] < 96 or r["avgLeadTime"] >= 35:
                    lines.append("- **우선 점검:** 납기준수율 또는 제작기간 지표가 취약합니다. 자재 투입, 주간 진도, 설비 가동률을 확인하세요.")
                else:
                    lines.append("- 현재 집계 지표만으로 즉각적인 지연을 단정하기 어렵습니다. 월별 부하와 진행률을 확인하세요.")
            lines += ["", "**현장 관리 포인트**"] + [f"- {x}" for x in r["mgmtPoints"]]
            lines.append("\n> 위험 점수는 기존 대시보드의 관리 지표이며 실제 납기 지연 확률이 아닙니다.")
            return "\n".join(lines)

        if compare:
            d = df_sup.copy()
            if item:
                d = d[d["name"].isin(ITEM_GROUPS[item])]
            if people:
                d = d.sort_values(["foreignPct", "skilledPct"], ascending=[False, True])
                measure = "외국인 비중 높은 순"
            elif risk or delivery:
                d = d.sort_values(["ontimePct", "risk_score"], ascending=[True, False])
                measure = "납기준수율 낮은 순"
            else:
                d = d.sort_values(["ontimePct", "risk_score"], ascending=[False, True])
                measure = "납기준수율 높은 순"
            lines = [f"### 📊 협력사 비교 — {measure}"]
            for _, r in d.head(7).iterrows():
                lines.append(f"- **{r['name']}**: 납기 {r['ontimePct']:.1f}% · Lead Time {r['avgLeadTime']:.1f}일 · 외국인 {r['foreignPct']}% · 위험 {r['risk_score']:.1f}")
            return "\n".join(lines)

        if people or risk or delivery:
            d = df_sup.sort_values(["ontimePct", "risk_score"], ascending=[True, False]) if (risk or delivery) else df_sup.sort_values(["foreignPct", "skilledPct"], ascending=[False, True])
            lines = ["### 🚦 납기 관리 우선 점검 업체" if (risk or delivery) else "### 👥 외국인 인력 비중 상위 업체"]
            for _, r in d.head(5).iterrows():
                lines.append(f"- **{r['name']}**: 납기 {r['ontimePct']:.1f}% · Lead Time {r['avgLeadTime']:.1f}일 · 외국인 {r['foreignPct']}% · 숙련공 {r['skilledPct']}%")
            lines.append("\n> 협력사별 현재 이탈률·월별 진행률은 이 데이터에 없습니다.")
            return "\n".join(lines)

        if "유일" in q or "격벽" in q or "t-bhd" in q or "cap" in q or "캐파" in q:
            return "### 🧱 CNTR T-BHD 배정 제약\n- 유일 우선 배정, **연간 최대 21,000T**\n- 유일 초과분은 **대아·동남**에 배분 검토\n- 실제 배정에는 양사의 월별 Capa, 설비와 품질 요건을 확인하세요."

        if year in HISTORICAL_TOTALS and any(x in q for x in ("물량", "총량", "몇척", "생산", "현황", "블록")):
            h = HISTORICAL_TOTALS[year]
            return f"### 📦 {year}년 사외블록 계획\n- 총 **{h['weight']:,}T / {h['blocks']:,}블록**\n- 선택된 화면 필터 기준은 **{total_weight:,}T / {total_blocks:,}블록**입니다."
        if client:
            context = {
                "selected_year": year, "selected_filters": {"ship_type": ship_type, "vessel": vessel_no, "supplier": supplier_filter},
                "annual_totals": HISTORICAL_TOTALS, "monthly_plans": MONTHLY_PIVOT,
                "supplier_profiles": df_sup[["name", "capaMonth", "ontimePct", "avgLeadTime", "foreignPct", "skilledPct", "risk_score", "topItem"]].to_dict("records"),
                "supplier_2027_weight": WEIGHT_2027, "item_suppliers": ITEM_GROUPS,
                "vessel_records": df_vessel.to_dict("records"),
            }
            try:
                response = client.responses.create(
                    model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
                    instructions=("당신은 B-SIGHT 사외블록 생산 의사결정 조력자입니다. 한국어로 질문에 직접 답하세요. "
                                  "제공된 JSON의 숫자와 규칙만 확정 사실로 사용하세요. 없는 월별 업체 배정, 실시간 진도, "
                                  "선종별 정확한 배정량, 2028 확정 계획을 지어내지 마세요. "
                                  "추론과 가정은 명시하고 계산 과정과 검증할 조건을 짧게 설명하세요. "
                                  "21,000T 유일 연간 한도 및 품목 적합성을 지키세요. "
                                  "업무 범위를 벗어난 질문에는 관련 정보를 제공할 수 없다고 말하세요."),
                    input=f"질문: {p}\n\nB-SIGHT 데이터(JSON): {json.dumps(context, ensure_ascii=False, default=str)}",
                )
                if response.output_text:
                    return response.output_text
            except Exception as exc:
                return f"AI 확장 답변을 가져오지 못했습니다: {type(exc).__name__}. 아래 기본 데이터 질문으로 다시 시도해 주세요."
        return ("### 📊 B-SIGHT 데이터 안내\n"
                "협력사 13곳의 납기·인력·Capa, 2026~27년 선표와 BOM을 기반으로 질문할 수 있습니다. "
                "예: ‘보원엠피 납기 위험’, ‘2027년 피크 대응’, ‘유일 Cap’, ‘힘스2 E/ROOM 5,000T 재배정’. "
                "질문 대상이나 기간이 데이터에 없으면 그 한계를 명시합니다.")

    if prompt:
        st.session_state.chat_messages.append({"role":"user","content":prompt})
        answer = generate_response(prompt)
        st.session_state.chat_messages.append({"role":"assistant","content":answer})
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("B-SIGHT 통합 플랫폼 · 문법 오류 수정 완료 및 AI 시뮬레이터·자동 재배정 탭 정상 복원.")
