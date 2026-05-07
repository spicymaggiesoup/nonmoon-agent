import os
import requests
import json
import time
import google.generativeai as genai
import arxiv

# GitHub Secrets에서 환경변수 가져오기
REST_API_KEY = os.environ.get('KAKAO_REST_API_KEY')
REFRESH_TOKEN = os.environ.get('KAKAO_REFRESH_TOKEN')

# Gemini 설정
# for m in genai.list_models():
#     if 'generateContent' in m.supported_generation_methods:
#         print(m.name)

genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
#model = genai.GenerativeModel('models/gemini-1.5-flash')
#model = genai.GenerativeModel(model_name="gemini-1.5-flash")
# 모델명을 명시적으로 지정 (경로 포함)
try:
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
except Exception:
    # 혹시라도 위 형식이 안 될 경우를 대비한 예외 처리
    model = genai.GenerativeModel('models/gemini-2.0-flash-lite')

def fetch_recent_papers():
    search_query = '(abs:"medical" OR abs:"multimodal") AND (abs:"NLP" OR abs:"time-series")'
    
    # 서버 에러 시 최대 3번까지 다시 시도
    for attempt in range(3):
        try:
            search = arxiv.Search(
                query=search_query,
                max_results=5,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            paper_data = []
            # deprecated -- results()를 리스트로 변환하여 에러 발생 여부를 즉시 확인
            # results = list(search.results())
            # 최신 라이브러리 방식
            client = arxiv.Client()
            results = list(client.results(search))
            
            for result in results:
                paper_info = {
                    "title": result.title,
                    "summary": result.summary[:400],
                    "url": result.pdf_url
                }
                paper_data.append(paper_info)
            
            return paper_data

        except Exception as e:
            print(f"⚠️ {attempt + 1}회차 시도 실패: {e}")
            if attempt < 2:
                time.sleep(5) # 5초 대기 후 다시 시도
            else:
                print("❌ arXiv 서버 응답 지연으로 논문을 가져올 수 없습니다.")
                return []

def fetch_recent_papers_org():
    """
    arXiv에서 의료, 멀티모달, NLP, 시계열 키워드로 최신 논문을 수집합니다.
    """
    # 사용자님의 관심 키워드 조합
    search_query = '(abs:"medical" OR abs:"multimodal") AND (abs:"NLP" OR abs:"time-series")'
    
    search = arxiv.Search(
        query=search_query,
        max_results=5, # 너무 많으면 카톡 글자수 제한에 걸리므로 5개로 제한
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    paper_data = []
    for result in search.results():
        paper_info = {
            "title": result.title,
            "summary": result.summary[:400], # Gemini 분석용 초록 일부
            "url": result.pdf_url
        }
        paper_data.append(paper_info)
    
    return paper_data

def get_gemini_summary(paper_list):
    """
    수집된 실제 논문 정보를 Gemini에게 전달합니다.
    """
    # 논문 리스트를 텍스트로 변환
    papers_text = ""
    for i, p in enumerate(paper_list):
        papers_text += f"{i+1}. 제목: {p['title']}\n초록: {p['summary']}\n링크: {p['url']}\n\n"

    prompt = f"""
    # Role: 
    당신은 최고 권위 AI 학회의 Senior Reviewer이자, SCI급 저널 투고를 지도하는 까칠하지만 실력 있는 '박사급 수석 연구원'입니다. 
    단순 요약보다는 논문의 허점(Weakness)과 연구 기회를 찾는 데 집착합니다.
    
    # Context:
    사용자는 인공지능 분야 석사과정생으로, 의료데이터를 다룬 인공지능, 멀티모달(Multimodal), NLP, 시계열 데이터 융합 등에 관심이 많습니다. 
    단순한 기술 습득이 아니라, 기존 연구를 비판적으로 계승하여 '나만의 논문 발제'를 하는 것이 목표입니다.
    
    # Task:
    제공된 논문 리스트 중에서 가장 임팩트 있는 3개를 선정하여 아래 기준에 따라 분석하세요.
    (반드시 각 논문의 [PDF 링크]를 제목 옆에 포함시켜주세요.)
    
    ## 1. 🔍 비판적 시각 (Critical Review)
    - 이 논문이 제안한 방법론이 가진 잠재적 한계나 '가정의 오류'는 무엇인가?
    - (중요) 저자들이 교묘하게 언급하지 않고 넘어간 '약점'은 무엇인가?
    
    ## 2. 💡 SCI급 연구 기회 (Research Gap)
    - 위에서 찾은 약점을 보완하기 위해 사용자가 시도해 볼 수 있는 구체적인 연구 방향은?
    
    ## 3. 📈 석사생을 위한 브리핑
    - 세미나 발제 시 교수님에게 받을 수 있는 '압박 질문' 1가지와 모범 답안.
    
    논문 리스트:
    {papers_text}
    
    # Tone & Style:
    - 전문 용어는 정확하게 사용하고, 1줄의 간단한 인삿말과 함께 Task의 내용만 전달할 것.
    - 카카오톡 메시지 형식에 맞게 이모지를 적절히 섞어 가독성 있게 작성할 것.
    - 카카오톡 메시지 글자수 제한이 있으니, 전체 내용은 공백 포함 800자 이내로 핵심만 뾰족하게 작성할 것.
    """
    
    response = model.generate_content(prompt)
    return response.text

def get_access_token():
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": REFRESH_TOKEN
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

def send_kakao_msg(token, text):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 'text' 대신 'feed' 템플릿 사용 (더 많은 글자수 수용)
    payload = {
        "template_object": json.dumps({
            "object_type": "feed",
            "content": {
                "title": "🎓 오늘의 SCI급 논문 분석 리포트",
                "description": text, # 여기서 Gemini가 쓴 글이 들어갑니다.
                "image_url": "https://raw.githubusercontent.com/google/fonts/main/ofl/robotoserif/static/RobotoSerif-Regular.png", # 예시 아이콘
                "link": {
                    "web_url": "https://arxiv.org",
                    "mobile_web_url": "https://arxiv.org"
                }
            },
            "buttons": [
                {
                    "title": "논문 원문 보기",
                    "link": {
                        "web_url": "https://arxiv.org",
                        "mobile_web_url": "https://arxiv.org"
                    }
                }
            ]
        })
    }
    res = requests.post(url, headers=headers, data=payload)
    
    # 응답 확인 로그
    result = res.json()
    if result.get("result_code") == 0:
        print("✅ 카카오톡 전송 성공!")
    else:
        print(f"❌ 전송 실패: {result}")

def send_kakao_msg_org(token, text):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": text,
            "link": {"web_url": "https://arxiv.org"},
            "button_title": "arXiv에서 확인"
        })
    }
    res = requests.post(url, headers=headers, data=payload)
    print(f"카카오 응답 결과: {res.json()}") 

if __name__ == "__main__":
    print("🚀 최신 SCI급 후보 논문 수집 중...")
    real_papers = fetch_recent_papers()
    
    if not real_papers:
        print("수집된 논문이 없습니다.")
    else:
        print(f"✅ {len(real_papers)}개의 논문 분석 시작 (Gemini)...")
        ai_summary = get_gemini_summary(real_papers)
        
        print("📩 카카오톡 전송 중...")
        access_token = get_access_token()
        send_kakao_msg(access_token, ai_summary)
        print("✨ 모든 작업 완료!")
