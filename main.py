import os
import requests
import json
import google.generativeai as genai

# GitHub Secrets에서 환경변수 가져오기
REST_API_KEY = os.environ.get('KAKAO_REST_API_KEY')
REFRESH_TOKEN = os.environ.get('KAKAO_REFRESH_TOKEN')

# Gemini 설정
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_gemini_summary(paper_list):
    """
    수집된 논문 리스트를 Gemini에게 전달하여 요약 및 추천을 받습니다.
    """
    prompt = f"""
    # Role: 
    당신은 최고 권위 AI 학회의 Senior Reviewer이자, SCI급 저널 투고를 지도하는 까칠하지만 실력 있는 '박사급 수석 연구원'입니다. 
    단순 요약보다는 논문의 허점(Weakness)과 연구 기회를 찾는 데 집착합니다.
    
    # Context:
    사용자는 인공지능 분야 석사과정생으로, 의료데이터를 다룬 인공지능, 멀티모달(Multimodal), NLP, 시계열 데이터 융합 등에 관심이 많습니다. 
    단순한 기술 습득이 아니라, 기존 연구를 비판적으로 계승하여 '나만의 논문 발제'를 하는 것이 목표입니다.
    
    # Task:
    제공된 논문 리스트 {paper_list} 중에서 가장 임팩트 있는 3개를 선정하여 아래 기준에 따라 분석하세요.
    
    ## 1. 🔍 비판적 시각 (Critical Review)
    - 이 논문이 제안한 방법론이 가진 잠재적 한계나 '가정의 오류'는 무엇인가?
    - 어떤 특정 데이터셋이나 환경에서는 이 알고리즘이 작동하지 않을 것 같은가?
    - (중요) 저자들이 교묘하게 언급하지 않고 넘어간 '약점'은 무엇인가?
    
    ## 2. 💡 SCI급 연구 기회 (Research Gap)
    - 위에서 찾은 약점을 보완하기 위해 사용자가 시도해 볼 수 있는 구체적인 연구 방향은?
    - "기존 모델 + [사용자의 아이디어]" 조합으로 성능을 개선하거나 비용을 낮출 수 있는 포인트 제언.
    
    ## 3. 📈 석사생을 위한 브리핑
    - 논문 제목 및 핵심 기여점 (1줄 요약)
    - 세미나 발제 시 교수님에게 받을 수 있는 '압박 질문' 1가지와 모범 답안.
    
    # Tone & Style:
    - 전문 용어는 정확하게 사용하되, 선배가 후배에게 조언하듯 직설적이고 명확하게 말할 것.
    - 카카오톡 메시지 형식에 맞게 이모지를 적절히 섞어 가독성 있게 작성할 것.
    """
    
    response = model.generate_content(prompt)
    return response.text

# 카카오 Access Token 갱신 함수
def get_access_token():
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": REFRESH_TOKEN
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

# 카카오톡 나에게 보내기 함수
def send_kakao_msg(token, text):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": text,
            "link": {"web_url": "https://scholar.google.com"},
            "button_title": "논문 확인"
        })
    }
    res = requests.post(url, headers=headers, data=payload)
    print(f"카카오 응답 결과: {res.json()}") 

# 메인 실행 로직
if __name__ == "__main__":
    # 테스트용: 구글 스칼라 AI 분야 1위 논문 가정 (추후 크롤링 코드 삽입)
    """
    paper_title = "Attention Is All You Need"
    paper_url = "https://arxiv.org/abs/1706.03762"
    message = f"📢 오늘의 인기 AI 논문\n제목: {paper_title}\n바로가기: {paper_url}"
    """
    # (예시) 구글 스칼라 크롤링 결과
    raw_papers = "1. Real-time De-identification in Video, 2. Privacy-preserving AI, 3. Survey of Deepfake Detection"
    
    # Gemini에게 요약 요청
    ai_summary = get_gemini_summary(raw_papers)
    
    access_token = get_access_token()
    send_kakao_msg(access_token, ai_summary)
    print("알림 전송 완료!")
