import os
import requests
import json

# GitHub Secrets에서 환경변수 가져오기
REST_API_KEY = os.environ.get('KAKAO_REST_API_KEY')
REFRESH_TOKEN = os.environ.get('KAKAO_REFRESH_TOKEN')

# 1. 카카오 Access Token 갱신 함수
def get_access_token():
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": REFRESH_TOKEN
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

# 2. 카카오톡 나에게 보내기 함수
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
    requests.post(url, headers=headers, data=payload)

# 메인 실행 로직
if __name__ == "__main__":
    # 테스트용: 구글 스칼라 AI 분야 1위 논문 가정 (추후 크롤링 코드 삽입)
    paper_title = "Attention Is All You Need"
    paper_url = "https://arxiv.org/abs/1706.03762"
    
    message = f"📢 오늘의 인기 AI 논문\n제목: {paper_title}\n바로가기: {paper_url}"
    
    access_token = get_access_token()
    send_kakao_msg(access_token, message)
    print("알림 전송 완료!")
