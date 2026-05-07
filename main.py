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
    당신은 AI 연구 전문가입니다. 아래의 논문 리스트를 분석하여 
    연구원에게 도움이 될 만한 핵심 논문 3개를 선정하고 요약해 주세요.
    
    대상 논문 리스트:
    {paper_list}
    
    출력 형식:
    - 각 논문의 제목과 핵심 기여점(1문장)
    - 왜 이 논문을 추천하는지 이유
    - 모든 답변은 한국어로 친절하게 작성해줘.
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
